using System;
using System.Linq;
using System.Windows.Forms;
using Speckle.AutoInstaller.Models;

namespace Speckle.AutoInstaller.UI
{
  public partial class SchedulePanel : UserControl
  {
    private RadioButton _rbRunNow;
    private RadioButton _rbMidnight;
    private RadioButton _rbWeekends;
    private RadioButton _rbDaily;
    private RadioButton _rbWeekly;
    private RadioButton _rbCustom;
    private DateTimePicker _timePicker;
    private CheckedListBox _daysOfWeek;
    private NumericUpDown _intervalHours;
    private Label _lblTitle;

    public SchedulePanel()
    {
      InitializeComponent();
    }

    private void InitializeComponent()
    {
      this.Size = new System.Drawing.Size(580, 400);
      this.Dock = DockStyle.Fill;

      _lblTitle = new Label
      {
        Text = "When should files be processed?",
        Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Bold),
        Location = new System.Drawing.Point(20, 20),
        Size = new System.Drawing.Size(500, 30)
      };

      _rbRunNow = new RadioButton
      {
        Text = "Run Now (start immediately)",
        Location = new System.Drawing.Point(20, 60),
        Size = new System.Drawing.Size(300, 20),
        Checked = true
      };
      _rbRunNow.CheckedChanged += (s, e) => UpdateControls();

      _rbMidnight = new RadioButton
      {
        Text = "Run at Midnight (daily)",
        Location = new System.Drawing.Point(20, 90),
        Size = new System.Drawing.Size(300, 20)
      };
      _rbMidnight.CheckedChanged += (s, e) => UpdateControls();

      _rbWeekends = new RadioButton
      {
        Text = "Run on Weekends (Saturday/Sunday)",
        Location = new System.Drawing.Point(20, 120),
        Size = new System.Drawing.Size(300, 20)
      };
      _rbWeekends.CheckedChanged += (s, e) => UpdateControls();

      _rbDaily = new RadioButton
      {
        Text = "Run Daily at:",
        Location = new System.Drawing.Point(20, 150),
        Size = new System.Drawing.Size(150, 20)
      };
      _rbDaily.CheckedChanged += (s, e) => UpdateControls();

      _timePicker = new DateTimePicker
      {
        Location = new System.Drawing.Point(180, 148),
        Size = new System.Drawing.Size(100, 20),
        Format = DateTimePickerFormat.Time,
        ShowUpDown = true,
        Value = DateTime.Today.AddHours(0).AddMinutes(0)
      };

      _rbWeekly = new RadioButton
      {
        Text = "Run Weekly on:",
        Location = new System.Drawing.Point(20, 180),
        Size = new System.Drawing.Size(150, 20)
      };
      _rbWeekly.CheckedChanged += (s, e) => UpdateControls();

      _daysOfWeek = new CheckedListBox
      {
        Location = new System.Drawing.Point(180, 180),
        Size = new System.Drawing.Size(300, 80)
      };
      _daysOfWeek.Items.Add("Monday", false);
      _daysOfWeek.Items.Add("Tuesday", false);
      _daysOfWeek.Items.Add("Wednesday", false);
      _daysOfWeek.Items.Add("Thursday", false);
      _daysOfWeek.Items.Add("Friday", false);
      _daysOfWeek.Items.Add("Saturday", false);
      _daysOfWeek.Items.Add("Sunday", false);

      _rbCustom = new RadioButton
      {
        Text = "Custom: Every",
        Location = new System.Drawing.Point(20, 270),
        Size = new System.Drawing.Size(150, 20)
      };
      _rbCustom.CheckedChanged += (s, e) => UpdateControls();

      _intervalHours = new NumericUpDown
      {
        Location = new System.Drawing.Point(180, 268),
        Size = new System.Drawing.Size(60, 20),
        Minimum = 1,
        Maximum = 168, // 1 week
        Value = 24
      };

      var lblHours = new Label
      {
        Text = "hours",
        Location = new System.Drawing.Point(250, 270),
        Size = new System.Drawing.Size(50, 20)
      };

      this.Controls.Add(_lblTitle);
      this.Controls.Add(_rbRunNow);
      this.Controls.Add(_rbMidnight);
      this.Controls.Add(_rbWeekends);
      this.Controls.Add(_rbDaily);
      this.Controls.Add(_timePicker);
      this.Controls.Add(_rbWeekly);
      this.Controls.Add(_daysOfWeek);
      this.Controls.Add(_rbCustom);
      this.Controls.Add(_intervalHours);
      this.Controls.Add(lblHours);

      UpdateControls();
    }

    private void UpdateControls()
    {
      _timePicker.Enabled = _rbDaily.Checked;
      _daysOfWeek.Enabled = _rbWeekly.Checked;
      _intervalHours.Enabled = _rbCustom.Checked;
    }

    public ScheduleConfiguration GetSchedule()
    {
      if (_rbRunNow.Checked)
        return new ScheduleConfiguration
        {
          Type = ScheduleType.RunNow,
          StartImmediately = true
        };

      if (_rbMidnight.Checked)
        return new ScheduleConfiguration
        {
          Type = ScheduleType.RunAtMidnight,
          Time = new TimeSpan(0, 0, 0) // Midnight
        };

      if (_rbWeekends.Checked)
        return new ScheduleConfiguration
        {
          Type = ScheduleType.RunOnWeekends,
          DaysOfWeek = new[] { DayOfWeek.Saturday, DayOfWeek.Sunday }
        };

      if (_rbDaily.Checked)
        return new ScheduleConfiguration
        {
          Type = ScheduleType.RunDaily,
          Time = _timePicker.Value.TimeOfDay
        };

      if (_rbWeekly.Checked)
      {
        var selectedDays = new System.Collections.Generic.List<DayOfWeek>();
        var dayNames = new[] { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" };
        var dayValues = new[] { DayOfWeek.Monday, DayOfWeek.Tuesday, DayOfWeek.Wednesday, DayOfWeek.Thursday, DayOfWeek.Friday, DayOfWeek.Saturday, DayOfWeek.Sunday };

        for (int i = 0; i < _daysOfWeek.Items.Count; i++)
        {
          if (_daysOfWeek.GetItemChecked(i))
          {
            selectedDays.Add(dayValues[i]);
          }
        }

        return new ScheduleConfiguration
        {
          Type = ScheduleType.RunWeekly,
          DaysOfWeek = selectedDays.ToArray(),
          Time = _timePicker.Value.TimeOfDay
        };
      }

      if (_rbCustom.Checked)
        return new ScheduleConfiguration
        {
          Type = ScheduleType.RunCustom,
          IntervalHours = (int)_intervalHours.Value
        };

      return new ScheduleConfiguration { Type = ScheduleType.RunNow, StartImmediately = true };
    }

    public bool ValidateInput()
    {
      if (_rbWeekly.Checked)
      {
        bool anySelected = false;
        for (int i = 0; i < _daysOfWeek.Items.Count; i++)
        {
          if (_daysOfWeek.GetItemChecked(i))
          {
            anySelected = true;
            break;
          }
        }

        if (!anySelected)
        {
          MessageBox.Show("Please select at least one day of the week.", "Validation Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
          return false;
        }
      }

      return true;
    }
  }
}


