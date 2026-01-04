using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Speckle.AutoInstaller.Models;

namespace Speckle.AutoInstaller.Services
{
  public class InstallerService
  {
    public void InstallConnectorForVersions(List<RevitVersionInfo> versions)
    {
      foreach (var version in versions.Where(v => v.IsSelected && v.IsInstalled))
      {
        try
        {
          InstallConnectorForVersion(version);
        }
        catch (Exception ex)
        {
          // Log error but continue with other versions
          System.Diagnostics.Debug.WriteLine($"Failed to install for Revit {version.Year}: {ex.Message}");
        }
      }
    }

    private void InstallConnectorForVersion(RevitVersionInfo version)
    {
      // 1. Create add-in folder structure
      var addinFolder = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Autodesk",
        "Revit",
        "Addins",
        version.Year.ToString()
      );

      var connectorFolder = Path.Combine(addinFolder, "SpeckleRevit2");
      Directory.CreateDirectory(connectorFolder);

      // 2. Extract embedded DLLs to connector folder
      // Note: In a real implementation, you would embed the DLLs as resources
      // For now, we'll create a placeholder that indicates where files should be copied
      ExtractEmbeddedResources(connectorFolder, version.Year);

      // 2b. Extract converter DLLs to Kits folder (required for connector to work)
      ExtractConverterDlls(version.Year);

      // 3. Create/update .addin file
      CreateAddinManifest(addinFolder, version.Year, connectorFolder);

      // 4. Verify installation
      VerifyInstallation(version);
    }

    private void ExtractEmbeddedResources(string targetFolder, int revitYear)
    {
      var assembly = Assembly.GetExecutingAssembly();
      var resourcePrefix = $"Speckle.AutoInstaller.Resources.Revit{revitYear}.";
      
      // Get all embedded resources for this Revit version
      var resourceNames = assembly.GetManifestResourceNames()
        .Where(name => name.StartsWith(resourcePrefix, StringComparison.OrdinalIgnoreCase))
        .ToList();

      if (resourceNames.Count == 0)
      {
        // No embedded resources found - this is expected if DLLs haven't been embedded yet
        // Create a marker file to indicate installation attempt
        var markerFile = Path.Combine(targetFolder, "Installed.txt");
        File.WriteAllText(markerFile, $"Installation attempted for Revit {revitYear} at {DateTime.Now}\n" +
                                      "Note: DLLs not yet embedded. Please embed connector DLLs as resources.");
        System.Diagnostics.Debug.WriteLine($"Warning: No embedded resources found for Revit {revitYear}. " +
                                          "DLLs need to be embedded in the project.");
        return;
      }

      // Ensure target directory exists
      if (!Directory.Exists(targetFolder))
      {
        Directory.CreateDirectory(targetFolder);
      }

      foreach (var resourceName in resourceNames)
      {
        try
        {
          // Extract resource name (e.g., "Speckle.AutoInstaller.Resources.Revit2024.SpeckleConnectorRevit.dll")
          // to just the filename
          var fileName = resourceName.Substring(resourcePrefix.Length);
          
          // Handle nested paths if any (replace dots with path separators if needed)
          // For now, assume flat structure in Resources folder
          var targetPath = Path.Combine(targetFolder, fileName);
          var targetDir = Path.GetDirectoryName(targetPath);
          
          if (!string.IsNullOrEmpty(targetDir) && !Directory.Exists(targetDir))
          {
            Directory.CreateDirectory(targetDir);
          }

          // Extract the resource
          using (var resourceStream = assembly.GetManifestResourceStream(resourceName))
          {
            if (resourceStream == null)
            {
              System.Diagnostics.Debug.WriteLine($"Warning: Failed to load embedded resource: {resourceName}");
              continue;
            }

            using (var fileStream = new FileStream(targetPath, FileMode.Create))
            {
              resourceStream.CopyTo(fileStream);
            }
            
            System.Diagnostics.Debug.WriteLine($"Extracted: {fileName} to {targetPath}");
          }
        }
        catch (Exception ex)
        {
          System.Diagnostics.Debug.WriteLine($"Error extracting resource {resourceName}: {ex.Message}");
          // Continue with other resources
        }
      }
    }

    private void CreateAddinManifest(string addinFolder, int year, string connectorPath)
    {
      var addinPath = Path.Combine(addinFolder, "SpeckleRevit2.addin");
      var dllPath = Path.Combine(connectorPath, "SpeckleConnectorRevit.dll");
      
      // Use relative path from addin folder (Path.GetRelativePath not available in .NET Framework 4.8)
      var relativeDllPath = dllPath.Replace(addinFolder, "").TrimStart('\\', '/').Replace('\\', '/');
      
      var manifest = $@"<?xml version=""1.0"" encoding=""utf-8""?>
<RevitAddIns>
  <AddIn Type=""Application"">
    <Name>Sidian for Revit</Name>
    <Description>Sidian Connector for Revit</Description>
    <Assembly>{relativeDllPath}</Assembly>
    <FullClassName>Speckle.ConnectorRevit.Entry.App</FullClassName>
    <ClientId>5AE0BD71-CDE6-40DC-8A9B-AB227DE75A52</ClientId>
    <VendorId>speckle</VendorId>
    <VendorDescription>Sidian: Empowering your design and construction data.</VendorDescription>
  </AddIn>
</RevitAddIns>";

      File.WriteAllText(addinPath, manifest);
    }

    private void ExtractConverterDlls(int revitYear)
    {
      var assembly = Assembly.GetExecutingAssembly();
      var resourcePrefix = $"Speckle.AutoInstaller.Resources.Revit{revitYear}.";
      
      // Create Kits folder structure
      var kitsFolder = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Speckle",
        "Kits",
        "Objects"
      );
      
      Directory.CreateDirectory(kitsFolder);
      
      // 1. Extract Objects.dll (main kit DLL - required for KitManager.GetDefaultKit())
      var objectsDllName = "Objects.dll";
      var objectsResourceName = $"{resourcePrefix}{objectsDllName}";
      
      var objectsResource = assembly.GetManifestResourceNames()
        .FirstOrDefault(name => name.Equals(objectsResourceName, StringComparison.OrdinalIgnoreCase));
      
      if (objectsResource != null)
      {
        var objectsTargetPath = Path.Combine(kitsFolder, objectsDllName);
        try
        {
          using (var resourceStream = assembly.GetManifestResourceStream(objectsResource))
          {
            if (resourceStream != null)
            {
              using (var fileStream = new FileStream(objectsTargetPath, FileMode.Create))
              {
                resourceStream.CopyTo(fileStream);
              }
              System.Diagnostics.Debug.WriteLine($"Extracted: {objectsDllName} to {objectsTargetPath}");
            }
          }
        }
        catch (Exception ex)
        {
          System.Diagnostics.Debug.WriteLine($"Error extracting {objectsDllName}: {ex.Message}");
          // Continue - don't fail installation if Objects.dll extraction fails
        }
      }
      else
      {
        System.Diagnostics.Debug.WriteLine($"Warning: Objects.dll not found in embedded resources for Revit {revitYear}");
      }
      
      // 2. Extract converter DLL for this Revit version
      var converterDllName = $"Objects.Converter.Revit{revitYear}.dll";
      var converterResourceName = $"{resourcePrefix}{converterDllName}";
      
      var converterResource = assembly.GetManifestResourceNames()
        .FirstOrDefault(name => name.Equals(converterResourceName, StringComparison.OrdinalIgnoreCase));
      
      if (converterResource != null)
      {
        var converterTargetPath = Path.Combine(kitsFolder, converterDllName);
        try
        {
          using (var resourceStream = assembly.GetManifestResourceStream(converterResource))
          {
            if (resourceStream != null)
            {
              using (var fileStream = new FileStream(converterTargetPath, FileMode.Create))
              {
                resourceStream.CopyTo(fileStream);
              }
              System.Diagnostics.Debug.WriteLine($"Extracted converter: {converterDllName} to {converterTargetPath}");
            }
          }
        }
        catch (Exception ex)
        {
          System.Diagnostics.Debug.WriteLine($"Error extracting converter DLL {converterDllName}: {ex.Message}");
          // Don't throw - continue with installation even if converter extraction fails
        }
      }
      else
      {
        System.Diagnostics.Debug.WriteLine($"Warning: Converter DLL not found in embedded resources: {converterDllName}");
      }
    }

    private void VerifyInstallation(RevitVersionInfo version)
    {
      var addinFolder = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Autodesk",
        "Revit",
        "Addins",
        version.Year.ToString()
      );

      var addinFile = Path.Combine(addinFolder, "SpeckleRevit2.addin");
      if (!File.Exists(addinFile))
      {
        throw new Exception($"Failed to create .addin file for Revit {version.Year}");
      }
    }
  }
}

