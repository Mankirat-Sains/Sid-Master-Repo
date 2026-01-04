using System;
using System.IO;
using System.Windows.Forms;

namespace Speckle.AutoInstaller.UI
{
  public partial class FolderSelectionPanel : UserControl
  {
    private TextBox _txtFolder;
    private Button _btnBrowse;
    private CheckBox _chkSubfolders;
    private Label _lblTitle;
    private FolderBrowserDialog _folderDialog;

    public string WatchFolder => _txtFolder.Text.Trim();
    public bool MonitorSubfolders => _chkSubfolders.Checked;

    public FolderSelectionPanel()
    {
      InitializeComponent();
    }

    private void InitializeComponent()
    {
      this.Size = new System.Drawing.Size(580, 400);
      this.Dock = DockStyle.Fill;

      _lblTitle = new Label
      {
        Text = "Which folder should be monitored?",
        Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Bold),
        Location = new System.Drawing.Point(20, 20),
        Size = new System.Drawing.Size(500, 30)
      };

      var lblFolder = new Label
      {
        Text = "Folder:",
        Location = new System.Drawing.Point(20, 70),
        Size = new System.Drawing.Size(100, 20)
      };

      _txtFolder = new TextBox
      {
        Location = new System.Drawing.Point(130, 68),
        Size = new System.Drawing.Size(350, 20),
        Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "RevitProjects")
      };

      _btnBrowse = new Button
      {
        Text = "Browse...",
        Location = new System.Drawing.Point(490, 66),
        Size = new System.Drawing.Size(80, 25)
      };
      _btnBrowse.Click += BtnBrowse_Click;

      _chkSubfolders = new CheckBox
      {
        Text = "Monitor subfolders",
        Location = new System.Drawing.Point(20, 110),
        Size = new System.Drawing.Size(200, 20),
        Checked = true
      };

      _folderDialog = new FolderBrowserDialog
      {
        Description = "Select the folder to monitor for Revit files",
        ShowNewFolderButton = true
      };

      this.Controls.Add(_lblTitle);
      this.Controls.Add(lblFolder);
      this.Controls.Add(_txtFolder);
      this.Controls.Add(_btnBrowse);
      this.Controls.Add(_chkSubfolders);
    }

    private void BtnBrowse_Click(object sender, EventArgs e)
    {
      if (Directory.Exists(_txtFolder.Text))
      {
        _folderDialog.SelectedPath = _txtFolder.Text;
      }

      if (_folderDialog.ShowDialog() == DialogResult.OK)
      {
        _txtFolder.Text = _folderDialog.SelectedPath;
      }
    }

    public bool ValidateInput()
    {
      if (string.IsNullOrWhiteSpace(WatchFolder))
      {
        MessageBox.Show("Please select a folder to monitor.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        _txtFolder.Focus();
        return false;
      }

      // Create folder if it doesn't exist
      if (!Directory.Exists(WatchFolder))
      {
        try
        {
          Directory.CreateDirectory(WatchFolder);
        }
        catch (Exception ex)
        {
          MessageBox.Show($"Cannot create folder: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
          return false;
        }
      }

      return true;
    }
  }
}


