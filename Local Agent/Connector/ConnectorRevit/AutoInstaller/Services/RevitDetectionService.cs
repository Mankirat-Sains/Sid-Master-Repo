using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Speckle.AutoInstaller.Models;

namespace Speckle.AutoInstaller.Services
{
  public class RevitDetectionService
  {
    public List<RevitVersionInfo> DetectInstalledVersions()
    {
      var versions = new List<RevitVersionInfo>();

      // Check for Revit 2020-2026
      for (int year = 2020; year <= 2026; year++)
      {
        var versionInfo = CheckRevitVersion(year);
        if (versionInfo != null)
        {
          versions.Add(versionInfo);
        }
      }

      return versions.OrderByDescending(v => v.Year).ToList();
    }

    private RevitVersionInfo CheckRevitVersion(int year)
    {
      var possiblePaths = new[]
      {
        $@"C:\Program Files\Autodesk\Revit {year}\Revit.exe",
        $@"C:\Program Files (x86)\Autodesk\Revit {year}\Revit.exe",
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), $"Autodesk\\Revit {year}\\Revit.exe"),
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), $"Autodesk\\Revit {year}\\Revit.exe")
      };

      foreach (var path in possiblePaths)
      {
        if (File.Exists(path))
        {
          return new RevitVersionInfo
          {
            Year = year,
            Path = path,
            IsInstalled = true,
            IsSelected = false // User will select
          };
        }
      }

      return null;
    }
  }
}

