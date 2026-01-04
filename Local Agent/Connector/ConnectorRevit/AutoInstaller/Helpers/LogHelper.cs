using System;
using System.IO;

namespace Speckle.AutoInstaller.Helpers
{
  /// <summary>
  /// Centralized logging helper for Speckle Auto-Installer.
  /// Logs are saved to AppData\Roaming\Speckle\AutoInstaller\Logs (works on any Windows machine).
  /// </summary>
  public static class LogHelper
  {
    /// <summary>
    /// Gets the log file path. Uses Environment.GetFolderPath to ensure it works on any Windows machine.
    /// Logs are saved to %APPDATA%\Speckle\AutoInstaller\Logs for easy access.
    /// </summary>
    public static string GetLogPath()
    {
      // Use AppData which is standard for application logs and works on any Windows machine
      var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
      var logFolder = Path.Combine(appDataPath, "Speckle", "AutoInstaller", "Logs");
      var logFileName = $"AutoInstaller_{DateTime.Now:yyyyMMdd}.log";
      return Path.Combine(logFolder, logFileName);
    }

    /// <summary>
    /// Logs a message to the log file with timestamp.
    /// </summary>
    public static void Log(string message)
    {
      try
      {
        var logPath = GetLogPath();
        var logDir = Path.GetDirectoryName(logPath);
        if (!Directory.Exists(logDir))
        {
          Directory.CreateDirectory(logDir);
        }

        var logMessage = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] {message}";
        File.AppendAllText(logPath, logMessage + Environment.NewLine);
      }
      catch
      {
        // Silently fail if logging fails - don't break the application
      }
    }
  }
}

