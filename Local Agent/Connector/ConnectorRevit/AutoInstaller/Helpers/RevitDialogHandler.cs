using System;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Automation;
using System.Windows.Forms;
using Speckle.AutoInstaller.Helpers;

namespace Speckle.AutoInstaller.Helpers
{
  /// <summary>
  /// Handles Revit dialogs using UI Automation, similar to the Waddell PowerShell script.
  /// Monitors for security dialogs (to click "Always Load") and "Manage Links" dialogs (to close them).
  /// </summary>
  public class RevitDialogHandler
  {
    private readonly int _revitProcessId;
    private readonly CancellationTokenSource _cancellationTokenSource;
    private Thread _staThread;
    private bool _isRunning;

    public RevitDialogHandler(int revitProcessId)
    {
      _revitProcessId = revitProcessId;
      _cancellationTokenSource = new CancellationTokenSource();
    }

    /// <summary>
    /// Starts the dialog handler in a background task. Runs for up to 5 minutes or until Revit exits.
    /// UI Automation requires STA threading, so we create a dedicated STA thread with a message loop.
    /// </summary>
    public void Start()
    {
      if (_isRunning)
        return;

      _isRunning = true;
      
      // UI Automation requires STA (Single Threaded Apartment) threading
      // Task.Run creates MTA threads, so we need to create a dedicated STA thread
      // We also need a message loop for UI Automation to work properly
      var threadReady = new AutoResetEvent(false);
      
      _staThread = new Thread(() =>
      {
        try
        {
          // Create a hidden form to provide a message loop for UI Automation
          using (var hiddenForm = new Form())
          {
            hiddenForm.WindowState = FormWindowState.Minimized;
            hiddenForm.ShowInTaskbar = false;
            hiddenForm.FormBorderStyle = FormBorderStyle.None;
            hiddenForm.Size = new System.Drawing.Size(0, 0);
            hiddenForm.Visible = false;
            hiddenForm.Opacity = 0;
            
            // Use a timer to periodically check for dialogs on the STA thread
            var checkTimer = new System.Windows.Forms.Timer();
            checkTimer.Interval = 1000; // Check every 1 second for faster response
            int attempt = 0;
            const int maxAttempts = 300; // 5 minutes (300 * 1 second)
            bool securityDialogHandled = false;
            
            checkTimer.Tick += (s, e) =>
            {
              try
              {
                if (attempt >= maxAttempts || _cancellationTokenSource.Token.IsCancellationRequested)
                {
                  checkTimer.Stop();
                  try
                  {
                    hiddenForm.Invoke(new Action(() => hiddenForm.Close()));
                  }
                  catch { }
                  return;
                }
                
                attempt++;
                
                try
                {
                  // Check if Revit process still exists
                  var revitProcess = Process.GetProcesses().FirstOrDefault(p => p.Id == _revitProcessId);
                  if (revitProcess == null || revitProcess.HasExited)
                  {
                    LogHelper.Log("[DialogHandler] Revit process exited, stopping dialog monitoring");
                    checkTimer.Stop();
                    try
                    {
                      hiddenForm.Invoke(new Action(() => hiddenForm.Close()));
                    }
                    catch { }
                    return;
                  }

                  // Try to close "Manage Links" and similar dialogs
                  try
                  {
                    CloseManageLinksDialogs();
                  }
                  catch (Exception ex)
                  {
                    LogHelper.Log($"[DialogHandler] Error in CloseManageLinksDialogs: {ex.Message}");
                  }

                  // Try to handle security dialog (only once)
                  if (!securityDialogHandled)
                  {
                    try
                    {
                      var securityDialog = FindSecurityDialog();
                      if (securityDialog != null)
                      {
                        LogHelper.Log("[DialogHandler] Security dialog found, attempting to click 'Always Load'...");
                        if (ClickAlwaysLoadButton(securityDialog))
                        {
                          LogHelper.Log("[DialogHandler] SUCCESS: Security dialog handled (clicked 'Always Load')");
                          securityDialogHandled = true;
                        }
                        else
                        {
                          LogHelper.Log("[DialogHandler] Failed to click 'Always Load' button, will retry...");
                        }
                      }
                    }
                    catch (Exception ex)
                    {
                      LogHelper.Log($"[DialogHandler] Error handling security dialog: {ex.Message}");
                    }
                  }

                  // Log progress every 15 attempts (15 seconds)
                  if (attempt % 15 == 0)
                  {
                    LogHelper.Log($"[DialogHandler] Still monitoring... (attempt {attempt}/{maxAttempts})");
                  }
                }
                catch (Exception ex)
                {
                  LogHelper.Log($"[DialogHandler] Error during dialog monitoring: {ex.Message}");
                  LogHelper.Log($"[DialogHandler] Error stack trace: {ex}");
                }
              }
              catch (Exception ex)
              {
                // Catch any exception in the timer handler itself
                LogHelper.Log($"[DialogHandler] CRITICAL ERROR in timer handler: {ex.Message}");
                LogHelper.Log($"[DialogHandler] CRITICAL ERROR stack trace: {ex}");
                // Don't stop the timer - keep trying
              }
            };
            
            hiddenForm.Load += (s, e) => 
            { 
              hiddenForm.Hide();
              checkTimer.Start();
              threadReady.Set(); // Signal that the thread is ready
            };
            
            // Show the form (hidden) to initialize the message loop
            hiddenForm.Show();
            
            // Start the message loop (this blocks until the form is closed)
            System.Windows.Forms.Application.Run(hiddenForm);
          }
        }
        catch (Exception ex)
        {
          LogHelper.Log($"[DialogHandler] Error in STA thread: {ex.Message}");
        }
        finally
        {
          threadReady.Set(); // Ensure we signal even on error
        }
      });
      
      _staThread.SetApartmentState(ApartmentState.STA);
      _staThread.IsBackground = true;
      _staThread.Start();
      
      // Wait for the thread to be ready
      threadReady.WaitOne(2000);
      
      LogHelper.Log("[DialogHandler] Started monitoring for Revit dialogs on STA thread");
    }

    /// <summary>
    /// Stops the dialog handler.
    /// </summary>
    public void Stop()
    {
      if (!_isRunning)
        return;

      _isRunning = false;
      _cancellationTokenSource?.Cancel();
      
      // The cancellation token will cause the timer to stop and close the form
      // Wait for the STA thread to finish (it should exit within 2 seconds when timer stops)
      if (_staThread != null && _staThread.IsAlive)
      {
        if (!_staThread.Join(3000))
        {
          LogHelper.Log("[DialogHandler] Warning: STA thread did not exit cleanly, forcing exit");
          try
          {
            // Try to exit the thread's message loop
            System.Windows.Forms.Application.ExitThread();
          }
          catch { }
        }
      }
      
      _cancellationTokenSource?.Dispose();
      LogHelper.Log("[DialogHandler] Stopped monitoring");
    }

    private async Task MonitorDialogs(CancellationToken cancellationToken)
    {
      const int maxAttempts = 150; // 5 minutes (150 * 2 seconds)
      int attempt = 0;
      bool securityDialogHandled = false;

      while (attempt < maxAttempts && !cancellationToken.IsCancellationRequested)
      {
        attempt++;

        try
        {
          // Check if Revit process still exists
          var revitProcess = Process.GetProcesses().FirstOrDefault(p => p.Id == _revitProcessId);
          if (revitProcess == null || revitProcess.HasExited)
          {
            LogHelper.Log("[DialogHandler] Revit process exited, stopping dialog monitoring");
            break;
          }

          // Try to close "Manage Links" and similar dialogs
          CloseManageLinksDialogs();

          // Try to handle security dialog (only once)
          if (!securityDialogHandled)
          {
            var securityDialog = FindSecurityDialog();
            if (securityDialog != null)
            {
              LogHelper.Log("[DialogHandler] Security dialog found, attempting to click 'Always Load'...");
              if (ClickAlwaysLoadButton(securityDialog))
              {
                LogHelper.Log("[DialogHandler] SUCCESS: Security dialog handled (clicked 'Always Load')");
                securityDialogHandled = true;
              }
              else
              {
                LogHelper.Log("[DialogHandler] Failed to click 'Always Load' button, will retry...");
              }
            }
          }

          // Log progress every 15 attempts (30 seconds)
          if (attempt % 15 == 0)
          {
            LogHelper.Log($"[DialogHandler] Still monitoring... (attempt {attempt}/{maxAttempts})");
          }
        }
        catch (Exception ex)
        {
          LogHelper.Log($"[DialogHandler] Error during dialog monitoring: {ex.Message}");
        }

        await Task.Delay(2000, cancellationToken).ConfigureAwait(false);
      }

      // Final attempt to close unwanted dialogs
      CloseManageLinksDialogs();

      if (!securityDialogHandled && attempt >= maxAttempts)
      {
        LogHelper.Log($"[DialogHandler] Timeout: Security dialog not found after {maxAttempts} attempts (may have already been handled or not appeared)");
      }

      LogHelper.Log("[DialogHandler] Dialog monitoring completed");
    }

    /// <summary>
    /// Finds the Revit main window using UI Automation.
    /// </summary>
    private AutomationElement FindRevitWindow()
    {
      try
      {
        // Strategy 1: Find by process (most reliable)
        var revitProcesses = Process.GetProcesses()
          .Where(p => p.ProcessName.IndexOf("Revit", StringComparison.OrdinalIgnoreCase) >= 0)
          .ToList();

        foreach (var proc in revitProcesses)
        {
          try
          {
            if (proc.MainWindowHandle != IntPtr.Zero)
            {
              var window = AutomationElement.FromHandle(proc.MainWindowHandle);
              if (window != null && window.Current.ControlType == ControlType.Window)
              {
                var name = window.Current.Name;
                LogHelper.Log($"[DialogHandler] Found Revit window by process handle: '{name}' (PID: {proc.Id})");
                return window;
              }
            }
          }
          catch { }
        }

        // Strategy 2: Find by window name
        var root = AutomationElement.RootElement;
        var condition = new PropertyCondition(
          AutomationElement.ControlTypeProperty,
          ControlType.Window
        );
        var windows = root.FindAll(TreeScope.Children, condition);

        var revitKeywords = new[] { "Autodesk Revit", "Revit" };
        var excludeKeywords = new[] { "File Explorer", "Explorer", "and 4 more tabs", "and 3 more tabs", "and 2 more tabs" };

        foreach (AutomationElement window in windows)
        {
          try
          {
            var name = window.Current.Name;
            if (string.IsNullOrEmpty(name)) continue;

            // Skip File Explorer windows
            if (excludeKeywords.Any(exclude => name.IndexOf(exclude, StringComparison.OrdinalIgnoreCase) >= 0))
              continue;

            // Check if it matches Revit keywords
            if (revitKeywords.Any(keyword => name.IndexOf(keyword, StringComparison.OrdinalIgnoreCase) >= 0))
            {
              LogHelper.Log($"[DialogHandler] Found Revit window by name: '{name}'");
              return window;
            }
          }
          catch { }
        }
      }
      catch (Exception ex)
      {
        LogHelper.Log($"[DialogHandler] Error finding Revit window: {ex.Message}");
      }

      return null;
    }

    /// <summary>
    /// Identifies if a dialog is the security dialog by checking button characteristics.
    /// This is more reliable and language-agnostic than checking window titles.
    /// </summary>
    private bool IsSecurityDialog(AutomationElement dialog)
    {
      try
      {
        // Look for buttons in the dialog
        var buttonCondition = new PropertyCondition(
          AutomationElement.ControlTypeProperty,
          ControlType.Button
        );
        var buttons = dialog.FindAll(TreeScope.Descendants, buttonCondition);

        if (buttons == null || buttons.Count < 2)
        {
          return false; // Security dialog should have at least 2-3 buttons
        }

        LogHelper.Log($"[DialogHandler] Dialog has {buttons.Count} button(s), checking characteristics...");

        // Characteristic button text patterns for security dialog (various languages)
        var characteristicPatterns = new[]
        {
          "Always", "Load", "Once", "Do Not", "Not Load",
          "Toujours", "charger",  // French
          "Siempre", "cargar",   // Spanish
          "Immer", "laden",       // German
          "Carica", "sempre"      // Italian
        };

        int matchingButtons = 0;
        var buttonTexts = new System.Collections.Generic.List<string>();

        foreach (AutomationElement button in buttons)
        {
          try
          {
            var buttonName = button.Current.Name;
            if (string.IsNullOrEmpty(buttonName)) continue;

            buttonTexts.Add(buttonName);

            // Check if button text matches characteristic patterns
            if (characteristicPatterns.Any(pattern => buttonName.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0))
            {
              matchingButtons++;
              LogHelper.Log($"[DialogHandler]   Found characteristic button: '{buttonName}'");
            }
          }
          catch { }
        }

        LogHelper.Log($"[DialogHandler]   Button texts: {string.Join(", ", buttonTexts)}");
        LogHelper.Log($"[DialogHandler]   Matching buttons: {matchingButtons}");

        // Security dialog characteristics:
        // 1. Has 2-3 buttons
        // 2. At least 2 buttons match characteristic patterns
        if (matchingButtons >= 2)
        {
          LogHelper.Log($"[DialogHandler]   Identified as security dialog (found {matchingButtons} matching buttons)");
          return true;
        }

        // Also check: Security dialog typically has exactly 3 buttons
        // And the first button is usually "Always Load" (leftmost)
        if (buttons.Count == 3)
        {
          // Find leftmost button
          AutomationElement leftmostButton = null;
          double minX = double.MaxValue;
          foreach (AutomationElement button in buttons)
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
            var firstButtonName = leftmostButton.Current.Name;
            LogHelper.Log($"[DialogHandler]   Dialog has 3 buttons. Leftmost button: '{firstButtonName}'");

            // If first button contains characteristic patterns, it's likely the security dialog
            var firstButtonPatterns = new[] { "Always", "Load", "Toujours", "Siempre", "Immer", "Carica" };
            if (firstButtonPatterns.Any(pattern => firstButtonName.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0))
            {
              LogHelper.Log("[DialogHandler]   Identified as security dialog (3 buttons with characteristic first button)");
              return true;
            }
          }
        }
      }
      catch (Exception ex)
      {
        LogHelper.Log($"[DialogHandler] Error in IsSecurityDialog: {ex.Message}");
      }

      return false;
    }

    /// <summary>
    /// Finds the security dialog by searching all top-level windows and within the Revit window.
    /// </summary>
    private AutomationElement FindSecurityDialog()
    {
      try
      {
        // Strategy 1: Search ALL top-level windows for the security dialog
        LogHelper.Log("[DialogHandler] Searching all top-level windows for security dialog...");
        var root = AutomationElement.RootElement;
        var condition = new PropertyCondition(
          AutomationElement.ControlTypeProperty,
          ControlType.Window
        );
        var allWindows = root.FindAll(TreeScope.Children, condition);
        LogHelper.Log($"[DialogHandler] Checking {allWindows.Count} top-level windows...");

        foreach (AutomationElement window in allWindows)
        {
          try
          {
            var name = window.Current.Name;
            LogHelper.Log($"[DialogHandler] Checking top-level window: '{name}'");

            // Identify by button characteristics
            if (IsSecurityDialog(window))
            {
              LogHelper.Log($"[DialogHandler] FOUND SECURITY DIALOG (top-level window): '{name}' (identified by button characteristics)");
              return window;
            }
          }
          catch (Exception ex)
          {
            LogHelper.Log($"[DialogHandler] Error checking top-level window: {ex.Message}");
          }
        }

        // Strategy 2: Search within Revit window
        var revitWindow = FindRevitWindow();
        if (revitWindow != null)
        {
          LogHelper.Log("[DialogHandler] Searching for security dialog within Revit window (by button characteristics)...");

          // Search for dialogs within Revit window (descendants)
          var dialogTypes = new[] { ControlType.Window, ControlType.Pane };

          foreach (var dialogType in dialogTypes)
          {
            var dialogCondition = new PropertyCondition(
              AutomationElement.ControlTypeProperty,
              dialogType
            );
            var dialogs = revitWindow.FindAll(TreeScope.Descendants, dialogCondition);
            LogHelper.Log($"[DialogHandler] Found {dialogs.Count} {dialogType.ProgrammaticName} elements in Revit window");

            foreach (AutomationElement dialog in dialogs)
            {
              try
              {
                var name = dialog.Current.Name;
                LogHelper.Log($"[DialogHandler] Checking dialog: '{name}' (Type: {dialogType.ProgrammaticName})");

                // Identify by button characteristics
                if (IsSecurityDialog(dialog))
                {
                  LogHelper.Log($"[DialogHandler] FOUND SECURITY DIALOG: '{name}' (identified by button characteristics)");
                  return dialog;
                }
              }
              catch (Exception ex)
              {
                LogHelper.Log($"[DialogHandler] Error checking dialog: {ex.Message}");
              }
            }
          }

          // Also check if the security dialog is a direct child window of Revit
          var childCondition = new PropertyCondition(
            AutomationElement.ControlTypeProperty,
            ControlType.Window
          );
          var childWindows = revitWindow.FindAll(TreeScope.Children, childCondition);
          LogHelper.Log($"[DialogHandler] Found {childWindows.Count} child windows of Revit");

          foreach (AutomationElement childWindow in childWindows)
          {
            try
            {
              var name = childWindow.Current.Name;
              LogHelper.Log($"[DialogHandler] Checking child window: '{name}'");

              if (IsSecurityDialog(childWindow))
              {
                LogHelper.Log($"[DialogHandler] FOUND SECURITY DIALOG (child window): '{name}' (identified by button characteristics)");
                return childWindow;
              }
            }
            catch { }
          }
        }
        else
        {
          LogHelper.Log("[DialogHandler] Revit window not found, but already checked all top-level windows");
        }
      }
      catch (Exception ex)
      {
        LogHelper.Log($"[DialogHandler] Error in FindSecurityDialog: {ex.Message}");
      }

      return null;
    }

    /// <summary>
    /// Clicks the "Always Load" button in the security dialog.
    /// </summary>
    private bool ClickAlwaysLoadButton(AutomationElement dialog)
    {
      try
      {
        var buttonCondition = new PropertyCondition(
          AutomationElement.ControlTypeProperty,
          ControlType.Button
        );
        var buttons = dialog.FindAll(TreeScope.Descendants, buttonCondition);

        LogHelper.Log($"[DialogHandler] Found {buttons.Count} button(s) in dialog");

        if (buttons != null && buttons.Count > 0)
        {
          // Log all button names for debugging
          var allButtonNames = new System.Collections.Generic.List<string>();
          foreach (AutomationElement btn in buttons)
          {
            try
            {
              allButtonNames.Add(btn.Current.Name);
            }
            catch { }
          }
          LogHelper.Log($"[DialogHandler] Button names: {string.Join(", ", allButtonNames)}");

          // Strategy 1: Find button by text pattern (most reliable)
          var alwaysLoadPatterns = new[] { "Always", "Load", "Toujours", "Siempre", "Immer", "Carica" };
          AutomationElement targetButton = null;

          foreach (AutomationElement button in buttons)
          {
            try
            {
              var buttonName = button.Current.Name;
              if (string.IsNullOrEmpty(buttonName)) continue;

              if (alwaysLoadPatterns.Any(pattern => buttonName.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0))
              {
                LogHelper.Log($"[DialogHandler] Found 'Always Load' button by pattern: '{buttonName}'");
                targetButton = button;
                break;
              }
            }
            catch { }
          }

          // Strategy 2: If not found by pattern, use leftmost button (typically "Always Load" is first)
          if (targetButton == null)
          {
            LogHelper.Log("[DialogHandler] Could not find button by pattern, trying leftmost button...");
            AutomationElement leftmostButton = null;
            double minX = double.MaxValue;
            foreach (AutomationElement button in buttons)
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
            targetButton = leftmostButton;
            if (targetButton != null)
            {
              var name = targetButton.Current.Name;
              LogHelper.Log($"[DialogHandler] Using leftmost button: '{name}'");
            }
          }

          // Strategy 3: Fallback to first button (index 0)
          if (targetButton == null)
          {
            LogHelper.Log("[DialogHandler] Using first button (index 0) as fallback...");
            targetButton = buttons[0];
            var name = targetButton.Current.Name;
            LogHelper.Log($"[DialogHandler] First button: '{name}'");
          }

          // Click the button
          if (targetButton != null)
          {
            try
            {
              if (targetButton.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
              {
                Thread.Sleep(500); // Small delay to ensure dialog is ready
                var buttonName = targetButton.Current.Name;
                LogHelper.Log($"[DialogHandler] Attempting to click button: '{buttonName}'");
                ((InvokePattern)pattern).Invoke();
                LogHelper.Log($"[DialogHandler] SUCCESS: Clicked button '{buttonName}'");
                return true;
              }
              else
              {
                LogHelper.Log("[DialogHandler] Could not get InvokePattern for button");
              }
            }
            catch (Exception ex)
            {
              LogHelper.Log($"[DialogHandler] Error invoking button: {ex.Message}");
            }
          }
        }
        else
        {
          LogHelper.Log("[DialogHandler] No buttons found in dialog!");
        }
      }
      catch (Exception ex)
      {
        LogHelper.Log($"[DialogHandler] Error in ClickAlwaysLoadButton: {ex.Message}");
      }

      return false;
    }

    /// <summary>
    /// Closes "Manage Links" and similar dialogs that can block automation.
    /// Also closes any other blocking dialogs (errors, warnings, info dialogs, etc.)
    /// </summary>
    private void CloseManageLinksDialogs()
    {
      try
      {
        // Expanded list of dialogs to automatically close
        var dialogsToClose = new[] 
        { 
          "Manage Links", 
          "ManageLinks", 
          "Link Manager", 
          "External References",
          "Warning",
          "Error",
          "Information",
          "Confirmation",
          "Alert",
          "Notice",
          "Message",
          "Dialog",
          "Revit",
          "Autodesk"
        };
        
        // Also close any modal dialogs that might block
        CloseBlockingDialogs();

        // Strategy 1: Search all top-level windows
        var root = AutomationElement.RootElement;
        var condition = new PropertyCondition(
          AutomationElement.ControlTypeProperty,
          ControlType.Window
        );
        var windows = root.FindAll(TreeScope.Children, condition);

        LogHelper.Log($"[DialogHandler] Checking {windows.Count} top-level windows for dialogs to close...");

        foreach (AutomationElement window in windows)
        {
          try
          {
            var name = window.Current.Name;
            if (string.IsNullOrEmpty(name)) continue;

              foreach (var dialogName in dialogsToClose)
              {
                if (name.IndexOf(dialogName, StringComparison.OrdinalIgnoreCase) >= 0)
              {
                LogHelper.Log($"[DialogHandler] Found dialog to close (top-level): '{name}', attempting to close...");
                if (CloseDialogWindow(window, name))
                {
                  return;
                }
              }
            }
          }
          catch { }
        }

        // Strategy 2: Search within Revit window for child windows
        var revitWindow = FindRevitWindow();
        if (revitWindow != null)
        {
          LogHelper.Log("[DialogHandler] Searching within Revit window for dialogs to close...");
          var childCondition = new PropertyCondition(
            AutomationElement.ControlTypeProperty,
            ControlType.Window
          );
          var childWindows = revitWindow.FindAll(TreeScope.Children, childCondition);

          LogHelper.Log($"[DialogHandler] Found {childWindows.Count} child windows of Revit");
          foreach (AutomationElement childWindow in childWindows)
          {
            try
            {
              var name = childWindow.Current.Name;
              if (string.IsNullOrEmpty(name)) continue;

              LogHelper.Log($"[DialogHandler] Checking child window: '{name}'");

              foreach (var dialogName in dialogsToClose)
              {
                if (name.IndexOf(dialogName, StringComparison.OrdinalIgnoreCase) >= 0)
                {
                  LogHelper.Log($"[DialogHandler] Found dialog to close (child window): '{name}', attempting to close...");
                  if (CloseDialogWindow(childWindow, name))
                  {
                    return;
                  }
                }
              }
            }
            catch { }
          }
        }
      }
      catch (Exception ex)
      {
        LogHelper.Log($"[DialogHandler] Error in CloseManageLinksDialogs: {ex.Message}");
      }
    }

    /// <summary>
    /// Closes any blocking modal dialogs that might prevent automation from proceeding.
    /// This is a more aggressive approach to close any dialogs that might appear.
    /// </summary>
    private void CloseBlockingDialogs()
    {
      try
      {
        var revitWindow = FindRevitWindow();
        if (revitWindow == null)
          return;

        // Find all child windows of Revit that might be blocking dialogs
        var childCondition = new PropertyCondition(
          AutomationElement.ControlTypeProperty,
          ControlType.Window
        );
        var childWindows = revitWindow.FindAll(TreeScope.Children, childCondition);

        foreach (AutomationElement childWindow in childWindows)
        {
          try
          {
            var name = childWindow.Current.Name;
            if (string.IsNullOrEmpty(name)) continue;

            // Skip the security dialog (handled separately) and main Revit window
            if (name.IndexOf("Security", StringComparison.OrdinalIgnoreCase) >= 0 ||
                name.IndexOf("Unsigned", StringComparison.OrdinalIgnoreCase) >= 0)
              continue;

            // Check if this is a modal dialog by looking for OK, Cancel, or Close buttons
            var buttonCondition = new PropertyCondition(
              AutomationElement.ControlTypeProperty,
              ControlType.Button
            );
            var buttons = childWindow.FindAll(TreeScope.Descendants, buttonCondition);

            if (buttons != null && buttons.Count > 0)
            {
              // Check if it has typical dialog buttons
              bool hasDialogButton = false;
              var dialogButtonNames = new[] { "OK", "Cancel", "Close", "Yes", "No", "Accept", "Dismiss" };
              
              foreach (AutomationElement button in buttons)
              {
                try
                {
                  var buttonName = button.Current.Name;
                  if (dialogButtonNames.Any(btn => buttonName.IndexOf(btn, StringComparison.OrdinalIgnoreCase) >= 0))
                  {
                    hasDialogButton = true;
                    break;
                  }
                }
                catch { }
              }

              // If it looks like a dialog, try to close it
              if (hasDialogButton)
              {
                LogHelper.Log($"[DialogHandler] Found potential blocking dialog: '{name}', attempting to close...");
                
                // Try to click OK or Accept button first (preferred for info dialogs)
                bool closed = false;
                var preferredButtons = new[] { "OK", "Accept", "Yes" };
                foreach (var preferredBtn in preferredButtons)
                {
                  foreach (AutomationElement button in buttons)
                  {
                    try
                    {
                      var buttonName = button.Current.Name;
                      if (buttonName.IndexOf(preferredBtn, StringComparison.OrdinalIgnoreCase) >= 0)
                      {
                        if (button.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
                        {
                          LogHelper.Log($"[DialogHandler]   Clicking '{buttonName}' button to close dialog...");
                          ((InvokePattern)pattern).Invoke();
                          Thread.Sleep(300);
                          closed = true;
                          break;
                        }
                      }
                    }
                    catch { }
                  }
                  if (closed) break;
                }

                // If preferred buttons didn't work, try closing the window
                if (!closed)
                {
                  CloseDialogWindow(childWindow, name);
                }
              }
            }
          }
          catch { }
        }
      }
      catch (Exception ex)
      {
        LogHelper.Log($"[DialogHandler] Error in CloseBlockingDialogs: {ex.Message}");
      }
    }

    /// <summary>
    /// Closes a dialog window using various methods (Close button, Escape key, etc.).
    /// Tries multiple methods to ensure the dialog is closed.
    /// </summary>
    private bool CloseDialogWindow(AutomationElement window, string name)
    {
      try
      {
        // Method 1: Try to find and click OK/Accept/Yes buttons first (for info/error dialogs)
        try
        {
          var okButtonNames = new[] { "OK", "Accept", "Yes", "Continue", "Dismiss" };
          var buttonCondition = new PropertyCondition(
            AutomationElement.ControlTypeProperty,
            ControlType.Button
          );
          var buttons = window.FindAll(TreeScope.Descendants, buttonCondition);

          foreach (AutomationElement button in buttons)
          {
            try
            {
              var buttonName = button.Current.Name;
              if (string.IsNullOrEmpty(buttonName)) continue;

              if (okButtonNames.Any(okName => buttonName.IndexOf(okName, StringComparison.OrdinalIgnoreCase) >= 0))
              {
                if (button.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
                {
                  LogHelper.Log($"[DialogHandler]   Found '{buttonName}' button, clicking to close dialog '{name}'...");
                  ((InvokePattern)pattern).Invoke();
                  Thread.Sleep(500);
                  LogHelper.Log($"[DialogHandler]   SUCCESS: Closed dialog '{name}' via '{buttonName}' button");
                  return true;
                }
              }
            }
            catch { }
          }
        }
        catch (Exception ex)
        {
          LogHelper.Log($"[DialogHandler]   Could not find OK/Accept buttons: {ex.Message}");
        }

        // Method 2: Try to find and click the close button (X button)
        var closeButtonNames = new[] { "Close", "×", "✕" };
        foreach (var closeButtonName in closeButtonNames)
        {
          try
          {
            var closeButton = window.FindFirst(
              TreeScope.Descendants,
              new PropertyCondition(AutomationElement.NameProperty, closeButtonName)
            );

            if (closeButton != null)
            {
              if (closeButton.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
              {
                LogHelper.Log($"[DialogHandler]   Found close button '{closeButtonName}', clicking...");
                ((InvokePattern)pattern).Invoke();
                Thread.Sleep(500);
                LogHelper.Log($"[DialogHandler]   SUCCESS: Closed dialog '{name}' via close button");
                return true;
              }
            }
          }
          catch (Exception ex)
          {
            LogHelper.Log($"[DialogHandler]   Could not use close button '{closeButtonName}': {ex.Message}");
          }
        }

        // Method 3: Try to find close button by AutomationId
        try
        {
          var buttonCondition = new AndCondition(
            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button),
            new PropertyCondition(AutomationElement.AutomationIdProperty, "Close")
          );
          var closeButton = window.FindFirst(TreeScope.Descendants, buttonCondition);
          if (closeButton != null)
          {
            if (closeButton.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
            {
              LogHelper.Log("[DialogHandler]   Found close button by AutomationId, clicking...");
              ((InvokePattern)pattern).Invoke();
              Thread.Sleep(500);
              LogHelper.Log($"[DialogHandler]   SUCCESS: Closed dialog '{name}' via AutomationId");
              return true;
            }
          }
        }
        catch (Exception ex)
        {
          LogHelper.Log($"[DialogHandler]   Could not find close button by AutomationId: {ex.Message}");
        }

        // Method 4: Try WindowPattern.Close() if available
        try
        {
          if (window.TryGetCurrentPattern(WindowPattern.Pattern, out object windowPattern))
          {
            LogHelper.Log("[DialogHandler]   Using WindowPattern.Close() to close dialog...");
            ((WindowPattern)windowPattern).Close();
            Thread.Sleep(500);
            LogHelper.Log($"[DialogHandler]   SUCCESS: Closed dialog '{name}' via WindowPattern.Close()");
            return true;
          }
        }
        catch (Exception ex)
        {
          LogHelper.Log($"[DialogHandler]   Could not use WindowPattern.Close(): {ex.Message}");
        }

        // Method 5: Send Escape key (focus the window first)
        try
        {
          // Try to set focus to the window
          try
          {
            window.SetFocus();
            Thread.Sleep(200);
          }
          catch { }

          // Send Escape key multiple times to ensure it's processed
          for (int i = 0; i < 3; i++)
          {
            SendKeys.SendWait("{ESC}");
            Thread.Sleep(200);
          }
          Thread.Sleep(300);
          LogHelper.Log($"[DialogHandler]   Sent Escape key to close dialog '{name}'");
          return true;
        }
        catch (Exception ex)
        {
          LogHelper.Log($"[DialogHandler]   Could not send Escape key: {ex.Message}");
        }

        // Method 6: Try Alt+F4 (close window shortcut)
        try
        {
          window.SetFocus();
          Thread.Sleep(200);
          SendKeys.SendWait("%{F4}");
          Thread.Sleep(500);
          LogHelper.Log($"[DialogHandler]   Sent Alt+F4 to close dialog '{name}'");
          return true;
        }
        catch (Exception ex)
        {
          LogHelper.Log($"[DialogHandler]   Could not send Alt+F4: {ex.Message}");
        }

        LogHelper.Log($"[DialogHandler]   WARNING: Could not close dialog '{name}' - all methods failed");
      }
      catch (Exception ex)
      {
        LogHelper.Log($"[DialogHandler]   ERROR in CloseDialogWindow: {ex.Message}");
        LogHelper.Log($"[DialogHandler]   ERROR Stack Trace: {ex}");
      }

      return false;
    }
  }
}

