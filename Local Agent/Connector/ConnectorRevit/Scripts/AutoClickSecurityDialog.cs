using System;
using System.Diagnostics;
using System.Threading;
using System.Windows.Automation;

namespace SpeckleRevitInstaller
{
    /// <summary>
    /// Standalone tool to automatically click "Always Load" on Revit security dialog.
    /// Run this BEFORE launching Revit, or while Revit is starting.
    /// </summary>
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== Revit Security Dialog Auto-Clicker ===");
            Console.WriteLine("Monitoring for 'Security - Unsigned Add-In' dialog...");
            Console.WriteLine("Press Ctrl+C to stop\n");

            int maxAttempts = 60; // Try for 60 seconds (30 attempts * 2 seconds)
            int attempt = 0;
            bool found = false;

            while (attempt < maxAttempts && !found)
            {
                attempt++;

                var dialog = FindSecurityDialog();

                if (dialog != null)
                {
                    Console.WriteLine("\nSecurity dialog found! Attempting to click 'Always Load'...");

                    if (ClickAlwaysLoadButton(dialog))
                    {
                        Console.WriteLine("\n=== SUCCESS ===");
                        Console.WriteLine("Security dialog handled successfully!");
                        found = true;
                        break;
                    }
                    else
                    {
                        Console.WriteLine("Failed to click button, will retry...");
                    }
                }
                else
                {
                    if (attempt % 5 == 0)
                    {
                        Console.WriteLine($"Still monitoring... (attempt {attempt}/{maxAttempts})");
                    }
                }

                Thread.Sleep(2000); // Wait 2 seconds between attempts
            }

            if (!found)
            {
                Console.WriteLine("\n=== TIMEOUT ===");
                Console.WriteLine($"Security dialog not found after {maxAttempts} attempts");
                Console.WriteLine("Either the dialog already appeared and was dismissed, or Revit hasn't started yet");
            }

            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }

        static AutomationElement FindSecurityDialog()
        {
            try
            {
                var root = AutomationElement.RootElement;

                // Get all top-level windows
                var condition = new PropertyCondition(
                    AutomationElement.ControlTypeProperty,
                    ControlType.Window
                );

                var windows = root.FindAll(TreeScope.Children, condition);

                string[] securityKeywords = { "Security", "Unsigned", "Add-In", "AddIn", "Publisher", "Verified" };

                foreach (AutomationElement window in windows)
                {
                    try
                    {
                        var name = window.Current.Name;
                        if (string.IsNullOrEmpty(name))
                            continue;

                        // Check if window title contains security-related keywords
                        bool isSecurityDialog = false;
                        foreach (var keyword in securityKeywords)
                        {
                            if (name.Contains(keyword, StringComparison.OrdinalIgnoreCase))
                            {
                                isSecurityDialog = true;
                                break;
                            }
                        }

                        if (isSecurityDialog)
                        {
                            Console.WriteLine($"Found security dialog: '{name}'");
                            return window;
                        }
                    }
                    catch { }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error finding security dialog: {ex.Message}");
            }

            return null;
        }

        static bool ClickAlwaysLoadButton(AutomationElement dialog)
        {
            try
            {
                // Method 1: Try by button index (first button is usually "Always Load")
                var buttonCondition = new PropertyCondition(
                    AutomationElement.ControlTypeProperty,
                    ControlType.Button
                );

                var buttons = dialog.FindAll(TreeScope.Descendants, buttonCondition);

                if (buttons != null && buttons.Count > 0)
                {
                    // Try first button (index 0)
                    var firstButton = buttons[0];
                    var buttonName = firstButton.Current.Name;
                    Console.WriteLine($"Trying first button: '{buttonName}'");

                    // Try to get InvokePattern
                    if (firstButton.TryGetCurrentPattern(InvokePattern.Pattern, out object pattern))
                    {
                        var invokePattern = pattern as InvokePattern;
                        if (invokePattern != null)
                        {
                            invokePattern.Invoke();
                            Console.WriteLine($"SUCCESS: Clicked button '{buttonName}' using InvokePattern");
                            return true;
                        }
                    }
                    else
                    {
                        Console.WriteLine("Could not get InvokePattern, trying alternative methods...");

                        // Try finding by text
                        foreach (AutomationElement button in buttons)
                        {
                            var name = button.Current.Name;
                            if (!string.IsNullOrEmpty(name) &&
                                (name.Contains("Always", StringComparison.OrdinalIgnoreCase) ||
                                 name.Contains("Load", StringComparison.OrdinalIgnoreCase) ||
                                 name == "Always Load"))
                            {
                                Console.WriteLine($"Found 'Always Load' button: '{name}'");
                                if (button.TryGetCurrentPattern(InvokePattern.Pattern, out object btnPattern))
                                {
                                    var btnInvokePattern = btnPattern as InvokePattern;
                                    if (btnInvokePattern != null)
                                    {
                                        btnInvokePattern.Invoke();
                                        Console.WriteLine("SUCCESS: Clicked 'Always Load' button");
                                        return true;
                                    }
                                }
                            }
                        }

                        // Try leftmost button by position
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
                            var name = leftmostButton.Current.Name;
                            Console.WriteLine($"Trying leftmost button: '{name}'");
                            if (leftmostButton.TryGetCurrentPattern(InvokePattern.Pattern, out object leftPattern))
                            {
                                var leftInvokePattern = leftPattern as InvokePattern;
                                if (leftInvokePattern != null)
                                {
                                    leftInvokePattern.Invoke();
                                    Console.WriteLine($"SUCCESS: Clicked leftmost button '{name}'");
                                    return true;
                                }
                            }
                        }
                    }
                }

                Console.WriteLine("Could not find or click 'Always Load' button");
                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error clicking button: {ex.Message}");
                return false;
            }
        }
    }
}


