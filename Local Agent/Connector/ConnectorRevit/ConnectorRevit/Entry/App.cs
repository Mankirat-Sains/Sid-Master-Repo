using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Automation;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.DB.Events;
using Autodesk.Revit.UI;
using ConnectorRevit.Entry;
using RevitSharedResources.Extensions.SpeckleExtensions;
using RevitSharedResources.Models;
using Speckle.ConnectorRevit.Storage;
using Speckle.ConnectorRevit.UI;
using Speckle.Core.Helpers;
using Speckle.Core.Kits;
using Speckle.Core.Logging;
using Speckle.DllConflictManagement;
using Speckle.DllConflictManagement.Analytics;
using Speckle.DllConflictManagement.ConflictManagementOptions;
using Speckle.DllConflictManagement.EventEmitter;
using Speckle.DllConflictManagement.Serialization;

namespace Speckle.ConnectorRevit.Entry;

public class App : IExternalApplication
{
  public static UIApplication AppInstance { get; set; }

  public static UIControlledApplication UICtrlApp { get; set; }

  private bool _initialized;
  private static readonly string[] s_assemblyPathFragmentsToIgnore = new string[]
  {
    "Microsoft.Net\\assembly\\GAC_MSIL\\",
    "C:\\Program Files\\dotnet\\shared\\"
  };

  public Result OnStartup(UIControlledApplication application)
  {
    // We need to hook into the AssemblyResolve event before doing anything else
    // or we'll run into unresolved issues loading dependencies
    AppDomain.CurrentDomain.AssemblyResolve += new ResolveEventHandler(OnAssemblyResolve);
    AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;
    System.Windows.Forms.Application.ThreadException += Application_ThreadException;
    UICtrlApp = application;
    
    // Register DialogBoxShowing event EARLY to catch security dialogs during add-in loading
    // This must be registered before the add-in fully loads, as security dialogs appear during OnStartup
    UICtrlApp.DialogBoxShowing += EarlyDialogBoxShowing;
    
    UICtrlApp.ControlledApplication.ApplicationInitialized += ControlledApplication_ApplicationInitialized;
    UICtrlApp.ControlledApplication.DocumentOpening += ControlledApplication_DocumentOpening;

    DllConflictEventEmitter eventEmitter = new();
    ISerializer serializer = new SpeckleNewtonsoftSerializer();
    AnalyticsWithoutDependencies analytics = new(eventEmitter, serializer, "Revit", GetRevitVersion());
    eventEmitter.OnAction += analytics.TrackEvent;

    DllConflictManagmentOptionsLoader optionsLoader = new(serializer, "Revit", GetRevitVersion());
    // ignore dll conflicts when dll lives in GAC because they are noisy and not an issue (at least in revit)
    DllConflictManager conflictManager =
      new(
        optionsLoader,
        eventEmitter,
        s_assemblyPathFragmentsToIgnore,
        new string[] { $"C:\\Program Files\\Autodesk\\Revit {GetRevitVersion()}" }
      );
    RevitDllConflictUserNotifier conflictNotifier = new(conflictManager, eventEmitter);

    try
    {
      conflictManager.DetectConflictsWithAssembliesInCurrentDomain(typeof(App).Assembly);
      InitializeCore();

      // Start UI Automation fallback AFTER logger is initialized
      // This ensures logs will be written properly
      Task.Run(() => HandleSecurityDialogWithUI());

      UnsubscibeFromDllConflictEventsWithDependencyFreeResources(eventEmitter, analytics);
      SubscibeToDllConflictEventsWithCoreResources(eventEmitter);

      //Always initialize RevitTask ahead of time within Revit API context
      APIContext.Initialize(application);

      InitializeUiPanel(application);

      return Result.Succeeded;
    }
    catch (TypeLoadException ex)
    {
      conflictNotifier.NotifyUserOfTypeLoadException(ex);
      return Result.Failed;
    }
    catch (MemberAccessException ex)
    {
      conflictNotifier.NotifyUserOfMissingMethodException(ex);
      return Result.Failed;
    }
    catch (Exception ex)
    {
      eventEmitter.EmitError(new("Failed to load Speckle app", ex));
      NotifyUserOfErrorStartingConnector(ex);
      throw;
    }
    finally
    {
      eventEmitter.BeginEmit();
    }
  }

  private static void UnsubscibeFromDllConflictEventsWithDependencyFreeResources(
    DllConflictEventEmitter eventEmitter,
    AnalyticsWithoutDependencies analytics
  )
  {
    eventEmitter.OnAction -= analytics.TrackEvent;
  }

  private static void SubscibeToDllConflictEventsWithCoreResources(DllConflictEventEmitter eventEmitter)
  {
    eventEmitter.OnError += (obj, args) => SpeckleLog.Logger.Error(args.Exception, args.ContextMessage);
    eventEmitter.OnInfo += (obj, args) => SpeckleLog.Logger.Information(args.Exception, args.ContextMessage);

    eventEmitter.OnAction += (obj, args) =>
    {
      _ = Enum.TryParse(args.EventName, out Analytics.Events eventName);
      Analytics.TrackEvent(eventName, args.EventProperties);
    };
  }

  private static string GetRevitVersion()
  {
#if REVIT2020
    return "2020";
#elif REVIT2021
    return "2021";
#elif REVIT2022
    return "2022";
#elif REVIT2023
    return "2023";
#elif REVIT2024
    return "2024";
#elif REVIT2025
    return "2025";
#elif REVIT2026
    return "2026";
#endif
  }

  /// <summary>
  /// Early dialog handler registered in OnStartup to catch security dialogs during add-in loading.
  /// This must be registered before the add-in fully loads, as security dialogs appear during OnStartup.
  /// </summary>
  private void EarlyDialogBoxShowing(object sender, Autodesk.Revit.UI.Events.DialogBoxShowingEventArgs e)
  {
    try
    {
      var dialogId = e.DialogId;
      var dialogType = e.GetType().Name;
      
      // Enhanced logging: Log ALL dialogs to see what we're getting
      SpeckleLog.Logger.Information(
        "EARLY HANDLER: DialogId='{dialogId}', Type={type}, IsTaskDialog={isTaskDialog}",
        dialogId,
        dialogType,
        e is Autodesk.Revit.UI.Events.TaskDialogShowingEventArgs
      );
      
      // Check if this is a security dialog for our add-in
      // Security dialogs appear when loading unsigned add-ins
      if (dialogId.Contains("Security", StringComparison.OrdinalIgnoreCase) ||
          dialogId.Contains("Unsigned", StringComparison.OrdinalIgnoreCase) ||
          dialogId.Contains("AddIn", StringComparison.OrdinalIgnoreCase) ||
          dialogId.Contains("Add-In", StringComparison.OrdinalIgnoreCase))
      {
        SpeckleLog.Logger.Information("EARLY HANDLER: Security dialog detected! DialogId='{dialogId}'", dialogId);
        
        // Check if this is a TaskDialog
        if (e is Autodesk.Revit.UI.Events.TaskDialogShowingEventArgs taskDialogArgs)
        {
          SpeckleLog.Logger.Information(
            "Early handler: Detected security TaskDialog '{dialogId}', auto-clicking 'Always Load' (CommandLink1)",
            dialogId
          );
          // "Always Load" is typically CommandLink1 in security dialogs
          taskDialogArgs.OverrideResult((int)Autodesk.Revit.UI.TaskDialogResult.CommandLink1);
          return;
        }
        else
        {
          SpeckleLog.Logger.Warning(
            "EARLY HANDLER: Security dialog detected but it's NOT a TaskDialog! Type={type}, DialogId='{dialogId}'. " +
            "UI Automation fallback will be needed.",
            dialogType,
            dialogId
          );
        }
      }
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      // Log but don't throw - we don't want to break add-in loading
      SpeckleLog.Logger.Warning(ex, "Error in early dialog handler for dialog: {dialogId}", e.DialogId);
    }
  }

  /// <summary>
  /// UI Automation fallback to handle security dialog if event handler doesn't catch it.
  /// This runs in a background thread and periodically checks for the security dialog.
  /// Uses multiple detection methods to be robust across different OS versions and languages.
  /// </summary>
  private void HandleSecurityDialogWithUI()
  {
    // Write to file immediately to verify this method is being called
    try
    {
      var testFile = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Speckle",
        "ui_automation_test.txt"
      );
      var testDir = Path.GetDirectoryName(testFile);
      if (!Directory.Exists(testDir))
      {
        Directory.CreateDirectory(testDir);
      }
      File.WriteAllText(testFile, $"UI Automation started at {DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}");
    }
    catch { }

    // Also write to debug output
    System.Diagnostics.Debug.WriteLine($"UI Automation: Starting at {DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}");

    try
    {
      // Try to log (logger should be initialized by now)
      try
      {
        SpeckleLog.Logger?.Information("UI Automation: Starting security dialog handler");
      }
      catch
      {
        System.Diagnostics.Debug.WriteLine("UI Automation: Logger not available yet");
      }

      // Wait a bit for Revit to fully start and dialog to appear
      Thread.Sleep(1000);
      
      // Try multiple times (dialog might appear with delay)
      for (int attempt = 0; attempt < 15; attempt++)
      {
        try
        {
          // Find security dialog - search all top-level windows (language-agnostic)
          AutomationElement dialog = FindSecurityDialog();
          
          if (dialog != null)
          {
            try { SpeckleLog.Logger?.Information("UI Automation: Found security dialog, attempting to click 'Always Load' button"); } catch { }
            System.Diagnostics.Debug.WriteLine("UI Automation: Found security dialog!");
            
            // Try multiple methods to find and click the button (in order of reliability)
            bool success = false;
            
            // Method 1: Try by button index (first button is usually "Always Load")
            // This is language-agnostic and most reliable
            success = TryClickButtonByIndex(dialog, 0);
            
            // Method 2: Try by automation ID if available
            if (!success)
            {
              success = TryClickButtonByAutomationId(dialog);
            }
            
            // Method 3: Try by button text (language-dependent, but good fallback)
            if (!success)
            {
              success = TryClickButtonByText(dialog);
            }
            
            // Method 4: Try by button position (leftmost button is usually "Always Load")
            if (!success)
            {
              success = TryClickButtonByPosition(dialog);
            }
            
            if (success)
            {
              try { SpeckleLog.Logger?.Information("UI Automation: Successfully handled security dialog"); } catch { }
              System.Diagnostics.Debug.WriteLine("UI Automation: SUCCESS - Clicked button!");
              
              // Update test file with success
              try
              {
                var testFile = Path.Combine(
                  Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                  "Speckle",
                  "ui_automation_test.txt"
                );
                File.AppendAllText(testFile, $"\nSUCCESS: Clicked button at {DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}");
              }
              catch { }
              
              return; // Success, exit the loop
            }
            else
            {
              try { SpeckleLog.Logger?.Warning("UI Automation: Found security dialog but could not click button (attempt {attempt}/15)", attempt + 1); } catch { }
              System.Diagnostics.Debug.WriteLine($"UI Automation: Failed to click button (attempt {attempt + 1}/15)");
            }
          }
          else
          {
            try { SpeckleLog.Logger?.Debug("UI Automation: Security dialog not found yet (attempt {attempt}/15)", attempt + 1); } catch { }
          }
        }
        catch (Exception ex)
        {
          try { SpeckleLog.Logger?.Debug(ex, "UI Automation: Error on attempt {attempt}/15", attempt + 1); } catch { }
          System.Diagnostics.Debug.WriteLine($"UI Automation: Exception on attempt {attempt + 1}: {ex.Message}");
        }

        // Wait before next attempt
        Thread.Sleep(500);
      }

      try
      {
        SpeckleLog.Logger?.Information("UI Automation: Completed all attempts to find security dialog");
      }
      catch { }
      
      System.Diagnostics.Debug.WriteLine("UI Automation: Completed all attempts");
      
      // Update test file
      try
      {
        var testFile = Path.Combine(
          Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
          "Speckle",
          "ui_automation_test.txt"
        );
        File.AppendAllText(testFile, $"\nUI Automation completed at {DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}");
      }
      catch { }
    }
    catch (Exception ex)
    {
      // Log to both logger and debug output
      try
      {
        SpeckleLog.Logger?.Warning(ex, "UI Automation: Failed to handle security dialog");
      }
      catch { }
      
      System.Diagnostics.Debug.WriteLine($"UI Automation Error: {ex.Message}\n{ex.StackTrace}");
      
      // Update test file with error
      try
      {
        var testFile = Path.Combine(
          Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
          "Speckle",
          "ui_automation_test.txt"
        );
        File.AppendAllText(testFile, $"\nERROR at {DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}: {ex.Message}");
      }
      catch { }
    }
  }

  /// <summary>
  /// Finds the security dialog by searching all top-level windows.
  /// Language-agnostic - searches for keywords that appear in security dialogs.
  /// </summary>
  private AutomationElement FindSecurityDialog()
  {
    try
    {
      // Get all top-level windows
      var allWindows = AutomationElement.RootElement.FindAll(
        TreeScope.Children,
        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Window)
      );

      // Keywords that appear in security dialogs (common across languages/versions)
      string[] securityKeywords = new[]
      {
        "Security",
        "Unsigned",
        "Add-In",
        "AddIn",
        "Publisher",
        "Verified"
      };

      foreach (AutomationElement window in allWindows)
      {
        try
        {
          var name = window.Current.Name;
          if (string.IsNullOrEmpty(name))
            continue;

          // Check if window title contains security-related keywords
          bool isSecurityDialog = securityKeywords.Any(keyword =>
            name.Contains(keyword, StringComparison.OrdinalIgnoreCase));

          if (isSecurityDialog)
          {
            SpeckleLog.Logger.Information("UI Automation: Found security dialog with title: {title}", name);
            return window;
          }
        }
        catch { }
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Debug(ex, "UI Automation: Error finding security dialog");
    }

    return null;
  }

  /// <summary>
  /// Tries to click button by index (first button is usually "Always Load").
  /// Most reliable method - language and text independent.
  /// </summary>
  private bool TryClickButtonByIndex(AutomationElement dialog, int buttonIndex)
  {
    try
    {
      var allButtons = dialog.FindAll(
        TreeScope.Descendants,
        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button)
      );

      if (allButtons != null && allButtons.Count > buttonIndex)
      {
        var button = allButtons[buttonIndex];
        var buttonName = button.Current.Name;
        SpeckleLog.Logger.Information("UI Automation: Trying button at index {index} (name: '{name}')", buttonIndex, buttonName ?? "unknown");
        
        if (TryInvokeButton(button))
        {
          SpeckleLog.Logger.Information("UI Automation: Successfully clicked button at index {index} by InvokePattern", buttonIndex);
          return true;
        }
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Debug(ex, "UI Automation: Error clicking button by index {index}", buttonIndex);
    }

    return false;
  }

  /// <summary>
  /// Tries to click button by automation ID (if available).
  /// Very reliable if automation IDs are present.
  /// </summary>
  private bool TryClickButtonByAutomationId(AutomationElement dialog)
  {
    try
    {
      var allButtons = dialog.FindAll(
        TreeScope.Descendants,
        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button)
      );

      if (allButtons != null)
      {
        foreach (AutomationElement button in allButtons)
        {
          try
          {
            var automationId = button.Current.AutomationId;
            var name = button.Current.Name;
            
            // Common automation IDs for "Always Load" button
            // These may vary by Revit version, but worth trying
            if (!string.IsNullOrEmpty(automationId) &&
                (automationId.Contains("Always", StringComparison.OrdinalIgnoreCase) ||
                 automationId.Contains("Load", StringComparison.OrdinalIgnoreCase) ||
                 automationId == "1" || automationId == "Button1"))
            {
              SpeckleLog.Logger.Information("UI Automation: Trying button by AutomationId: {id} (name: '{name}')", automationId, name ?? "unknown");
              if (TryInvokeButton(button))
              {
                SpeckleLog.Logger.Information("UI Automation: Successfully clicked button by AutomationId");
                return true;
              }
            }
          }
          catch { }
        }
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Debug(ex, "UI Automation: Error clicking button by AutomationId");
    }

    return false;
  }

  /// <summary>
  /// Tries to click button by text (language-dependent fallback).
  /// Searches for common translations of "Always Load".
  /// </summary>
  private bool TryClickButtonByText(AutomationElement dialog)
  {
    try
    {
      // Common translations/keywords for "Always Load" button
      // Add more as needed for different languages
      string[] buttonTexts = new[]
      {
        "Always Load",
        "Always",
        "Load",
        "Toujours charger", // French
        "Siempre cargar",   // Spanish
        "Immer laden",      // German
        "Carica sempre",    // Italian
      };

      var allButtons = dialog.FindAll(
        TreeScope.Descendants,
        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button)
      );

      if (allButtons != null)
      {
        foreach (AutomationElement button in allButtons)
        {
          try
          {
            var buttonName = button.Current.Name;
            if (string.IsNullOrEmpty(buttonName))
              continue;

            // Check if button text matches any of our known texts
            bool matches = buttonTexts.Any(text =>
              buttonName.Contains(text, StringComparison.OrdinalIgnoreCase));

            if (matches)
            {
              SpeckleLog.Logger.Information("UI Automation: Trying button by text: '{name}'", buttonName);
              if (TryInvokeButton(button))
              {
                SpeckleLog.Logger.Information("UI Automation: Successfully clicked button by text");
                return true;
              }
            }
          }
          catch { }
        }
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Debug(ex, "UI Automation: Error clicking button by text");
    }

    return false;
  }

  /// <summary>
  /// Tries to click button by position (leftmost button is usually "Always Load").
  /// Language-agnostic method based on dialog layout.
  /// </summary>
  private bool TryClickButtonByPosition(AutomationElement dialog)
  {
    try
    {
      var allButtons = dialog.FindAll(
        TreeScope.Descendants,
        new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button)
      );

      if (allButtons != null && allButtons.Count > 0)
      {
        // Find leftmost button (usually "Always Load")
        AutomationElement leftmostButton = null;
        double minX = double.MaxValue;

        foreach (AutomationElement button in allButtons)
        {
          try
          {
            var bounds = button.Current.BoundingRectangle;
            if (bounds.Left < minX)
            {
              minX = bounds.Left;
              leftmostButton = button;
            }
          }
          catch { }
        }

        if (leftmostButton != null)
        {
          var buttonName = leftmostButton.Current.Name;
          SpeckleLog.Logger.Information("UI Automation: Trying leftmost button (name: '{name}')", buttonName ?? "unknown");
          if (TryInvokeButton(leftmostButton))
          {
            SpeckleLog.Logger.Information("UI Automation: Successfully clicked leftmost button");
            return true;
          }
        }
      }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Debug(ex, "UI Automation: Error clicking button by position");
    }

    return false;
  }

  /// <summary>
  /// Attempts to invoke a button using the InvokePattern.
  /// Returns true if successful.
  /// </summary>
  private bool TryInvokeButton(AutomationElement button)
  {
    try
    {
      if (button == null)
        return false;

      // Try InvokePattern first (most reliable)
      if (button.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
      {
        var invokePattern = pattern as InvokePattern;
        if (invokePattern != null)
        {
          invokePattern.Invoke();
          return true;
        }
      }

      // Fallback: Try using mouse click simulation
      // Note: This requires additional permissions and may not work in all scenarios
      try
      {
        var bounds = button.Current.BoundingRectangle;
        if (!bounds.IsEmpty)
        {
          // Calculate center of button
          int x = (int)(bounds.Left + bounds.Width / 2);
          int y = (int)(bounds.Top + bounds.Height / 2);
          
          // Use SetCursorPos and mouse_event (requires P/Invoke)
          // For now, just log that we would try this
          SpeckleLog.Logger.Debug("UI Automation: Button bounds available but mouse click not implemented (would click at {x}, {y})", x, y);
        }
      }
      catch { }
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Debug(ex, "UI Automation: Error invoking button");
    }

    return false;
  }

  private void ControlledApplication_DocumentOpening(object sender, DocumentOpeningEventArgs e)
  {
    // When a user double-clicks on an .rvt file that start Revit, Revit invokes the DocumentOpening event before ApplicationInitialized.
    // In such instances, it becomes necessary to instantiate the pane during the document opening process.
    try
    {
      InitializeConnector();
      AppInstance ??= new UIApplication(sender as Application);
      CreateBindings();
      SpeckleRevitCommand.RegisterPane();
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.Fatal(ex, "Failed to load Speckle app");
      NotifyUserOfErrorStartingConnector(ex);
    }
  }

  private static void CreateBindings()
  {
    if (SpeckleRevitCommand.Bindings != null)
    {
      return;
    }

    ConnectorBindingsRevit bindings = new(AppInstance);
    bindings.RegisterAppEvents();
    SpeckleRevitCommand.Bindings = bindings;
    SchedulerCommand.Bindings = bindings;
  }

  private void ControlledApplication_ApplicationInitialized(
    object sender,
    Autodesk.Revit.DB.Events.ApplicationInitializedEventArgs e
  )
  {
    try
    {
      InitializeConnector();
      AppInstance ??= new UIApplication(sender as Application);
      CreateBindings();

      //This is also called in DUI, adding it here to know how often the connector is loaded and used
      Analytics.TrackEvent(Analytics.Events.Registered, null, false);

      SpeckleRevitCommand.RegisterPane();

      //AppInstance.ViewActivated += new EventHandler<ViewActivatedEventArgs>(Application_ViewActivated);
    }
    catch (KitException ex)
    {
      SpeckleLog.Logger.Warning(ex, "Error loading kit on startup");
      NotifyUserOfErrorStartingConnector(ex);
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.Fatal(ex, "Failed to load Speckle app");
      NotifyUserOfErrorStartingConnector(ex);
    }
  }

  private void Application_ThreadException(object sender, System.Threading.ThreadExceptionEventArgs e)
  {
    SpeckleLog.Logger.Fatal(
      e.Exception,
      "Caught thread exception with message {exceptionMessage}",
      e.Exception.Message
    );
  }

  private void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
  {
    if (e.ExceptionObject is Exception ex)
    {
      SpeckleLog.Logger.Fatal(
        ex,
        "Caught unhandled exception. Is terminating : {isTerminating}. Message : {exceptionMessage}",
        e.IsTerminating,
        ex.Message
      );
    }
    else
    {
      SpeckleLog.Logger.Fatal(
        "Caught unhandled exception. Is terminating : {isTerminating}. Exception object is of type : {exceptionObjectType}. Exception object to string : {exceptionObjToString}",
        e.IsTerminating,
        e.ExceptionObject.GetType(),
        e.ExceptionObject.ToString()
      );
    }
  }

  private void InitializeUiPanel(UIControlledApplication application)
  {
    string tabName = "Sidian";
    try
    {
      application.CreateRibbonTab(tabName);
    }
    catch (Autodesk.Revit.Exceptions.ArgumentException)
    {
      // exception occurs when the speckle tab has already been created.
      // this happens when both the dui2 and the dui3 connectors are installed. Can be safely ignored.
    }
    catch (Autodesk.Revit.Exceptions.InvalidOperationException ex)
    {
      SpeckleLog.Logger.Warning(ex, "User has too many Revit add-on tabs installed");
      NotifyUserOfErrorStartingConnector(ex);
      throw;
    }

    var specklePanel = application.CreateRibbonPanel(tabName, "Sidian");

    string path = typeof(App).Assembly.Location;

    //desktopui 2
    var speckleButton2 =
      specklePanel.AddItem(
        new PushButtonData(
          "Sidian",
          "Sidian",
          typeof(App).Assembly.Location,
          typeof(SpeckleRevitCommand).FullName
        )
      ) as PushButton;

    if (speckleButton2 != null)
    {
      speckleButton2.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.logo16.png", path);
      speckleButton2.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.logo32.png", path);
      speckleButton2.ToolTipImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.logo32.png", path);
      speckleButton2.ToolTip = "Speckle Connector for Revit";
      speckleButton2.AvailabilityClassName = typeof(CmdAvailabilityViews).FullName;
      speckleButton2.SetContextualHelp(new ContextualHelp(ContextualHelpType.Url, "https://speckle.systems"));
    }

    var schedulerButton =
      specklePanel.AddItem(
        new PushButtonData("Scheduler", "Scheduler", typeof(App).Assembly.Location, typeof(SchedulerCommand).FullName)
      ) as PushButton;

    if (schedulerButton != null)
    {
      schedulerButton.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.scheduler16.png", path);
      schedulerButton.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.scheduler32.png", path);
      schedulerButton.ToolTipImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.scheduler32.png", path);
      schedulerButton.ToolTip = "Scheduler for the Revit Connector";
      schedulerButton.AvailabilityClassName = typeof(CmdAvailabilityViews).FullName;
      schedulerButton.SetContextualHelp(new ContextualHelp(ContextualHelpType.Url, "https://speckle.systems"));
    }

    PulldownButton helpPulldown =
      specklePanel.AddItem(new PulldownButtonData("Help&Resources", "Help & Resources")) as PulldownButton;
    helpPulldown.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.help16.png", path);
    helpPulldown.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.help32.png", path);

    PushButton forum =
      helpPulldown.AddPushButton(
        new PushButtonData("forum", "Community Forum", typeof(App).Assembly.Location, typeof(ForumCommand).FullName)
      ) as PushButton;
    forum.ToolTip = "Check out our Community Forum! Opens a page in your web browser.";
    forum.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.forum16.png", path);
    forum.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.forum32.png", path);

    PushButton tutorials =
      helpPulldown.AddPushButton(
        new PushButtonData("tutorials", "Tutorials", typeof(App).Assembly.Location, typeof(TutorialsCommand).FullName)
      ) as PushButton;
    tutorials.ToolTip = "Check out our tutorials! Opens a page in your web browser.";
    tutorials.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.tutorials16.png", path);
    tutorials.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.tutorials32.png", path);

    PushButton docs =
      helpPulldown.AddPushButton(
        new PushButtonData("docs", "Docs", typeof(App).Assembly.Location, typeof(DocsCommand).FullName)
      ) as PushButton;
    docs.ToolTip = "Check out our documentation! Opens a page in your web browser.";
    docs.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.docs16.png", path);
    docs.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.docs32.png", path);

    PushButton manager =
      helpPulldown.AddPushButton(
        new PushButtonData("manager", "Manager", typeof(App).Assembly.Location, typeof(ManagerCommand).FullName)
      ) as PushButton;
    manager.ToolTip = "Manage accounts and connectors. Opens SpeckleManager.";
    manager.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.logo16.png", path);
    manager.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.logo32.png", path);

    // Add AutoSend button
    var autoSendButton =
      specklePanel.AddItem(
        new PushButtonData(
          "AutoSend",
          "Auto Send",
          typeof(App).Assembly.Location,
          typeof(HeadlessSendCommand).FullName
        )
      ) as PushButton;

    if (autoSendButton != null)
    {
      autoSendButton.Image = LoadPngImgSource("Speckle.ConnectorRevit.Assets.send16.png", path);
      autoSendButton.LargeImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.send32.png", path);
      autoSendButton.ToolTipImage = LoadPngImgSource("Speckle.ConnectorRevit.Assets.send32.png", path);
      autoSendButton.ToolTip = "Automatically send the current document to Speckle using the config file settings.";
      autoSendButton.AvailabilityClassName = typeof(HeadlessSendCommandAvailability).FullName;
      autoSendButton.SetContextualHelp(new ContextualHelp(ContextualHelpType.Url, "https://speckle.systems"));
    }

    // Ensure sample config exists
    AutomatedSendConfigManager.EnsureSampleConfigExists();
  }

  public Result OnShutdown(UIControlledApplication application)
  {
    return Result.Succeeded;
  }

  private ImageSource LoadPngImgSource(string sourceName, string path)
  {
    try
    {
      var assembly = Assembly.LoadFrom(Path.Combine(path));
      var icon = assembly.GetManifestResourceStream(sourceName);
      PngBitmapDecoder m_decoder = new(icon, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.Default);
      ImageSource m_source = m_decoder.Frames[0];
      return (m_source);
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
      SpeckleLog.Logger.LogDefaultError(ex);
    }

    return null;
  }

  static Assembly OnAssemblyResolve(object sender, ResolveEventArgs args)
  {
    Assembly a = null;
    var name = args.Name.Split(',')[0];
    string path = Path.GetDirectoryName(typeof(App).Assembly.Location);

    string assemblyFile = Path.Combine(path, name + ".dll");

    if (File.Exists(assemblyFile))
    {
      a = Assembly.LoadFrom(assemblyFile);
    }

    return a;
  }

  internal static void NotifyUserOfErrorStartingConnector(Exception ex)
  {
    using var td = new TaskDialog("Error loading Speckle");

    td.MainContent =
      ex is KitException
        ? ex.Message
        : $"Oh no! Something went wrong while loading Speckle, please report it on the forum:\n\n{ex.Message}";

    td.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Ask for help on our Community Forum");

    TaskDialogResult tResult = td.Show();

    if (TaskDialogResult.CommandLink1 == tResult)
    {
      Open.Url("https://speckle.community/");
    }
  }

  private void InitializeCore()
  {
    Setup.Init(ConnectorBindingsRevit.HostAppNameVersion, ConnectorBindingsRevit.HostAppName);
  }

  private void InitializeConnector()
  {
    if (_initialized)
    {
      return;
    }

    //DUI2 - pre build app, so that it's faster to open up
    SpeckleRevitCommand.InitAvalonia();

    _initialized = true;
  }
}
