using System;
using System.Windows.Forms;
using Speckle.AutoInstaller.Models;

namespace Speckle.AutoInstaller.UI
{
  public partial class SetupWizard : Form
  {
    private TabControl _steps;
    private Button _btnNext;
    private Button _btnBack;
    private Button _btnCancel;
    private int _currentStep = 0;

    private CredentialPanel _credentialStep;
    private RevitSelectionPanel _revitStep;
    private SchedulePanel _scheduleStep;
    private FolderSelectionPanel _folderStep;

    private SetupData _setupData;

    public SetupWizard()
    {
      InitializeComponent();
      _setupData = new SetupData();
    }

    private void InitializeComponent()
    {
      this.Text = "Speckle Auto-Installer Setup";
      this.Size = new System.Drawing.Size(650, 550);
      this.MinimumSize = new System.Drawing.Size(500, 400);
      this.StartPosition = FormStartPosition.CenterScreen;
      this.FormBorderStyle = FormBorderStyle.Sizable; // Make resizable
      this.MaximizeBox = true;
      this.MinimizeBox = true;

      // Create tab control (hidden tabs, we'll show panels manually)
      // Use Anchor to resize automatically, leaving space at bottom for buttons
      _steps = new TabControl
      {
        Location = new System.Drawing.Point(0, 0),
        Size = new System.Drawing.Size(650, 500),
        Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
        Appearance = TabAppearance.FlatButtons,
        ItemSize = new System.Drawing.Size(0, 1),
        SizeMode = TabSizeMode.Fixed
      };

      // Create step panels
      _credentialStep = new CredentialPanel();
      _revitStep = new RevitSelectionPanel();
      _scheduleStep = new SchedulePanel();
      _folderStep = new FolderSelectionPanel();

      // Add panels as tabs
      var tab1 = new TabPage();
      tab1.Controls.Add(_credentialStep);
      _steps.TabPages.Add(tab1);

      var tab2 = new TabPage();
      tab2.Controls.Add(_revitStep);
      _steps.TabPages.Add(tab2);

      var tab3 = new TabPage();
      tab3.Controls.Add(_scheduleStep);
      _steps.TabPages.Add(tab3);

      var tab4 = new TabPage();
      tab4.Controls.Add(_folderStep);
      _steps.TabPages.Add(tab4);

      // Navigation buttons - use Anchor to position at bottom-right
      // Don't set Location here - let the Load event handle it after form is sized
      _btnBack = new Button
      {
        Text = "< Back",
        Size = new System.Drawing.Size(100, 35),
        Anchor = AnchorStyles.Bottom | AnchorStyles.Right,
        Enabled = false
      };
      _btnBack.Click += BtnBack_Click;

      _btnNext = new Button
      {
        Text = "Next >",
        Size = new System.Drawing.Size(100, 35),
        Anchor = AnchorStyles.Bottom | AnchorStyles.Right
      };
      _btnNext.Click += BtnNext_Click;

      _btnCancel = new Button
      {
        Text = "Cancel",
        Size = new System.Drawing.Size(100, 35),
        Anchor = AnchorStyles.Bottom | AnchorStyles.Right
      };
      _btnCancel.Click += (s, e) => this.DialogResult = DialogResult.Cancel;

      // Add controls - buttons first so they appear on top
      this.Controls.Add(_steps);
      this.Controls.Add(_btnBack);
      this.Controls.Add(_btnNext);
      this.Controls.Add(_btnCancel);

      // Handle Load event to position buttons after form is fully initialized
      this.Load += (s, e) =>
      {
        int buttonY = this.ClientSize.Height - 45;
        int buttonSpacing = 110;
        _btnBack.Location = new System.Drawing.Point(this.ClientSize.Width - (buttonSpacing * 2 + 100), buttonY);
        _btnNext.Location = new System.Drawing.Point(this.ClientSize.Width - (buttonSpacing + 100), buttonY);
        _btnCancel.Location = new System.Drawing.Point(this.ClientSize.Width - 100, buttonY);
      };

      // Handle resize to adjust TabControl to leave space for buttons
      this.Resize += SetupWizard_Resize;

      UpdateStepDisplay();
    }

    private void SetupWizard_Resize(object sender, EventArgs e)
    {
      // Adjust TabControl to leave space for buttons at bottom (55px for button height + padding)
      const int buttonAreaHeight = 55;
      if (_steps != null && this.ClientSize.Height > buttonAreaHeight)
      {
        _steps.Height = this.ClientSize.Height - buttonAreaHeight;
        _steps.Width = this.ClientSize.Width;
      }
      
      // Update button positions to stay at bottom when window resizes
      if (_btnBack != null && _btnNext != null && _btnCancel != null)
      {
        int buttonY = this.ClientSize.Height - 45;
        int buttonSpacing = 110;
        _btnBack.Location = new System.Drawing.Point(this.ClientSize.Width - (buttonSpacing * 2 + 100), buttonY);
        _btnNext.Location = new System.Drawing.Point(this.ClientSize.Width - (buttonSpacing + 100), buttonY);
        _btnCancel.Location = new System.Drawing.Point(this.ClientSize.Width - 100, buttonY);
      }
    }

    private void BtnNext_Click(object sender, EventArgs e)
    {
      if (!ValidateCurrentStep())
        return;

      if (_currentStep < _steps.TabPages.Count - 1)
      {
        _currentStep++;
        UpdateStepDisplay();
      }
      else
      {
        // Last step - finish
        CollectSetupData();
        this.DialogResult = DialogResult.OK;
        this.Close();
      }
    }

    private void BtnBack_Click(object sender, EventArgs e)
    {
      if (_currentStep > 0)
      {
        _currentStep--;
        UpdateStepDisplay();
      }
    }

    private void UpdateStepDisplay()
    {
      _steps.SelectedIndex = _currentStep;
      _btnBack.Enabled = _currentStep > 0;

      if (_currentStep == _steps.TabPages.Count - 1)
      {
        _btnNext.Text = "Finish";
      }
      else
      {
        _btnNext.Text = "Next >";
      }

      this.Text = $"Speckle Auto-Installer Setup - Step {_currentStep + 1} of {_steps.TabPages.Count}";
    }

    private bool ValidateCurrentStep()
    {
      switch (_currentStep)
      {
        case 0: // Credentials
          return _credentialStep.ValidateInput();
        case 1: // Revit Selection
          return _revitStep.ValidateInput();
        case 2: // Schedule
          return _scheduleStep.ValidateInput();
        case 3: // Folder
          return _folderStep.ValidateInput();
        default:
          return true;
      }
    }

    private void CollectSetupData()
    {
      _setupData.Email = _credentialStep.Email;
      _setupData.Password = _credentialStep.Password;
      _setupData.ServerUrl = _credentialStep.ServerUrl;
      _setupData.SelectedRevitVersions = _revitStep.GetSelectedVersions();
      _setupData.PrimaryRevitVersion = _revitStep.PrimaryVersion;
      _setupData.Schedule = _scheduleStep.GetSchedule();
      _setupData.WatchFolder = _folderStep.WatchFolder;
      _setupData.MonitorSubfolders = _folderStep.MonitorSubfolders;
    }

    public SetupData GetSetupData()
    {
      return _setupData;
    }
  }
}


