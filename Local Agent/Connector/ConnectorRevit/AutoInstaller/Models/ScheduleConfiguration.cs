using System;

namespace Speckle.AutoInstaller.Models
{
  public enum ScheduleType
  {
    RunNow,           // Start immediately
    RunAtMidnight,    // Daily at 12:00 AM
    RunOnWeekends,    // Saturday and Sunday
    RunDaily,         // Every day at specified time
    RunWeekly,        // Specific days of week
    RunCustom         // Custom interval
  }

  public class ScheduleConfiguration
  {
    public ScheduleType Type { get; set; }
    public bool StartImmediately { get; set; }
    public TimeSpan? Time { get; set; }
    public DayOfWeek[] DaysOfWeek { get; set; }
    public int? IntervalHours { get; set; }
    public DateTime? NextRunTime { get; set; }
  }
}


