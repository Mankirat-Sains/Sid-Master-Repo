#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using Speckle.Core.Logging;
using Speckle.Newtonsoft.Json;

namespace Speckle.ConnectorRevit.Storage;

/// <summary>
/// Configuration for automated/headless sending of Revit models to Speckle.
/// </summary>
public class AutomatedSendConfig
{
  /// <summary>
  /// The Speckle server URL (e.g., "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com" or "https://app.speckle.systems")
  /// </summary>
  public string ServerUrl { get; set; } = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com";

  /// <summary>
  /// The email of the account to use for sending. If empty, uses the default account.
  /// </summary>
  public string? AccountEmail { get; set; }

  /// <summary>
  /// The default stream ID to send to if no mapping is found for the document.
  /// </summary>
  public string? DefaultStreamId { get; set; }

  /// <summary>
  /// Optional mapping from document/project name to stream ID.
  /// Key: Revit document title (without .rvt extension)
  /// Value: Speckle stream ID
  /// </summary>
  public Dictionary<string, string> StreamIdMapping { get; set; } = new();

  /// <summary>
  /// The default filter to use when sending. Options: "all", "category", "view", etc.
  /// Default is "all" which sends everything.
  /// </summary>
  public string DefaultFilter { get; set; } = "all";

  /// <summary>
  /// Default converter settings (key-value pairs).
  /// </summary>
  public Dictionary<string, string> DefaultSettings { get; set; } = new();

  /// <summary>
  /// If true, automatically send the document when it's opened.
  /// </summary>
  public bool AutoSendOnDocumentOpen { get; set; } = false;

  /// <summary>
  /// The branch name to send to. Default is "main".
  /// </summary>
  public string BranchName { get; set; } = "main";

  /// <summary>
  /// Template for commit messages. Supports {DocumentName} and {Timestamp} placeholders.
  /// </summary>
  public string CommitMessageTemplate { get; set; } = "Automated send: {DocumentName} at {Timestamp}";

  /// <summary>
  /// If true, close the document after sending (useful for batch processing).
  /// </summary>
  public bool CloseDocumentAfterSend { get; set; } = true;

  /// <summary>
  /// If true, close Revit after sending (useful for batch processing single files).
  /// </summary>
  public bool CloseRevitAfterSend { get; set; } = false;

  /// <summary>
  /// If true, automatically create a new project/stream for each model.
  /// The project name will be based on the document name.
  /// </summary>
  public bool AutoCreateStream { get; set; } = true;

  /// <summary>
  /// If AutoCreateStream is true, this is the visibility of the created project.
  /// Options: "Private", "Public", "Unlisted"
  /// </summary>
  public string ProjectVisibility { get; set; } = "Private";

  /// <summary>
  /// Template for project name when auto-creating. Supports {DocumentName} placeholder.
  /// </summary>
  public string ProjectNameTemplate { get; set; } = "{DocumentName}";

  /// <summary>
  /// Template for project description when auto-creating. Supports {DocumentName} and {Timestamp} placeholders.
  /// </summary>
  public string ProjectDescriptionTemplate { get; set; } = "Automated project for {DocumentName} - Created at {Timestamp}";

  /// <summary>
  /// Directory to write result files to. If empty, uses %TEMP%\SpeckleAutoSend
  /// </summary>
  public string? ResultsDirectory { get; set; }

  /// <summary>
  /// Gets the stream ID for a given document name.
  /// </summary>
  public string? GetStreamIdForDocument(string documentName)
  {
    // Remove .rvt extension if present
    var name = documentName.EndsWith(".rvt", StringComparison.OrdinalIgnoreCase)
      ? documentName.Substring(0, documentName.Length - 4)
      : documentName;

    // Try to find in mapping first
    if (StreamIdMapping.TryGetValue(name, out var streamId))
    {
      return streamId;
    }

    // Fall back to default
    return DefaultStreamId;
  }

  /// <summary>
  /// Generates a commit message using the template.
  /// </summary>
  public string GenerateCommitMessage(string documentName)
  {
    return CommitMessageTemplate
      .Replace("{DocumentName}", documentName)
      .Replace("{Timestamp}", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
  }

  /// <summary>
  /// Generates a project name using the template.
  /// </summary>
  public string GenerateProjectName(string documentName)
  {
    // Remove .rvt extension if present
    var name = documentName.EndsWith(".rvt", StringComparison.OrdinalIgnoreCase)
      ? documentName.Substring(0, documentName.Length - 4)
      : documentName;

    return ProjectNameTemplate
      .Replace("{DocumentName}", name)
      .Replace("{Timestamp}", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
  }

  /// <summary>
  /// Generates a project description using the template.
  /// </summary>
  public string GenerateProjectDescription(string documentName)
  {
    // Remove .rvt extension if present
    var name = documentName.EndsWith(".rvt", StringComparison.OrdinalIgnoreCase)
      ? documentName.Substring(0, documentName.Length - 4)
      : documentName;

    return ProjectDescriptionTemplate
      .Replace("{DocumentName}", name)
      .Replace("{Timestamp}", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
  }
}

/// <summary>
/// Manages loading and saving of AutomatedSendConfig.
/// </summary>
public static class AutomatedSendConfigManager
{
  private static readonly string s_configFileName = "RevitAutomatedSend.json";

  /// <summary>
  /// Gets the default config file path in AppData.
  /// </summary>
  public static string GetDefaultConfigPath()
  {
    var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
    var speckleFolder = Path.Combine(appData, "Speckle");
    
    // Ensure directory exists
    if (!Directory.Exists(speckleFolder))
    {
      Directory.CreateDirectory(speckleFolder);
    }

    return Path.Combine(speckleFolder, s_configFileName);
  }

  /// <summary>
  /// Gets the results directory path.
  /// </summary>
  public static string GetResultsDirectory(AutomatedSendConfig? config = null)
  {
    if (!string.IsNullOrEmpty(config?.ResultsDirectory))
    {
      if (!Directory.Exists(config.ResultsDirectory))
      {
        Directory.CreateDirectory(config.ResultsDirectory);
      }
      return config.ResultsDirectory;
    }

    var tempPath = Path.Combine(Path.GetTempPath(), "SpeckleAutoSend");
    if (!Directory.Exists(tempPath))
    {
      Directory.CreateDirectory(tempPath);
    }
    return tempPath;
  }

  /// <summary>
  /// Loads the configuration from the default path, or creates a default config if none exists.
  /// </summary>
  public static AutomatedSendConfig Load()
  {
    return Load(GetDefaultConfigPath());
  }

  /// <summary>
  /// Loads the configuration from the specified path.
  /// </summary>
  public static AutomatedSendConfig Load(string path)
  {
    try
    {
      if (File.Exists(path))
      {
        var json = File.ReadAllText(path);
        var config = JsonConvert.DeserializeObject<AutomatedSendConfig>(json);
        return config ?? new AutomatedSendConfig();
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Warning(ex, "Failed to load AutomatedSendConfig from {path}", path);
    }

    return new AutomatedSendConfig();
  }

  /// <summary>
  /// Saves the configuration to the default path.
  /// </summary>
  public static void Save(AutomatedSendConfig config)
  {
    Save(config, GetDefaultConfigPath());
  }

  /// <summary>
  /// Saves the configuration to the specified path.
  /// </summary>
  public static void Save(AutomatedSendConfig config, string path)
  {
    try
    {
      var json = JsonConvert.SerializeObject(config, Formatting.Indented);
      File.WriteAllText(path, json);
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Error(ex, "Failed to save AutomatedSendConfig to {path}", path);
      throw;
    }
  }

  /// <summary>
  /// Creates a sample config file if one doesn't exist.
  /// </summary>
  public static void EnsureSampleConfigExists()
  {
    var path = GetDefaultConfigPath();
    if (!File.Exists(path))
    {
      var sampleConfig = new AutomatedSendConfig
      {
        ServerUrl = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com",
        AccountEmail = "shinesains@gmail.com",
        AutoCreateStream = true,
        ProjectVisibility = "Private",
        ProjectNameTemplate = "{DocumentName}",
        ProjectDescriptionTemplate = "Automated project for {DocumentName} - Created at {Timestamp}",
        AutoSendOnDocumentOpen = false,
        CloseDocumentAfterSend = true,
        BranchName = "main",
        CommitMessageTemplate = "Automated send: {DocumentName} at {Timestamp}"
      };
      Save(sampleConfig, path);
    }
  }
}

/// <summary>
/// Result of an automated send operation.
/// </summary>
public class AutomatedSendResult
{
  public bool Success { get; set; }
  public string? CommitId { get; set; }
  public string? StreamId { get; set; }
  public string? DocumentName { get; set; }
  public string? DocumentPath { get; set; }
  public string? ErrorMessage { get; set; }
  public DateTime Timestamp { get; set; } = DateTime.Now;
  public int ObjectCount { get; set; }
  public double DurationSeconds { get; set; }

  /// <summary>
  /// Writes the result to a JSON file.
  /// </summary>
  public void WriteToFile(string directory)
  {
    var fileName = $"{Path.GetFileNameWithoutExtension(DocumentPath ?? "unknown")}_{Timestamp:yyyyMMdd_HHmmss}.json";
    var path = Path.Combine(directory, fileName);
    var json = JsonConvert.SerializeObject(this, Formatting.Indented);
    File.WriteAllText(path, json);
  }
}

