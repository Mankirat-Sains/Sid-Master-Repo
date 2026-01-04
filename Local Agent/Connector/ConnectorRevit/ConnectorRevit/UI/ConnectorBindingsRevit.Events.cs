using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;
using Avalonia.Controls;
using DesktopUI2.Models;
using DesktopUI2.ViewModels;
using DesktopUI2.Views.Windows.Dialogs;
using RevitSharedResources.Extensions.SpeckleExtensions;
using RevitSharedResources.Models;
using Speckle.ConnectorRevit.Entry;
using Speckle.ConnectorRevit.Storage;
using Speckle.Core.Kits;
using Speckle.Core.Logging;
using Speckle.Core.Models;

namespace Speckle.ConnectorRevit.UI;

public partial class ConnectorBindingsRevit
{
  private string _lastSyncComment { get; set; }

  public override async void WriteStreamsToFile(List<StreamState> streams)
  {
    try
    {
      await APIContext
        .Run(app =>
        {
          using (Transaction t = new(CurrentDoc.Document, "Speckle Write State"))
          {
            t.Start();
            StreamStateManager.WriteStreamStateList(CurrentDoc.Document, streams);
            t.Commit();
          }
        })
        .ConfigureAwait(false);
    }
    // note : I don't think this exception catch is necessary, but this is an async VOID instead
    // of an async Task. Revit WILL CRASH if this method tries to throw an error, so keeping this
    // catch out of an abundance of caution
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.Fatal(
        ex,
        "Swallowing exception in {methodName}: {exceptionMessage}",
        nameof(WriteStreamsToFile),
        ex.Message
      );
    }
  }

  /// <summary>
  /// Sets the revit external event handler and initialises the rocket engines.
  /// </summary>
  /// <param name="eventHandler"></param>
  public void RegisterAppEvents()
  {
    //// GLOBAL EVENT HANDLERS
    RevitApp.ViewActivated += RevitApp_ViewActivated;
    //RevitApp.Application.DocumentChanged += Application_DocumentChanged;
    RevitApp.Application.DocumentCreated += Application_DocumentCreated;
    RevitApp.Application.DocumentCreating += Application_DocumentCreating;
    RevitApp.Application.DocumentOpened += Application_DocumentOpened;
    // This code may fire during the DocumentOpening event, in which case an exception will be
    // thrown about being unable to subscribe to an event during that event
    //RevitApp.Application.DocumentOpening += Application_DocumentOpening;
    ;
    RevitApp.Application.DocumentClosed += Application_DocumentClosed;
    RevitApp.Application.DocumentSaved += Application_DocumentSaved;
    RevitApp.Application.DocumentSynchronizingWithCentral += Application_DocumentSynchronizingWithCentral;
    RevitApp.Application.DocumentSynchronizedWithCentral += Application_DocumentSynchronizedWithCentral;
    RevitApp.Application.FileExported += Application_FileExported;
    RevitApp.ApplicationClosing += RevitApp_ApplicationClosing;
    //RevitApp.Application.FileExporting += Application_FileExporting;
    //RevitApp.Application.FileImporting += Application_FileImporting;
    
    // Register dialog box showing event to auto-dismiss dialogs during automated processing
    RevitApp.DialogBoxShowing += Application_DialogBoxShowing;
    
    //SelectionTimer = new Timer(1400) { AutoReset = true, Enabled = true };
    //SelectionTimer.Elapsed += SelectionTimer_Elapsed;
    // TODO: Find a way to handle when document is closed via middle mouse click
    // thus triggering the focus on a new project
  }

  private void RevitApp_ApplicationClosing(object sender, Autodesk.Revit.UI.Events.ApplicationClosingEventArgs e)
  {
    if (HomeViewModel.Instance == null)
    {
      return;
    }

    ///ensure WS connections etc are disposed, otherwise it might throw
    HomeViewModel.Instance.SavedStreams.ForEach(s => s.Dispose());
  }

  //DISABLED
  private void Application_FileExporting(object sender, FileExportingEventArgs e)
  {
    ShowImportExportAlert();
  }

  //DISABLED
  private void Application_FileImporting(object sender, FileImportingEventArgs e)
  {
    ShowImportExportAlert();
  }

  private void ShowImportExportAlert()
  {
    var config = ConfigManager.Load();
    if (config.ShowImportExportAlert)
    {
      Analytics.TrackEvent(Analytics.Events.ImportExportAlert, new Dictionary<string, object>() { { "name", "Show" } });
      var dialog = new ImportExportAlert();
      dialog.LaunchAction = () =>
      {
        SpeckleRevitCommand.RegisterPane();
        var panel = App.AppInstance.GetDockablePane(SpeckleRevitCommand.PanelId);
        panel.Show();
      };
      dialog.WindowStartupLocation = WindowStartupLocation.CenterScreen;
      dialog.Show();
      dialog.Topmost = true;
    }
  }

  private void Application_DocumentOpening(object sender, Autodesk.Revit.DB.Events.DocumentOpeningEventArgs e) { }

  private void Application_DocumentCreating(object sender, Autodesk.Revit.DB.Events.DocumentCreatingEventArgs e) { }

  private void Application_FileExported(object sender, Autodesk.Revit.DB.Events.FileExportedEventArgs e)
  {
    SendScheduledStream("export");
  }

  private void Application_DocumentSynchronizingWithCentral(
    object sender,
    Autodesk.Revit.DB.Events.DocumentSynchronizingWithCentralEventArgs e
  )
  {
    _lastSyncComment = e.Comments;
  }

  private void Application_DocumentSynchronizedWithCentral(
    object sender,
    Autodesk.Revit.DB.Events.DocumentSynchronizedWithCentralEventArgs e
  )
  {
    SendScheduledStream("sync", _lastSyncComment);
  }

  private void Application_DocumentSaved(object sender, Autodesk.Revit.DB.Events.DocumentSavedEventArgs e)
  {
    SendScheduledStream("save");
  }

  private async void SendScheduledStream(string slug, string message = "")
  {
    try
    {
      var stream = GetStreamsInFile().FirstOrDefault(x => x.SchedulerEnabled && x.SchedulerTrigger == slug);
      if (stream == null)
      {
        return;
      }

      var progress = new ProgressViewModel();
      progress.ProgressTitle = "Sending to Speckle 🚀";
      progress.IsProgressing = true;

      var dialog = new QuickOpsDialog();
      dialog.DataContext = progress;
      dialog.WindowStartupLocation = WindowStartupLocation.CenterScreen;
      dialog.Topmost = true;
      dialog.Show();

      if (message != null)
      {
        stream.CommitMessage = message;
      }

      await Task.Run(() => SendStream(stream, progress));
      progress.IsProgressing = false;
      dialog.Close();
      if (!progress.CancellationToken.IsCancellationRequested)
      {
        Analytics.TrackEvent(
          stream.Client.Account,
          Analytics.Events.Send,
          new Dictionary<string, object>() { { "method", "Schedule" }, { "filter", stream.Filter.Name } }
        );
      }
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.LogDefaultError(ex);
    }
  }

  //checks whether to refresh the stream list in case the user changes active view and selects a different document
  private void RevitApp_ViewActivated(object sender, Autodesk.Revit.UI.Events.ViewActivatedEventArgs e)
  {
    try
    {
      if (
        e.Document == null
        || e.PreviousActiveView == null
        || e.Document.GetHashCode() == e.PreviousActiveView.Document.GetHashCode()
      )
      {
        return;
      }

      // if the dialog body is open, then avalonia will freak out and crash Revit when trying to re-initialize
      // so we need to close the dialog and cancel any ongoing send / receive operation. (Maybe we can somehow
      // save the operation state and let the user come back to it later)
      if (MainViewModel.Instance.DialogBody != null)
      {
        CurrentOperationCancellation?.Cancel();
        MainViewModel.CloseDialog();
      }

      // invalidate all revit elements in the cache
      revitDocumentAggregateCache.InvalidateAll();

      SpeckleRevitCommand.RegisterPane();

      var streams = GetStreamsInFile();
      UpdateSavedStreams(streams);

      MainViewModel.Instance.NavigateToDefaultScreen();
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.LogDefaultError(ex);
    }
  }

  private void Application_DocumentClosed(object sender, Autodesk.Revit.DB.Events.DocumentClosedEventArgs e)
  {
    try
    {
      // the DocumentClosed event is triggered AFTER ViewActivated
      // is both doc A and B are open and B is closed, this would result in wiping the list of streams retrieved for A
      // only proceed if it's the last document open (the current is null)
      if (CurrentDoc != null)
      {
        return;
      }

      //if (SpeckleRevitCommand2.MainWindow != null)
      //  SpeckleRevitCommand2.MainWindow.Hide();

      //clear saved streams if closig a doc
      if (UpdateSavedStreams != null)
      {
        UpdateSavedStreams(new List<StreamState>());
      }

      MainViewModel.Instance.NavigateToDefaultScreen();
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.LogDefaultError(ex);
    }
  }

  // this method is triggered when there are changes in the active document
  private void Application_DocumentChanged(object sender, Autodesk.Revit.DB.Events.DocumentChangedEventArgs e) { }

  private void Application_DocumentCreated(object sender, Autodesk.Revit.DB.Events.DocumentCreatedEventArgs e)
  {
    SpeckleRevitCommand.RegisterPane();

    //clear saved streams if opening a new doc
    if (UpdateSavedStreams != null)
    {
      UpdateSavedStreams(new List<StreamState>());
    }
  }

  private void Application_DocumentOpened(object sender, Autodesk.Revit.DB.Events.DocumentOpenedEventArgs e)
  {
    SpeckleLog.Logger.Information("=== DocumentOpened event fired ===");
    SpeckleLog.Logger.Information("Document: {documentName}, Path: {documentPath}", e.Document?.Title ?? "null", e.Document?.PathName ?? "null");
    
    var streams = GetStreamsInFile();
    if (streams != null && streams.Count != 0)
    {
      if (SpeckleRevitCommand.UseDockablePanel)
      {
        SpeckleRevitCommand.RegisterPane();
        var panel = App.AppInstance.GetDockablePane(SpeckleRevitCommand.PanelId);
        panel.Show();
      }
      else
      {
        SpeckleRevitCommand.CreateOrFocusSpeckle();
      }
    }
    if (UpdateSavedStreams != null)
    {
      UpdateSavedStreams(streams);
    }

    //exit "stream view" when changing documents
    MainViewModel.Instance.NavigateToDefaultScreen();

    // Check for auto-send configuration
    // Pass the document from event args to avoid timing issues when launched from command line
    SpeckleLog.Logger.Information("Calling TriggerAutoSendIfEnabled with document: {documentName}", e.Document?.Title ?? "null");
    TriggerAutoSendIfEnabled(e.Document);
  }

  /// <summary>
  /// Triggers auto-send if enabled in the configuration.
  /// </summary>
  private async void TriggerAutoSendIfEnabled(Document doc = null)
  {
    SpeckleLog.Logger.Information("=== TriggerAutoSendIfEnabled called ===");
    SpeckleLog.Logger.Information("Provided document: {documentName}", doc?.Title ?? "null");
    SpeckleLog.Logger.Information("CurrentDoc?.Document: {documentName}", CurrentDoc?.Document?.Title ?? "null");
    
    try
    {
      SpeckleLog.Logger.Information("Loading config file...");
      var config = AutomatedSendConfigManager.Load();
      SpeckleLog.Logger.Information("Config loaded. AutoSendOnDocumentOpen: {autoSend}, AutoSendEnabled: {enabled}", 
        config.AutoSendOnDocumentOpen, HeadlessSendCommand.AutoSendEnabled);
      
      if (!config.AutoSendOnDocumentOpen && !HeadlessSendCommand.AutoSendEnabled)
      {
        SpeckleLog.Logger.Warning("Auto-send is disabled. AutoSendOnDocumentOpen={autoSend}, AutoSendEnabled={enabled}",
          config.AutoSendOnDocumentOpen, HeadlessSendCommand.AutoSendEnabled);
        return;
      }

      // Use provided document or fall back to CurrentDoc
      // When launched from command line, ActiveUIDocument might not be set yet
      var document = doc ?? CurrentDoc?.Document;
      SpeckleLog.Logger.Information("Document after initial check: {documentName}", document?.Title ?? "null");
      
      if (document == null)
      {
        SpeckleLog.Logger.Warning("Document is null, waiting 2 seconds and retrying...");
        // Wait a bit and retry for timing issues
        await Task.Delay(2000);
        document = CurrentDoc?.Document;
        SpeckleLog.Logger.Information("Document after retry: {documentName}", document?.Title ?? "null");
        if (document == null)
        {
          SpeckleLog.Logger.Error("Could not get document for auto-send - ActiveUIDocument not available after retry");
          return;
        }
      }

      SpeckleLog.Logger.Information(
        "=== Starting auto-send for document: {documentName} ===",
        document.Title
      );

      // Run the send asynchronously to not block the UI
      // Pass the document explicitly to avoid timing issues with ActiveUIDocument
      SpeckleLog.Logger.Information("Calling HeadlessSendService.SendCurrentDocument...");
      var result = await HeadlessSendService.SendCurrentDocument(
        RevitApp,
        config,
        CancellationToken.None,
        document
      ).ConfigureAwait(false);
      
      SpeckleLog.Logger.Information("HeadlessSendService.SendCurrentDocument returned. Success: {success}", result.Success);

      if (result.Success)
      {
        SpeckleLog.Logger.Information(
          "Auto-send completed successfully. Commit: {commitId}",
          result.CommitId
        );
      }
      else
      {
        SpeckleLog.Logger.Warning(
          "Auto-send failed: {error}",
          result.ErrorMessage
        );
      }

      // Handle post-send actions
      // Note: Closing documents from event handlers is unreliable in Revit
      // The batch script should handle closing Revit after detecting the result file
      if (config.CloseDocumentAfterSend)
      {
        SpeckleLog.Logger.Information("CloseDocumentAfterSend is true, but document close from event handler is unreliable. Batch script should handle Revit closure.");
        // Don't attempt to close - let the batch script handle it
        // Attempting to close can cause "The active document may not be closed from the API" errors
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Error(ex, "Auto-send failed with exception");
    }
  }

  public override bool CanOpen3DView => true;

  public override async Task Open3DView(List<double> viewCoordinates, string viewName = "")
  {
    var views = new FilteredElementCollector(CurrentDoc.Document).OfClass(typeof(View3D)).ToElements().Cast<View3D>();
    var viewtypes = new FilteredElementCollector(CurrentDoc.Document)
      .OfClass(typeof(ViewFamilyType))
      .ToElements()
      .Cast<ViewFamilyType>()
      .Where(x => x.ViewFamily == ViewFamily.ThreeDimensional);

    //hacky but the current comments camera is not a Base object
    //so it cannot be passed automatically to the converter
    //making a dummy one here
    var speckleCamera = new Base();
    speckleCamera["isHackySpeckleCamera"] = true;
    speckleCamera["coordinates"] = viewCoordinates;

    //when in a perspective view, it's not possible to open any transaction (txs adsk)
    //so we're switching to any other non perspective view here
    if (CurrentDoc.ActiveView.ViewType == ViewType.ThreeD)
    {
      var activeView = CurrentDoc.ActiveView as View3D;
      if (activeView.IsPerspective)
      {
        var nonPerspectiveView = views.FirstOrDefault(x => !x.IsPerspective);
        if (nonPerspectiveView != null)
        {
          CurrentDoc.ActiveView = nonPerspectiveView;
        }
      }
    }

    var perspView = views.FirstOrDefault(o => o.Name == "SpeckleCommentView");

    await APIContext.Run(app =>
    {
      using (var t = new Transaction(CurrentDoc.Document, $"Open Comment View"))
      {
        t.Start();

        var converter = (ISpeckleConverter)Activator.CreateInstance(Converter.GetType());
        converter.SetContextDocument(CurrentDoc.Document);
        var viewOrientation3D = converter.ConvertToNative(speckleCamera) as ViewOrientation3D;

        //txs bcfier
        if (perspView == null)
        {
          perspView = View3D.CreatePerspective(CurrentDoc.Document, viewtypes.First().Id);
          perspView.Name = "SpeckleCommentView";
        }
        perspView.SetOrientation(viewOrientation3D);
        perspView.CropBoxActive = false;
        perspView.CropBoxVisible = false;
        perspView.DisplayStyle = DisplayStyle.Shading;

        // the default phase was not looking good, picking the one of the View3D
        if (views.Any())
        {
          var viewPhase = views.First().get_Parameter(BuiltInParameter.VIEW_PHASE);
          if (viewPhase != null)
          {
            perspView.get_Parameter(BuiltInParameter.VIEW_PHASE).Set(viewPhase.AsElementId());
          }
        }

        t.Commit();
      }
      // needs to be outside the transaction
      CurrentDoc.ActiveView = perspView;
      // "refresh" the active view, txs Connor
      var uiView = CurrentDoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId.Equals(perspView.Id));
      uiView.Zoom(1);
    });
  }

  /// <summary>
  /// Handles dialog boxes that appear during automated processing.
  /// Automatically dismisses common dialogs when auto-send is enabled.
  /// Uses a generic approach: tries known dialogs first, then falls back to safe defaults.
  /// </summary>
  private void Application_DialogBoxShowing(object sender, Autodesk.Revit.UI.Events.DialogBoxShowingEventArgs e)
  {
    try
    {
      // Only auto-dismiss dialogs if auto-send is enabled
      var config = AutomatedSendConfigManager.Load();
      if (!config.AutoSendOnDocumentOpen && !HeadlessSendCommand.AutoSendEnabled)
      {
        return; // Let dialogs show normally if auto-send is not enabled
      }

      var dialogId = e.DialogId;
      SpeckleLog.Logger.Information("Dialog showing during auto-send: DialogId='{dialogId}'", dialogId);

      // Check if this is a TaskDialog (most Revit dialogs are TaskDialogs)
      if (e is Autodesk.Revit.UI.Events.TaskDialogShowingEventArgs taskDialogArgs)
      {
        // Special handling for security dialogs - check for keywords in DialogId
        // Security dialogs often appear before the add-in fully loads, so we need to catch them early
        if (dialogId.Contains("Security", StringComparison.OrdinalIgnoreCase) ||
            dialogId.Contains("Unsigned", StringComparison.OrdinalIgnoreCase) ||
            dialogId.Contains("AddIn", StringComparison.OrdinalIgnoreCase) ||
            dialogId.Contains("Add-In", StringComparison.OrdinalIgnoreCase))
        {
          SpeckleLog.Logger.Information(
            "Detected security-related dialog '{dialogId}', auto-clicking 'Always Load' (CommandLink1)",
            dialogId
          );
          // "Always Load" is typically CommandLink1 in security dialogs
          taskDialogArgs.OverrideResult((int)Autodesk.Revit.UI.TaskDialogResult.CommandLink1);
          return;
        }

        // Try to handle known dialogs with specific actions
        if (TryHandleKnownDialog(taskDialogArgs, dialogId))
        {
          return; // Successfully handled
        }

        // For unknown dialogs, be conservative - only try generic defaults for dialogs
        // that are likely to appear during file opening (contain keywords like "Upgrade", "Central", etc.)
        // Don't auto-dismiss dialogs that might be opened intentionally by the connector
        var fileOpeningKeywords = new[]
        {
          "Upgrade", "Central", "Workset", "Worksharing", "Audit", "Reference", "Link"
        };
        
        bool isLikelyFileOpeningDialog = fileOpeningKeywords.Any(keyword => 
          dialogId.Contains(keyword, StringComparison.OrdinalIgnoreCase));
        
        if (isLikelyFileOpeningDialog)
        {
          SpeckleLog.Logger.Information(
            "Unknown dialog '{dialogId}' appears to be a file-opening dialog, attempting generic safe default",
            dialogId
          );
          if (TryGenericSafeDefault(taskDialogArgs, dialogId))
          {
            return; // Successfully handled with generic default
          }
        }

        // If we can't handle it, log and let it show (better safe than sorry)
        // This prevents accidentally dismissing dialogs that are opened intentionally
        SpeckleLog.Logger.Information(
          "Dialog '{dialogId}' will show normally (not auto-dismissed to avoid interfering with intentional dialogs). " +
          "If this dialog blocks automation, add it to knownDialogs or fileOpeningKeywords.",
          dialogId
        );
      }
      else
      {
        // Handle non-TaskDialog dialogs (like dockable panes, windows, etc.)
        SpeckleLog.Logger.Information("Non-TaskDialog showing: DialogId='{dialogId}'", dialogId);
        
        // Check if this is a dialog that should be closed during automated processing
        // "Manage Links" and similar dialogs can block automation
        var dialogsToClose = new[]
        {
          "Manage Links",
          "ManageLinks",
          "Links",
          "Link Manager",
          "External References"
        };
        
        foreach (var dialogName in dialogsToClose)
        {
          if (dialogId.Contains(dialogName, StringComparison.OrdinalIgnoreCase))
          {
            SpeckleLog.Logger.Information(
              "Detected '{dialogName}' dialog during auto-send. This dialog will need to be closed manually or via UI Automation.",
              dialogName
            );
            // Note: We can't directly close non-TaskDialog dialogs from this event handler
            // The PowerShell script's UI Automation should handle closing these
            // But we log it so it's visible in the logs
            break;
          }
        }
      }
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.Error(ex, "Error handling dialog box: {dialogId}", e.DialogId);
      // Don't override result on error - let the dialog show normally
    }
  }

  /// <summary>
  /// Tries to handle known dialogs with specific actions.
  /// Returns true if the dialog was handled, false otherwise.
  /// </summary>
  private bool TryHandleKnownDialog(
    Autodesk.Revit.UI.Events.TaskDialogShowingEventArgs taskDialogArgs,
    string dialogId
  )
  {
    // Known dialog IDs and their safe default actions
    // These are dialogs that commonly appear during file opening
    var knownDialogs = new Dictionary<string, Autodesk.Revit.UI.TaskDialogResult>
    {
      // Security - Unsigned Add-In: "Always Load" is typically CommandLink1
      // This dialog appears when loading unsigned add-ins
      { "TaskDialog_SecurityUnsignedAddIn", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      { "Dialog_Revit_SecurityUnsignedAddIn", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      { "SecurityUnsignedAddIn", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      { "TaskDialog_Security", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      
      // Unresolved References: "Ignore and continue" (CommandLink1)
      { "TaskDialog_UnresolvedReferences", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      
      // File Upgrade: Usually "Upgrade" is the first option (CommandLink1) or "Yes"
      // DialogId may vary by version, but common patterns include:
      { "TaskDialog_UpgradeFile", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      { "TaskDialog_Upgrade", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      
      // Central Model / Worksharing: "Detach from Central" is safer for automated processing
      // This prevents sync issues and allows read-only access
      { "TaskDialog_DetachFromCentral", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      { "TaskDialog_Worksharing", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      
      // Audit: "Audit" is typically CommandLink1
      { "TaskDialog_AuditFile", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      { "TaskDialog_Audit", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      
      // Workset: "Open all worksets" is typically CommandLink1
      { "TaskDialog_Worksets", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
      
      // Model Upgrade Warning: "Upgrade" is typically CommandLink1
      { "TaskDialog_ModelUpgrade", Autodesk.Revit.UI.TaskDialogResult.CommandLink1 },
    };

    // Check if this is a known dialog
    if (knownDialogs.TryGetValue(dialogId, out var result))
    {
      SpeckleLog.Logger.Information(
        "Auto-dismissing known dialog '{dialogId}' with action: {action}",
        dialogId,
        result
      );
      taskDialogArgs.OverrideResult((int)result);
      return true;
    }

    // Also check for partial matches (some dialogs have version-specific IDs)
    foreach (var kvp in knownDialogs)
    {
      if (dialogId.Contains(kvp.Key, StringComparison.OrdinalIgnoreCase) ||
          kvp.Key.Contains(dialogId, StringComparison.OrdinalIgnoreCase))
      {
        SpeckleLog.Logger.Information(
          "Auto-dismissing dialog '{dialogId}' (matched pattern '{pattern}') with action: {action}",
          dialogId,
          kvp.Key,
          kvp.Value
        );
        taskDialogArgs.OverrideResult((int)kvp.Value);
        return true;
      }
    }

    return false;
  }

  /// <summary>
  /// Tries to find a safe default action for unknown dialogs.
  /// Strategy: Try CommandLink1 (first command link, usually the "continue" option),
  /// then Yes, then OK.
  /// Returns true if a safe default was applied, false otherwise.
  /// </summary>
  private bool TryGenericSafeDefault(
    Autodesk.Revit.UI.Events.TaskDialogShowingEventArgs taskDialogArgs,
    string dialogId
  )
  {
    // Strategy: Try common "safe" defaults in order of preference
    // Most Revit dialogs during file opening have a "continue" option as CommandLink1
    var safeDefaults = new[]
    {
      Autodesk.Revit.UI.TaskDialogResult.CommandLink1, // First command link (usually "continue/yes")
      Autodesk.Revit.UI.TaskDialogResult.CommandLink2, // Second command link (fallback)
      Autodesk.Revit.UI.TaskDialogResult.Yes,          // Yes button
      Autodesk.Revit.UI.TaskDialogResult.Ok,           // OK button
    };

    // Try each safe default
    foreach (var result in safeDefaults)
    {
      try
      {
        SpeckleLog.Logger.Information(
          "Attempting generic safe default for '{dialogId}': {action}",
          dialogId,
          result
        );
        taskDialogArgs.OverrideResult((int)result);
        SpeckleLog.Logger.Information(
          "Successfully applied generic safe default for '{dialogId}': {action}",
          dialogId,
          result
        );
        return true;
      }
      catch (Exception ex)
      {
        // This result type might not be available for this dialog, try next
        SpeckleLog.Logger.Debug(
          ex,
          "Could not apply {action} to dialog '{dialogId}', trying next option",
          result
        );
        continue;
      }
    }

    return false;
  }
}
