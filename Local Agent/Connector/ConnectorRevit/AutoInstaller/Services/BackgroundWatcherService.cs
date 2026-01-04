using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Speckle.AutoInstaller.Helpers;
using Speckle.AutoInstaller.Storage;

namespace Speckle.AutoInstaller.Services
{
  public class BackgroundWatcherService
  {
    private FileSystemWatcher _watcher;
    private Queue<string> _fileQueue;
    private readonly object _queueLock = new object();
    private Task _processingTask;
    private CancellationTokenSource _cancellationTokenSource;
    private string _watchFolder;
    private AutomatedSendConfig _config;
    private bool _isRunning;

    public bool IsRunning => _isRunning;

    public void Start(string watchFolder, AutomatedSendConfig config)
    {
      if (_isRunning)
      {
        Log("Watcher is already running, ignoring Start() call");
        return;
      }

      Log($"Starting file watcher service...");
      Log($"  Watch folder: {watchFolder}");
      Log($"  Results directory: {config?.ResultsDirectory ?? "Not specified"}");

      _watchFolder = watchFolder;
      _config = config;
      _fileQueue = new Queue<string>();
      _cancellationTokenSource = new CancellationTokenSource();
      _isRunning = true;

      // Ensure no existing Revit instances are running, since automation expects
      // to control the Revit lifecycle for each processed file.
      TryCloseRunningRevitInstances();

      // Ensure folder exists
      if (!Directory.Exists(_watchFolder))
      {
        Log($"Watch folder does not exist, creating: {_watchFolder}");
        Directory.CreateDirectory(_watchFolder);
      }
      else
      {
        Log($"Watch folder exists: {_watchFolder}");
      }

      // Set up file watcher
      _watcher = new FileSystemWatcher(_watchFolder, "*.rvt")
      {
        IncludeSubdirectories = true,
        NotifyFilter = NotifyFilters.FileName | NotifyFilters.LastWrite
      };

      _watcher.Created += OnFileCreated;
      _watcher.Changed += OnFileChanged;
      _watcher.EnableRaisingEvents = true;

      Log("File system watcher configured and enabled");

      // Start processing queue
      _processingTask = Task.Run(() => ProcessQueue(_cancellationTokenSource.Token));
      Log("File processing queue started");

      // Process existing files in the watch folder when starting
      Task.Run(() => ProcessExistingFiles(_cancellationTokenSource.Token));
      Log("Existing files scanner started");

      Log("File watcher service started successfully");
    }

    public void Stop()
    {
      if (!_isRunning)
      {
        Log("Watcher is not running, ignoring Stop() call");
        return;
      }

      Log("Stopping file watcher service...");
      _isRunning = false;
      _watcher?.Dispose();
      _cancellationTokenSource?.Cancel();
      _processingTask?.Wait(5000);
      _cancellationTokenSource?.Dispose();
      Log("File watcher service stopped");
    }

    /// <summary>
    /// Attempts to close any running Revit instances before automation starts.
    /// This first tries to close gracefully via CloseMainWindow, then falls back
    /// to Kill() if Revit does not exit within a short timeout. Any unsaved work
    /// will be lost, which is expected for fully automated runs.
    /// </summary>
    private void TryCloseRunningRevitInstances()
    {
      try
      {
        var processes = Process
          .GetProcesses()
          .Where(p => p.ProcessName.IndexOf("Revit", StringComparison.OrdinalIgnoreCase) >= 0)
          .ToList();

        if (processes.Count == 0)
        {
          return;
        }

        Log($"Found {processes.Count} running Revit process(es). Closing before automation.");

        foreach (var proc in processes)
        {
          try
          {
            if (proc.HasExited)
              continue;

            // Force kill immediately - no graceful close to avoid dialogs
            proc.Kill();
            proc.WaitForExit(5000);
            Log($"Revit process (PID: {proc.Id}) was killed.");
          }
          catch (Exception ex)
          {
            Log($"Error while closing Revit process: {ex.Message}");
          }
        }
        
        // Wait longer to ensure all processes and windows are fully closed
        // This prevents file dialogs from appearing
        Thread.Sleep(3000);
        
        // Double-check no Revit processes remain
        var remaining = Process.GetProcesses().Where(p => p.ProcessName.IndexOf("Revit", StringComparison.OrdinalIgnoreCase) >= 0).ToList();
        if (remaining.Count > 0)
        {
          Log($"WARNING: {remaining.Count} Revit process(es) still running after kill attempt");
          foreach (var proc in remaining)
          {
            try
            {
              if (!proc.HasExited)
              {
                proc.Kill();
                proc.WaitForExit(3000);
              }
            }
            catch { }
          }
          Thread.Sleep(2000);
        }
      }
      catch (Exception ex)
      {
        Log($"Error while enumerating Revit processes: {ex.Message}");
      }
    }

    private async void OnFileCreated(object sender, FileSystemEventArgs e)
    {
      await HandleFileEvent(e.FullPath).ConfigureAwait(false);
    }

    private async void OnFileChanged(object sender, FileSystemEventArgs e)
    {
      // Only process .rvt files
      if (!e.FullPath.EndsWith(".rvt", StringComparison.OrdinalIgnoreCase))
        return;

      await HandleFileEvent(e.FullPath).ConfigureAwait(false);
    }

    /// <summary>
    /// Checks if a file is a Revit backup file (e.g., filename.0009.rvt, filename.0010.rvt)
    /// These should be skipped - only process the base file.
    /// </summary>
    private bool IsBackupFile(string filePath)
    {
      var fileName = Path.GetFileNameWithoutExtension(filePath);
      // Check for pattern: filename.XXXX where XXXX is 4 digits
      // Examples: "file.0009", "file.0010", "file.0011"
      var match = System.Text.RegularExpressions.Regex.Match(fileName, @"\.\d{4}$");
      return match.Success;
    }

    private async Task HandleFileEvent(string filePath)
    {
      try
      {
        // Skip backup files (e.g., filename.0009.rvt, filename.0010.rvt)
        if (IsBackupFile(filePath))
        {
          Log($"Skipping backup file: {Path.GetFileName(filePath)}");
          return;
        }

        // Wait for file to be fully written
        await WaitForFileReady(filePath).ConfigureAwait(false);

        // Add to queue
        lock (_queueLock)
        {
          if (!_fileQueue.Contains(filePath))
          {
            _fileQueue.Enqueue(filePath);
            Log($"File queued: {Path.GetFileName(filePath)}");
          }
        }
      }
      catch (Exception ex)
      {
        Log($"Error handling file event: {ex.Message}");
      }
    }

    private async Task WaitForFileReady(string filePath, int maxWaitSeconds = 30)
    {
      var startTime = DateTime.Now;
      while ((DateTime.Now - startTime).TotalSeconds < maxWaitSeconds)
      {
        try
        {
          using (var stream = File.Open(filePath, FileMode.Open, FileAccess.Read, FileShare.None))
          {
            // File is ready
            return;
          }
        }
        catch (IOException)
        {
          // File is still locked, wait a bit
          await Task.Delay(500).ConfigureAwait(false);
        }
      }

      throw new TimeoutException($"File {filePath} was not ready within {maxWaitSeconds} seconds");
    }

    private async Task ProcessExistingFiles(CancellationToken cancellationToken)
    {
      try
      {
        Log("Scanning for existing .rvt files in watch folder...");
        
        if (!Directory.Exists(_watchFolder))
        {
          Log("Watch folder does not exist, skipping existing files scan");
          return;
        }

        // Find all existing .rvt files
        var allFiles = Directory.GetFiles(_watchFolder, "*.rvt", SearchOption.AllDirectories);
        
        // Filter out backup files (e.g., filename.0009.rvt, filename.0010.rvt)
        var existingFiles = allFiles.Where(f => !IsBackupFile(f)).ToArray();
        
        var skippedCount = allFiles.Length - existingFiles.Length;
        if (skippedCount > 0)
        {
          Log($"Skipped {skippedCount} backup file(s) (files with .XXXX pattern)");
        }
        
        Log($"Found {existingFiles.Length} existing .rvt file(s) to process in watch folder");

        foreach (var filePath in existingFiles)
        {
          if (cancellationToken.IsCancellationRequested)
            break;

          try
          {
            // Wait for file to be ready (not locked)
            await WaitForFileReady(filePath).ConfigureAwait(false);

            // Add to queue
            lock (_queueLock)
            {
              if (!_fileQueue.Contains(filePath))
              {
                _fileQueue.Enqueue(filePath);
                Log($"Queued existing file: {Path.GetFileName(filePath)}");
              }
            }
          }
          catch (Exception ex)
          {
            Log($"Error processing existing file {Path.GetFileName(filePath)}: {ex.Message}");
          }
        }

        if (existingFiles.Length > 0)
        {
          Log($"Finished scanning. {existingFiles.Length} file(s) queued for processing");
        }
      }
      catch (Exception ex)
      {
        Log($"Error scanning for existing files: {ex.Message}");
      }
    }

    private async Task ProcessQueue(CancellationToken cancellationToken)
    {
      while (!cancellationToken.IsCancellationRequested)
      {
        string filePath = null;

        lock (_queueLock)
        {
          if (_fileQueue.Count > 0)
          {
            filePath = _fileQueue.Dequeue();
          }
        }

        if (filePath != null)
        {
          try
          {
            await ProcessRevitFile(filePath).ConfigureAwait(false);
          }
          catch (Exception ex)
          {
            Log($"Error processing file {filePath}: {ex.Message}");
          }
        }
        else
        {
          // No files to process, wait a bit
          await Task.Delay(1000, cancellationToken).ConfigureAwait(false);
        }
      }
    }

    private async Task ProcessRevitFile(string filePath)
    {
      var fileName = Path.GetFileName(filePath);
      Log($"=== Starting processing for file: {fileName} ===");
      Log($"  Full path: {filePath}");
      Log($"  File size: {new FileInfo(filePath).Length / 1024 / 1024} MB");

      // Ensure config is saved so Revit picks up the latest automation settings
      try
      {
        if (_config != null)
        {
          // CRITICAL: Ensure AutoSendOnDocumentOpen is TRUE so the model is sent automatically
          if (!_config.AutoSendOnDocumentOpen)
          {
            Log("  WARNING: AutoSendOnDocumentOpen was false, setting to true to ensure models are sent");
            _config.AutoSendOnDocumentOpen = true;
          }

          // Ensure a concrete results directory is configured
          if (string.IsNullOrWhiteSpace(_config.ResultsDirectory))
          {
            _config.ResultsDirectory = AutomatedSendConfigManager.GetResultsDirectory(_config);
            Log($"  Results directory was empty, set to: {_config.ResultsDirectory}");
          }

          // Ensure AutoCreateStream is true (critical for models to send)
          if (!_config.AutoCreateStream)
          {
            Log("  WARNING: AutoCreateStream was false, setting to true to ensure streams are created");
            _config.AutoCreateStream = true;
          }

          AutomatedSendConfigManager.Save(_config);
          Log($"  Configuration saved successfully");
          Log($"    AutoSendOnDocumentOpen: {_config.AutoSendOnDocumentOpen} (MUST be true for models to send)");
          Log($"    AutoCreateStream: {_config.AutoCreateStream} (MUST be true to create streams)");
          Log($"    CloseDocumentAfterSend: {_config.CloseDocumentAfterSend}");
          Log($"    CloseRevitAfterSend: {_config.CloseRevitAfterSend}");
          Log($"    ServerUrl: {_config.ServerUrl}");
          Log($"    AccountEmail: {_config.AccountEmail}");
          Log($"    ProjectVisibility: {_config.ProjectVisibility ?? "Private"}");
        }
        else
        {
          Log("  ERROR: Configuration is null! Cannot process file.");
          throw new Exception("Configuration is null - cannot send model to Speckle");
        }
      }
      catch (Exception ex)
      {
        Log($"  ERROR: Failed to save AutomatedSendConfig before processing file: {ex.Message}");
        Log($"  Stack trace: {ex.StackTrace}");
        throw; // Re-throw to prevent processing without valid config
      }

      // Resolve results directory and expected result-file pattern
      var resultsDir = AutomatedSendConfigManager.GetResultsDirectory(_config);
      var docBaseName = Path.GetFileNameWithoutExtension(filePath);
      var resultPattern = $"{docBaseName}_*.json";

      Log($"  Results directory: {resultsDir}");
      Log($"  Expected result pattern: {resultPattern}");

      // Find Revit executable
      Log("  Searching for Revit executable...");
      var revitPath = FindRevitExecutable();
      if (string.IsNullOrEmpty(revitPath))
      {
        var errorMsg = "Revit executable not found";
        Log($"  ERROR: {errorMsg}");
        throw new Exception(errorMsg);
      }
      Log($"  Found Revit executable: {revitPath}");

      // Launch Revit with the file - ensure no dialogs appear
      var absoluteFilePath = Path.GetFullPath(filePath);
      
      if (!File.Exists(absoluteFilePath))
      {
        throw new FileNotFoundException($"File does not exist: {absoluteFilePath}");
      }

      Log("  Launching Revit with file...");
      Log($"  File: {absoluteFilePath}");
      Log($"  File exists: {File.Exists(absoluteFilePath)}");
      Log($"  File size: {new FileInfo(absoluteFilePath).Length} bytes");
      
      // Revit command-line: just pass the file path
      // The file path must be absolute and properly quoted
      // Use UseShellExecute = false for better control and to prevent dialogs
      // Match the working PowerShell implementation exactly (BatchSendToSpeckle.ps1 line 295-298)
      var processInfo = new ProcessStartInfo
      {
        FileName = revitPath,
        Arguments = $"\"{absoluteFilePath}\"",
        UseShellExecute = true  // Match working PowerShell scripts
      };
      
      Log($"  Command: {processInfo.FileName} {processInfo.Arguments}");

      Process process = null;
      try
      {
        process = Process.Start(processInfo);
        if (process == null)
        {
          throw new Exception("Process.Start returned null");
        }
        
        // Wait for Revit to fully start before continuing
        // This ensures the file is being opened, not showing a dialog
        var waitTime = 0;
        while (waitTime < 5000 && !process.HasExited)
        {
          Thread.Sleep(500);
          waitTime += 500;
          try
          {
            process.Refresh();
          }
          catch { }
        }
      }
      catch (Exception ex)
      {
        var errorMsg = $"Failed to start Revit process: {ex.Message}";
        Log($"  ERROR: {errorMsg}");
        throw new Exception(errorMsg, ex);
      }

      if (process.HasExited)
      {
        throw new Exception("Revit process exited immediately after starting - file may not have opened correctly");
      }

      Log($"  Revit started (PID: {process.Id})");

      // Start background dialog handler (full UI Automation like Waddell script)
      RevitDialogHandler dialogHandler = null;
      try
      {
        dialogHandler = new RevitDialogHandler(process.Id);
        dialogHandler.Start();
        Log("  Dialog handler started (monitoring for security dialogs and 'Manage Links' dialogs)");
      }
      catch (Exception ex)
      {
        Log($"  WARNING: Failed to start dialog handler: {ex.Message}");
        // Continue anyway - dialog handling is best-effort
      }

      // Wait for Revit / connector to complete the automated send by
      // monitoring the results directory for a matching result file.
      var startTime = DateTime.Now;
      var timeout = TimeSpan.FromMinutes(5);
      var checkInterval = TimeSpan.FromSeconds(10);
      string resultFilePath = null;
      int checkCount = 0;

      Log($"  Waiting for result file in '{resultsDir}' with pattern '{resultPattern}'...");
      Log($"  Timeout: {timeout.TotalMinutes} minutes, Check interval: {checkInterval.TotalSeconds} seconds");

      while (DateTime.Now - startTime < timeout)
      {
        checkCount++;
        var elapsed = DateTime.Now - startTime;

        try
        {
          if (Directory.Exists(resultsDir))
          {
            var dirInfo = new DirectoryInfo(resultsDir);
            var candidates = dirInfo.GetFiles(resultPattern)
              .Where(f => f.LastWriteTime >= startTime)
              .OrderByDescending(f => f.LastWriteTime)
              .ToList();

            if (candidates.Count > 0)
            {
              resultFilePath = candidates[0].FullName;
              Log($"  ✓ Result file detected after {elapsed.TotalSeconds:F1} seconds: {candidates[0].Name}");
              Log($"    Result file path: {resultFilePath}");
              Log($"    Result file size: {candidates[0].Length} bytes");
              Log($"    Result file modified: {candidates[0].LastWriteTime:yyyy-MM-dd HH:mm:ss}");
              break;
            }
            else if (checkCount % 3 == 0) // Log every 30 seconds
            {
              Log($"  Still waiting for result file... (elapsed: {elapsed.TotalSeconds:F1}s, check #{checkCount})");
            }
          }
          else
          {
            if (checkCount % 6 == 0) // Log every 60 seconds
            {
              Log($"  Results directory does not exist yet: {resultsDir}");
            }
          }
        }
        catch (Exception ex)
        {
          Log($"  Warning while checking for result file (check #{checkCount}): {ex.Message}");
        }

        if (process.HasExited)
        {
          Log($"  Revit process exited after {elapsed.TotalSeconds:F1} seconds (before result file was detected)");
          Log($"  Exit code: {process.ExitCode}");
          break;
        }

        await Task.Delay(checkInterval).ConfigureAwait(false);
      }

      // Stop dialog handler
      try
      {
        dialogHandler?.Stop();
      }
      catch { }

      if (resultFilePath == null)
      {
        var elapsed = DateTime.Now - startTime;
        Log($"  ⚠ No result file detected within timeout window ({elapsed.TotalSeconds:F1}s elapsed)");
        Log($"  Possible reasons:");
        Log($"    - Send may have failed");
        Log($"    - Send completed but result file was not written");
        Log($"    - Result file pattern mismatch");
        Log($"  Check Speckle server for commits and check connector logs");
      }
      else
      {
        Log($"  ✓ Processing completed successfully");
      }

      // Ensure Revit is not left running indefinitely for this file
      try
      {
        if (!process.HasExited)
        {
          Log("  Closing Revit process after automated send...");
          process.Kill();
          if (!process.WaitForExit(10000))
          {
            Log("  ⚠ Revit did not exit within 10 seconds after Kill() was called");
          }
          else
          {
            Log($"  ✓ Revit process closed successfully (exit code: {process.ExitCode})");
          }
        }
        else
        {
          Log($"  Revit process already exited (exit code: {process.ExitCode})");
        }
      }
      catch (Exception ex)
      {
        Log($"  ERROR while closing Revit process: {ex.Message}");
        Log($"  Stack trace: {ex.StackTrace}");
      }

      var totalTime = DateTime.Now - startTime;
      Log($"=== Finished processing file: {fileName} (total time: {totalTime.TotalSeconds:F1}s) ===");
    }

    private string FindRevitExecutable()
    {
      // Try to detect automatically (search common paths)
      Log("  Searching common Revit installation paths...");
      for (int year = 2026; year >= 2020; year--)
      {
        var possiblePaths = new[]
        {
          $@"C:\Program Files\Autodesk\Revit {year}\Revit.exe",
          $@"C:\Program Files (x86)\Autodesk\Revit {year}\Revit.exe"
        };

        foreach (var path in possiblePaths)
        {
          if (File.Exists(path))
          {
            Log($"  Found Revit at auto-detected path: {path}");
            return path;
          }
        }
      }

      Log("  ERROR: Revit executable not found in any common location");
      return null;
    }


    private void Log(string message)
    {
      LogHelper.Log($"[WatcherService] {message}");
    }
  }
}

