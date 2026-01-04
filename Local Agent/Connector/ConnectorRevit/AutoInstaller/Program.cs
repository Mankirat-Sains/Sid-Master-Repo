using System;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Speckle.AutoInstaller.Helpers;
using Speckle.AutoInstaller.Models;
using Speckle.AutoInstaller.Services;
using Speckle.AutoInstaller.Storage;
using Speckle.AutoInstaller.UI;
using Speckle.Core.Logging;
using Speckle.Core.Kits;

namespace Speckle.AutoInstaller
{
  internal static class Program
  {
    // Configuration flag file - if this exists, the app thinks it's configured
    // To reset and show setup wizard again, delete this file:
    // %APPDATA%\Speckle\SpeckleAutoInstaller.configured
    // Or run with: SpeckleAutoInstaller.exe /setup
    private const string ConfigFlagFile = "SpeckleAutoInstaller.configured";

    [STAThread]
    static void Main(string[] args)
    {
      // Set up global exception handlers to prevent crash dialogs
      // This ensures all exceptions are logged instead of showing error dialogs
      Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
      Application.ThreadException += Application_ThreadException;
      AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;

      Application.EnableVisualStyles();
      Application.SetCompatibleTextRenderingDefault(false);

      // Initialize Speckle Core - MUST be called before any AccountManager usage
      try
      {
        Setup.Init(
          HostApplications.Other.Slug,  // "other"
          HostApplications.Other.Name   // "Other"
        );
      }
      catch (Exception ex)
      {
        // Try to log even if Setup.Init failed
        try
        {
          LogHelper.Log($"CRITICAL ERROR: Failed to initialize Speckle Core: {ex.Message}");
          LogHelper.Log($"CRITICAL ERROR: Stack trace: {ex}");
        }
        catch { }
        
        MessageBox.Show(
          $"Failed to initialize Speckle Core: {ex.Message}\n\nDetails: {ex}\n\nCheck logs at: {LogHelper.GetLogPath()}",
          "Initialization Error",
          MessageBoxButtons.OK,
          MessageBoxIcon.Error
        );
        return;
      }

      // Ensure log directory exists and log startup
      try
      {
        var logPath = LogHelper.GetLogPath();
        LogHelper.Log($"=== Speckle Auto-Installer Started at {DateTime.Now:yyyy-MM-dd HH:mm:ss} ===");
        LogHelper.Log($"Log file location: {logPath}");
      }
      catch (Exception ex)
      {
        // If we can't create logs, continue anyway but show a warning
        MessageBox.Show(
          $"Warning: Could not initialize logging: {ex.Message}\n\nThe application will continue but logs may not be saved.",
          "Logging Warning",
          MessageBoxButtons.OK,
          MessageBoxIcon.Warning
        );
      }

      // Check for command-line argument to force setup wizard
      bool forceSetup = args != null && args.Length > 0 && 
                       (args[0].Equals("/setup", StringComparison.OrdinalIgnoreCase) ||
                        args[0].Equals("--setup", StringComparison.OrdinalIgnoreCase) ||
                        args[0].Equals("-setup", StringComparison.OrdinalIgnoreCase));

      // Check if already configured
      var flagPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Speckle",
        ConfigFlagFile
      );

      LogHelper.Log($"Checking for configuration flag file: {flagPath}");
      LogHelper.Log($"Flag file exists: {File.Exists(flagPath)}");

      // Check config file path too
      var configPath = AutomatedSendConfigManager.GetDefaultConfigPath();
      LogHelper.Log($"Checking for config file: {configPath}");
      LogHelper.Log($"Config file exists: {File.Exists(configPath)}");

      // Always show wizard if forced, or if flag file doesn't exist, or if config file doesn't exist
      if (forceSetup || !File.Exists(flagPath) || !File.Exists(configPath))
      {
        if (forceSetup)
        {
          LogHelper.Log("Setup wizard forced via command-line argument");
        }
        else if (!File.Exists(flagPath))
        {
          LogHelper.Log("First run - flag file doesn't exist, showing setup wizard");
        }
        else
        {
          LogHelper.Log("Config file missing, showing setup wizard");
        }
        RunSetupWizard();
        return; // Exit after wizard
      }

      // Both files exist - check if config is valid
      try
      {
        var config = AutomatedSendConfigManager.Load();
        if (config == null || string.IsNullOrWhiteSpace(config.ServerUrl) || string.IsNullOrWhiteSpace(config.AccountEmail))
        {
          // Config missing or invalid, show setup again
          LogHelper.Log("Configuration file missing or invalid, showing setup wizard");
          LogHelper.Log($"  ServerUrl: '{config?.ServerUrl ?? "null"}'");
          LogHelper.Log($"  AccountEmail: '{config?.AccountEmail ?? "null"}'");
          RunSetupWizard();
          return;
        }

        // Config is valid - start background service
        LogHelper.Log("Configuration valid, starting background service");
        StartBackgroundService(config);
        // Create and run a hidden form to keep the message loop alive
        using (var mainForm = new UI.BackgroundServiceForm())
        {
          Application.Run(mainForm);
        }
      }
      catch (Exception ex)
      {
        // If config loading fails, show setup wizard
        LogHelper.Log($"Error loading configuration: {ex.Message}, showing setup wizard");
        LogHelper.Log($"Stack trace: {ex}");
        RunSetupWizard();
      }
    }

    private static void RunSetupWizard()
    {
      using (var wizard = new SetupWizard())
      {
        if (wizard.ShowDialog() == DialogResult.OK)
        {
          var setupData = wizard.GetSetupData();

          // Run installation asynchronously
          var setupTask = Task.Run(async () =>
          {
            try
            {
              // 1. Install connector for selected versions
              var installer = new InstallerService();
              installer.InstallConnectorForVersions(setupData.SelectedRevitVersions);

              // 2. Create account
              var accountService = new AccountSetupService();
              var account = await accountService.CreateAccountAsync(
                setupData.ServerUrl,
                setupData.Email,
                setupData.Password
              ).ConfigureAwait(false);

              if (account == null)
              {
                MessageBox.Show(
                  "Failed to create account. Please check your credentials and try again.",
                  "Account Setup Failed",
                  MessageBoxButtons.OK,
                  MessageBoxIcon.Error
                );
                return;
              }

              // 3. Create config for automated sending
              // NOTE: This is aligned with the Waddell batch automation behavior:
              // - AutoSendOnDocumentOpen: true  -> send as soon as the document opens
              // - CloseDocumentAfterSend: true  -> close the RVT after sending
              // - CloseRevitAfterSend: true     -> Revit can be closed after each automated send
              var config = new AutomatedSendConfig
              {
                ServerUrl = setupData.ServerUrl,
                AccountEmail = setupData.Email,
                AutoCreateStream = true,
                // Let the connector auto-send when a document opens; our watcher is only
                // responsible for launching Revit with the right files at the right time.
                AutoSendOnDocumentOpen = true,
                DefaultFilter = "all",
                BranchName = "main",
                CommitMessageTemplate = "Automated send: {DocumentName} at {Timestamp}",
                CloseDocumentAfterSend = true,
                // Allow fully headless / batch-style behavior; Revit can close after send.
                CloseRevitAfterSend = true
              };

              // Ensure a concrete results directory is configured so automation
              // (and any monitoring tools) can detect completion of sends.
              if (string.IsNullOrWhiteSpace(config.ResultsDirectory))
              {
                config.ResultsDirectory = AutomatedSendConfigManager.GetResultsDirectory(config);
              }

              // Store schedule configuration separately
              SaveScheduleConfig(setupData.Schedule);

              AutomatedSendConfigManager.Save(config);

              // 4. Mark as configured
              var speckleFolder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "Speckle"
              );
              Directory.CreateDirectory(speckleFolder);
              var flagPath = Path.Combine(speckleFolder, ConfigFlagFile);
              File.WriteAllText(flagPath, DateTime.Now.ToString());

              // 5. Start background service
              StartBackgroundService(config, setupData.WatchFolder);
            }
            catch (Exception ex)
            {
              LogHelper.Log($"ERROR: Setup failed: {ex.Message}");
              LogHelper.Log($"ERROR: Stack trace: {ex}");
              
              MessageBox.Show(
                $"Setup failed: {ex.Message}",
                "Setup Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
              );
            }
          });

          // Show progress and wait
          var progressForm = new Form
          {
            Text = "Setting up Speckle...",
            Size = new System.Drawing.Size(300, 100),
            StartPosition = FormStartPosition.CenterParent,
            FormBorderStyle = FormBorderStyle.FixedDialog,
            MaximizeBox = false,
            MinimizeBox = false
          };

          var progressLabel = new Label
          {
            Text = "Please wait while we set up your Speckle connector...",
            Dock = DockStyle.Fill,
            TextAlign = System.Drawing.ContentAlignment.MiddleCenter
          };
          progressForm.Controls.Add(progressLabel);

          // Show form and process messages
          progressForm.Show();
          
          // Wait for task to complete, processing messages
          while (!setupTask.IsCompleted)
          {
            Application.DoEvents();
            System.Threading.Thread.Sleep(100);
          }

          progressForm.Close();

          // Check for exceptions
          if (setupTask.IsFaulted)
          {
            var ex = setupTask.Exception?.GetBaseException();
            if (ex != null)
            {
              LogHelper.Log($"ERROR: Setup task faulted: {ex.Message}");
              LogHelper.Log($"ERROR: Stack trace: {ex}");
              
              MessageBox.Show(
                $"Setup failed: {ex.Message}",
                "Setup Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
              );
            }
          }
          else if (!setupTask.IsCanceled)
          {
            // Setup completed successfully - show completion message
            MessageBox.Show(
              "Setup completed successfully! The background service is now running.",
              "Setup Complete",
              MessageBoxButtons.OK,
              MessageBoxIcon.Information
            );
            
            // Start the background service form to keep the application running
            // This is essential for timers, MessageBox calls, and background services to work
            using (var mainForm = new UI.BackgroundServiceForm())
            {
              Application.Run(mainForm);
            }
          }
        }
      }
    }

    private static void SaveScheduleConfig(ScheduleConfiguration schedule)
    {
      // Store schedule in a separate file or extend config
      var schedulePath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Speckle",
        "ScheduleConfig.json"
      );

      var scheduleJson = Newtonsoft.Json.JsonConvert.SerializeObject(schedule, Newtonsoft.Json.Formatting.Indented);
      File.WriteAllText(schedulePath, scheduleJson);
    }

    private static void StartBackgroundService(AutomatedSendConfig config, string watchFolder = null)
    {
      var schedulePath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Speckle",
        "ScheduleConfig.json"
      );

      ScheduleConfiguration schedule = null;
      if (File.Exists(schedulePath))
      {
        var scheduleJson = File.ReadAllText(schedulePath);
        schedule = Newtonsoft.Json.JsonConvert.DeserializeObject<ScheduleConfiguration>(scheduleJson);
      }

      if (schedule == null)
      {
        schedule = new ScheduleConfiguration
        {
          Type = ScheduleType.RunNow,
          StartImmediately = true
        };
      }

      var defaultFolder = watchFolder ?? Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
        "RevitProjects"
      );

      var service = new ScheduledBackgroundService();
      service.Start(schedule, defaultFolder, config);
    }

    /// <summary>
    /// Handles unhandled exceptions on the UI thread.
    /// </summary>
    private static void Application_ThreadException(object sender, ThreadExceptionEventArgs e)
    {
      try
      {
        LogHelper.Log($"UNHANDLED UI THREAD EXCEPTION: {e.Exception.Message}");
        LogHelper.Log($"UNHANDLED EXCEPTION STACK TRACE: {e.Exception}");
        if (e.Exception.InnerException != null)
        {
          LogHelper.Log($"INNER EXCEPTION: {e.Exception.InnerException.Message}");
          LogHelper.Log($"INNER EXCEPTION STACK TRACE: {e.Exception.InnerException}");
        }
      }
      catch
      {
        // If logging fails, at least try to write to a file
        try
        {
          var errorLogPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "Speckle",
            "AutoInstaller",
            "Errors",
            $"Error_{DateTime.Now:yyyyMMdd_HHmmss}.txt"
          );
          Directory.CreateDirectory(Path.GetDirectoryName(errorLogPath));
          File.WriteAllText(errorLogPath, $"UNHANDLED EXCEPTION: {e.Exception}\n\nStack Trace:\n{e.Exception}");
        }
        catch { }
      }
      
      // Don't show the error dialog - just log it and continue if possible
      // The application will try to continue running
    }

    /// <summary>
    /// Handles unhandled exceptions on non-UI threads.
    /// </summary>
    private static void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
      try
      {
        var exception = e.ExceptionObject as Exception;
        if (exception != null)
        {
          LogHelper.Log($"UNHANDLED EXCEPTION (Non-UI Thread): {exception.Message}");
          LogHelper.Log($"UNHANDLED EXCEPTION STACK TRACE: {exception}");
          if (exception.InnerException != null)
          {
            LogHelper.Log($"INNER EXCEPTION: {exception.InnerException.Message}");
            LogHelper.Log($"INNER EXCEPTION STACK TRACE: {exception.InnerException}");
          }
        }
        else
        {
          LogHelper.Log($"UNHANDLED EXCEPTION (Non-UI Thread): {e.ExceptionObject}");
        }
      }
      catch
      {
        // If logging fails, at least try to write to a file
        try
        {
          var errorLogPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "Speckle",
            "AutoInstaller",
            "Errors",
            $"Error_{DateTime.Now:yyyyMMdd_HHmmss}.txt"
          );
          Directory.CreateDirectory(Path.GetDirectoryName(errorLogPath));
          var exception = e.ExceptionObject as Exception;
          File.WriteAllText(errorLogPath, $"UNHANDLED EXCEPTION: {exception ?? e.ExceptionObject}\n\nStack Trace:\n{exception}");
        }
        catch { }
      }
      
      // If it's a terminating exception, we can't prevent the crash, but we've logged it
      if (e.IsTerminating)
      {
        LogHelper.Log("CRITICAL: Application is terminating due to unhandled exception");
      }
    }
  }
}

