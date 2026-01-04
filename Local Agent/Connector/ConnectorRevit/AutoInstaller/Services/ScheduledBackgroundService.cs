using System;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Timers;
using System.Windows.Forms;
using Speckle.AutoInstaller.Helpers;
using Speckle.AutoInstaller.Models;
using Speckle.AutoInstaller.Storage;

namespace Speckle.AutoInstaller.Services
{
  public class ScheduledBackgroundService
  {
    private ScheduleConfiguration _schedule;
    private BackgroundWatcherService _watcher;
    private System.Timers.Timer _scheduleTimer;
    private System.Timers.Timer _warningTimer;
    private string _watchFolder;
    private AutomatedSendConfig _config;
    private bool _isRunning;

    public void Start(ScheduleConfiguration schedule, string watchFolder, AutomatedSendConfig config)
    {
      _schedule = schedule;
      _watchFolder = watchFolder;
      _config = config;
      _isRunning = true;

      // Ensure watch folder exists
      if (!Directory.Exists(_watchFolder))
      {
        Directory.CreateDirectory(_watchFolder);
      }

      if (schedule.Type == ScheduleType.RunNow || schedule.StartImmediately)
      {
        // Only start immediately if explicitly "Run Now"
        Log("Starting immediately (Run Now selected)");
        StartWatcher();
      }
      else
      {
        // Schedule for later - calculate next run time and wait
        Log($"Scheduling for later (Type: {schedule.Type})");
        ScheduleNextRun();
      }
    }

    public void Stop()
    {
      _isRunning = false;
      _scheduleTimer?.Stop();
      _scheduleTimer?.Dispose();
      _warningTimer?.Stop();
      _warningTimer?.Dispose();
      _watcher?.Stop();
    }

    private void ScheduleNextRun()
    {
      var now = DateTime.Now;
      var nextRun = CalculateNextRunTime(_schedule);
      _schedule.NextRunTime = nextRun;

      var delay = nextRun - now;
      if (delay.TotalMilliseconds < 0)
      {
        // Time has passed, run immediately
        StartWatcher();
        return;
      }

      // 15-minute pre-run warning popup
      try
      {
        // Only show warning if the run is at least 15 minutes away
        var warningOffset = TimeSpan.FromMinutes(15);
        if (delay > warningOffset)
        {
          var warningDelay = delay - warningOffset;
          _warningTimer?.Stop();
          _warningTimer?.Dispose();

          _warningTimer = new System.Timers.Timer(warningDelay.TotalMilliseconds);
          _warningTimer.AutoReset = false;
          _warningTimer.Elapsed += (s, e) =>
          {
              try
              {
                // Log warning instead of showing popup during automation
                Log("15-minute pre-run warning: Automation will run in 15 minutes.");
              }
              catch
              {
                // Swallow any exceptions
              }
          };
          _warningTimer.Start();
        }
      }
      catch
      {
        // Do not let warning issues affect scheduling
      }

      _scheduleTimer = new System.Timers.Timer(delay.TotalMilliseconds);
      _scheduleTimer.Elapsed += (s, e) => OnScheduledRun();
      _scheduleTimer.AutoReset = false;
      _scheduleTimer.Start();

      Log($"Next run scheduled for: {nextRun} (in {delay.TotalMinutes:F1} minutes)");
      
      // Show 15-minute warning if next run is more than 15 minutes away
      if (delay.TotalMinutes > 15)
      {
        var warningDelay = delay.TotalMinutes - 15;
        var warningTimer = new System.Timers.Timer(warningDelay * 60 * 1000);
        warningTimer.Elapsed += (s, e) =>
        {
          Log("15-minute pre-run warning: Automation will run in 15 minutes.");
          warningTimer.Stop();
          warningTimer.Dispose();
        };
        warningTimer.AutoReset = false;
        warningTimer.Start();
        Log($"15-minute warning scheduled for: {nextRun.AddMinutes(-15):yyyy-MM-dd HH:mm:ss}");
      }
    }

    private DateTime CalculateNextRunTime(ScheduleConfiguration schedule)
    {
      var now = DateTime.Now;

      switch (schedule.Type)
      {
        case ScheduleType.RunAtMidnight:
          var midnight = now.Date.AddDays(1); // Tomorrow midnight
          return midnight;

        case ScheduleType.RunOnWeekends:
          // Find next Saturday or Sunday
          var nextWeekend = FindNextWeekendDay(now);
          return nextWeekend.Date.Add(schedule.Time ?? TimeSpan.Zero);

        case ScheduleType.RunDaily:
          var todayAtTime = now.Date.Add(schedule.Time ?? TimeSpan.Zero);
          if (todayAtTime > now)
            return todayAtTime;
          else
            return todayAtTime.AddDays(1);

        case ScheduleType.RunWeekly:
          // Find next occurrence of selected days
          return FindNextWeeklyRun(now, schedule.DaysOfWeek, schedule.Time);

        case ScheduleType.RunCustom:
          return now.AddHours(schedule.IntervalHours ?? 24);

        default:
          return now;
      }
    }

    private DateTime FindNextWeekendDay(DateTime from)
    {
      var day = from;
      while (day.DayOfWeek != DayOfWeek.Saturday && day.DayOfWeek != DayOfWeek.Sunday)
      {
        day = day.AddDays(1);
      }
      return day;
    }

    private DateTime FindNextWeeklyRun(DateTime from, DayOfWeek[] daysOfWeek, TimeSpan? time)
    {
      if (daysOfWeek == null || daysOfWeek.Length == 0)
        return from;

      var targetTime = time ?? TimeSpan.Zero;
      var day = from;

      // Check today first
      if (daysOfWeek.Contains(day.DayOfWeek))
      {
        var todayAtTime = day.Date.Add(targetTime);
        if (todayAtTime > from)
          return todayAtTime;
      }

      // Find next matching day
      for (int i = 0; i < 7; i++)
      {
        day = day.AddDays(1);
        if (daysOfWeek.Contains(day.DayOfWeek))
        {
          return day.Date.Add(targetTime);
        }
      }

      return from; // Fallback
    }

    private void OnScheduledRun()
    {
      if (!_isRunning)
        return;

      // Start the watcher for this run period
      StartWatcher();

      // Schedule next run based on configuration
      if (_schedule.Type == ScheduleType.RunOnWeekends)
      {
        // For weekends, we might want to run continuously until end of weekend
        // Then schedule next weekend
        ScheduleNextRun();
      }
      else if (_schedule.Type == ScheduleType.RunDaily)
      {
        // Schedule next day
        ScheduleNextRun();
      }
      else if (_schedule.Type == ScheduleType.RunCustom)
      {
        // Schedule next interval
        ScheduleNextRun();
      }
      // RunNow doesn't need rescheduling
    }

    private void StartWatcher()
    {
      if (_watcher != null && _watcher.IsRunning)
        return;

      _watcher = new BackgroundWatcherService();
      _watcher.Start(_watchFolder, _config);

      Log("Background watcher started");
    }

    private void Log(string message)
    {
      LogHelper.Log($"[ScheduledService] {message}");
    }
  }
}

