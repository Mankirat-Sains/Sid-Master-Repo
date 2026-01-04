using System;
using System.Windows.Forms;

namespace Speckle.AutoInstaller.UI
{
  /// <summary>
  /// Hidden form that keeps the application message loop alive when running as a background service.
  /// This is necessary for timers, MessageBox calls, and other Windows Forms components to work properly.
  /// </summary>
  public class BackgroundServiceForm : Form
  {
    public BackgroundServiceForm()
    {
      // Make the form invisible
      this.WindowState = FormWindowState.Minimized;
      this.ShowInTaskbar = false;
      this.FormBorderStyle = FormBorderStyle.None;
      this.Size = new System.Drawing.Size(0, 0);
      this.Visible = false;
      this.Opacity = 0;
      
      // Prevent the form from showing
      this.Load += (s, e) => { this.Hide(); };
    }

    protected override void SetVisibleCore(bool value)
    {
      // Always keep the form hidden
      base.SetVisibleCore(false);
    }
  }
}

