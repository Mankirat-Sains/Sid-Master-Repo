using System.Collections.Generic;
using Speckle.AutoInstaller.Models;

namespace Speckle.AutoInstaller.Models
{
  public class SetupData
  {
    public string Email { get; set; }
    public string Password { get; set; }
    public string ServerUrl { get; set; }
    public string WatchFolder { get; set; }
    public bool MonitorSubfolders { get; set; }
    public List<RevitVersionInfo> SelectedRevitVersions { get; set; } = new List<RevitVersionInfo>();
    public int? PrimaryRevitVersion { get; set; }
    public ScheduleConfiguration Schedule { get; set; }
  }

  public class RevitVersionInfo
  {
    public int Year { get; set; }  // 2020, 2021, 2022, etc.
    public string Path { get; set; }  // Path to Revit.exe
    public bool IsInstalled { get; set; }
    public bool IsSelected { get; set; }
  }
}


