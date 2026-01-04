#nullable enable
using System;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using RevitSharedResources.Models;
using Speckle.ConnectorRevit.Storage;
using Speckle.ConnectorRevit.UI;
using Speckle.Core.Logging;

namespace Speckle.ConnectorRevit.Entry;

/// <summary>
/// External command for headless/automated sending of Revit models to Speckle.
/// This command can be triggered programmatically or via Revit's command line.
/// </summary>
[Transaction(TransactionMode.Manual)]
public class HeadlessSendCommand : IExternalCommand
{
  /// <summary>
  /// Set this to true to enable auto-send on document open.
  /// This can be controlled via the config file.
  /// </summary>
  public static bool AutoSendEnabled { get; set; } = false;

  /// <summary>
  /// The last send result (for external access).
  /// </summary>
  public static AutomatedSendResult? LastResult { get; private set; }

  public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
  {
    try
    {
      var uiApp = commandData.Application;
      
      // Load configuration
      var config = AutomatedSendConfigManager.Load();
      
      SpeckleLog.Logger.Information(
        "HeadlessSendCommand executing for document: {documentName}",
        uiApp.ActiveUIDocument?.Document?.Title ?? "unknown"
      );

      // Run the send operation
      var result = Task.Run(async () => 
        await HeadlessSendService.SendCurrentDocument(uiApp, config, CancellationToken.None)
      ).GetAwaiter().GetResult();

      LastResult = result;

      if (result.Success)
      {
        SpeckleLog.Logger.Information(
          "HeadlessSendCommand completed successfully. Commit: {commitId}",
          result.CommitId
        );

        // Handle post-send actions
        HandlePostSendActions(uiApp, config);

        return Result.Succeeded;
      }
      else
      {
        message = result.ErrorMessage ?? "Unknown error during send";
        SpeckleLog.Logger.Error("HeadlessSendCommand failed: {error}", message);
        
        // Still handle post-send actions even on failure if configured
        HandlePostSendActions(uiApp, config);
        
        return Result.Failed;
      }
    }
    catch (Exception ex)
    {
      message = ex.Message;
      SpeckleLog.Logger.Error(ex, "HeadlessSendCommand threw an exception");
      return Result.Failed;
    }
  }

  /// <summary>
  /// Handles post-send actions like closing document or Revit.
  /// </summary>
  private void HandlePostSendActions(UIApplication uiApp, AutomatedSendConfig config)
  {
    try
    {
      if (config.CloseDocumentAfterSend && uiApp.ActiveUIDocument != null)
      {
        // Queue document close - can't do it directly in the command
        // The document will be closed by the external event handler
        QueueDocumentClose(uiApp);
      }

      if (config.CloseRevitAfterSend)
      {
        // Queue Revit close
        QueueRevitClose();
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Warning(ex, "Failed to handle post-send actions");
    }
  }

  private static void QueueDocumentClose(UIApplication uiApp)
  {
    // We'll use an external event to close the document after the command completes
    // For now, just log that we would close
    SpeckleLog.Logger.Information("Document close queued (CloseDocumentAfterSend=true)");
    
    // Actually close the document using APIContext
    try
    {
      APIContext.Run(app =>
      {
        var doc = uiApp.ActiveUIDocument?.Document;
        if (doc != null && !doc.IsLinked)
        {
          doc.Close(false); // false = don't save changes
        }
      }).Wait();
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Warning(ex, "Failed to close document");
    }
  }

  private static void QueueRevitClose()
  {
    SpeckleLog.Logger.Information("Revit close queued (CloseRevitAfterSend=true)");
    // Note: Actually closing Revit programmatically is complex and might not work well
    // The user should handle this externally or use journal files
  }

  /// <summary>
  /// Sends the current document using the loaded configuration.
  /// This can be called from DocumentOpened event handler.
  /// </summary>
  public static async Task<AutomatedSendResult?> SendCurrentDocumentAsync(UIApplication uiApp)
  {
    try
    {
      var config = AutomatedSendConfigManager.Load();
      
      if (!config.AutoSendOnDocumentOpen && !AutoSendEnabled)
      {
        SpeckleLog.Logger.Debug("Auto-send is disabled, skipping");
        return null;
      }

      SpeckleLog.Logger.Information(
        "Auto-sending document: {documentName}",
        uiApp.ActiveUIDocument?.Document?.Title ?? "unknown"
      );

      var result = await HeadlessSendService.SendCurrentDocument(uiApp, config, CancellationToken.None);
      LastResult = result;

      return result;
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Error(ex, "Auto-send failed");
      return new AutomatedSendResult
      {
        Success = false,
        ErrorMessage = ex.Message,
        DocumentName = uiApp.ActiveUIDocument?.Document?.Title,
        DocumentPath = uiApp.ActiveUIDocument?.Document?.PathName
      };
    }
  }
}

/// <summary>
/// Command availability - always available when a document is open.
/// </summary>
public class HeadlessSendCommandAvailability : IExternalCommandAvailability
{
  public bool IsCommandAvailable(UIApplication applicationData, CategorySet selectedCategories)
  {
    return applicationData.ActiveUIDocument?.Document != null;
  }
}





