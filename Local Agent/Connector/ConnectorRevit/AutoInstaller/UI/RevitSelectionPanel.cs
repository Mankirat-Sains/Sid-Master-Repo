using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;
using Speckle.AutoInstaller.Models;
using Speckle.AutoInstaller.Services;

namespace Speckle.AutoInstaller.UI
{
  public partial class RevitSelectionPanel : UserControl
  {
    private CheckedListBox _versionList;
    private ComboBox _primaryVersionCombo;
    private Button _btnSelectAll;
    private Button _btnDeselectAll;
    private Label _lblTitle;
    private Label _lblPrimary;
    private List<RevitVersionInfo> _detectedVersions;

    public RevitSelectionPanel()
    {
      InitializeComponent();
      DetectVersions();
    }

    private void InitializeComponent()
    {
      this.Size = new System.Drawing.Size(580, 400);
      this.Dock = DockStyle.Fill;

      _lblTitle = new Label
      {
        Text = "Select Revit versions to install connector",
        Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Bold),
        Location = new System.Drawing.Point(20, 20),
        Size = new System.Drawing.Size(500, 30)
      };

      _versionList = new CheckedListBox
      {
        Location = new System.Drawing.Point(20, 60),
        Size = new System.Drawing.Size(500, 200),
        CheckOnClick = true
      };

      _btnSelectAll = new Button
      {
        Text = "Select All",
        Location = new System.Drawing.Point(20, 270),
        Size = new System.Drawing.Size(100, 30)
      };
      _btnSelectAll.Click += (s, e) =>
      {
        for (int i = 0; i < _versionList.Items.Count; i++)
        {
          _versionList.SetItemChecked(i, true);
        }
      };

      _btnDeselectAll = new Button
      {
        Text = "Deselect All",
        Location = new System.Drawing.Point(130, 270),
        Size = new System.Drawing.Size(100, 30)
      };
      _btnDeselectAll.Click += (s, e) =>
      {
        for (int i = 0; i < _versionList.Items.Count; i++)
        {
          _versionList.SetItemChecked(i, false);
        }
      };

      _lblPrimary = new Label
      {
        Text = "Primary version for processing:",
        Location = new System.Drawing.Point(20, 320),
        Size = new System.Drawing.Size(200, 20)
      };

      _primaryVersionCombo = new ComboBox
      {
        Location = new System.Drawing.Point(230, 318),
        Size = new System.Drawing.Size(200, 21),
        DropDownStyle = ComboBoxStyle.DropDownList
      };

      this.Controls.Add(_lblTitle);
      this.Controls.Add(_versionList);
      this.Controls.Add(_btnSelectAll);
      this.Controls.Add(_btnDeselectAll);
      this.Controls.Add(_lblPrimary);
      this.Controls.Add(_primaryVersionCombo);
    }

    private void DetectVersions()
    {
      var detector = new RevitDetectionService();
      _detectedVersions = detector.DetectInstalledVersions();

      _versionList.Items.Clear();
      _primaryVersionCombo.Items.Clear();

      foreach (var version in _detectedVersions)
      {
        var displayText = $"Revit {version.Year} (Installed)";
        _versionList.Items.Add(displayText, version.IsSelected);
        _primaryVersionCombo.Items.Add(version.Year);
      }

      // Select first version by default if any are found
      if (_detectedVersions.Count > 0)
      {
        _versionList.SetItemChecked(0, true);
        _primaryVersionCombo.SelectedIndex = 0;
      }
    }

    public List<RevitVersionInfo> GetSelectedVersions()
    {
      var selected = new List<RevitVersionInfo>();
      for (int i = 0; i < _versionList.Items.Count; i++)
      {
        if (_versionList.GetItemChecked(i))
        {
          _detectedVersions[i].IsSelected = true;
          selected.Add(_detectedVersions[i]);
        }
      }
      return selected;
    }

    public int? PrimaryVersion
    {
      get
      {
        if (_primaryVersionCombo.SelectedItem != null)
        {
          return (int)_primaryVersionCombo.SelectedItem;
        }
        return null;
      }
    }

    public bool ValidateInput()
    {
      var selected = GetSelectedVersions();
      if (selected.Count == 0)
      {
        MessageBox.Show("Please select at least one Revit version.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        return false;
      }

      if (_primaryVersionCombo.SelectedItem == null)
      {
        MessageBox.Show("Please select a primary Revit version.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        return false;
      }

      return true;
    }
  }
}


