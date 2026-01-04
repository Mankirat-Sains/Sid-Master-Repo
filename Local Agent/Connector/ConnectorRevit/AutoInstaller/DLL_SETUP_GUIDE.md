# DLL Setup Guide for AutoInstaller

This guide explains how to prepare and embed the connector DLLs into the AutoInstaller executable.

## Step 1: Build Connector Projects

Build each Revit connector project for the versions you want to support:

### Build Commands (Visual Studio)
1. Open `speckle-sharp/ConnectorRevit/ConnectorRevit.sln`
2. Build each project:
   - `ConnectorRevit2020`
   - `ConnectorRevit2021`
   - `ConnectorRevit2022`
   - `ConnectorRevit2023`
   - `ConnectorRevit2024`
   - `ConnectorRevit2025`

### Build Commands (Command Line)
```bash
cd speckle-sharp/ConnectorRevit
dotnet build ConnectorRevit2020/ConnectorRevit2020.csproj -c Release
dotnet build ConnectorRevit2021/ConnectorRevit2021.csproj -c Release
dotnet build ConnectorRevit2022/ConnectorRevit2022.csproj -c Release
dotnet build ConnectorRevit2023/ConnectorRevit2023.csproj -c Release
dotnet build ConnectorRevit2024/ConnectorRevit2024.csproj -c Release
dotnet build ConnectorRevit2025/ConnectorRevit2025.csproj -c Release
```

## Step 2: Locate Built DLLs

After building, find the output DLLs. They're typically in:
- `speckle-sharp/ConnectorRevit/ConnectorRevit{Year}/bin/Release/` or
- `speckle-sharp/ConnectorRevit/ConnectorRevit{Year}/bin/Debug/`

For each version, you need:
- `SpeckleConnectorRevit.dll` (main connector)
- All dependency DLLs (from Core, DesktopUI2, Objects, etc.)

## Step 3: Create Resources Folder Structure

Create this folder structure in the AutoInstaller project:

```
speckle-sharp/ConnectorRevit/AutoInstaller/
  Resources/
    Revit2020/
      SpeckleConnectorRevit.dll
      [all dependency DLLs]
    Revit2021/
      SpeckleConnectorRevit.dll
      [all dependency DLLs]
    Revit2022/
      SpeckleConnectorRevit.dll
      [all dependency DLLs]
    Revit2023/
      SpeckleConnectorRevit.dll
      [all dependency DLLs]
    Revit2024/
      SpeckleConnectorRevit.dll
      [all dependency DLLs]
    Revit2025/
      SpeckleConnectorRevit.dll
      [all dependency DLLs]
```

## Step 4: Copy DLLs to Resources Folders

For each Revit version:

1. Copy `SpeckleConnectorRevit.dll` from the build output
2. Copy all dependency DLLs from the build output
3. Paste them into `AutoInstaller/Resources/Revit{Year}/`

### Finding Dependencies

The connector depends on DLLs from:
- `speckle-sharp/Core/Core/bin/Release/`
- `speckle-sharp/DesktopUI2/DesktopUI2/bin/Release/`
- `speckle-sharp/Objects/Objects/bin/Release/`
- `speckle-sharp/ConnectorRevit/RevitSharedResources{Year}/bin/Release/`

Copy all DLLs that are referenced by the connector.

## Step 5: Update Project File

The `AutoInstaller.csproj` file needs to be updated to embed these DLLs. Add this to the project file:

```xml
<ItemGroup>
  <!-- Embed DLLs for each Revit version -->
  <EmbeddedResource Include="Resources\Revit2020\**\*.dll">
    <Link>Resources\Revit2020\%(RecursiveDir)%(Filename)%(Extension)</Link>
  </EmbeddedResource>
  <EmbeddedResource Include="Resources\Revit2021\**\*.dll">
    <Link>Resources\Revit2021\%(RecursiveDir)%(Filename)%(Extension)</Link>
  </EmbeddedResource>
  <EmbeddedResource Include="Resources\Revit2022\**\*.dll">
    <Link>Resources\Revit2022\%(RecursiveDir)%(Filename)%(Extension)</Link>
  </EmbeddedResource>
  <EmbeddedResource Include="Resources\Revit2023\**\*.dll">
    <Link>Resources\Revit2023\%(RecursiveDir)%(Filename)%(Extension)</Link>
  </EmbeddedResource>
  <EmbeddedResource Include="Resources\Revit2024\**\*.dll">
    <Link>Resources\Revit2024\%(RecursiveDir)%(Filename)%(Extension)</Link>
  </EmbeddedResource>
  <EmbeddedResource Include="Resources\Revit2025\**\*.dll">
    <Link>Resources\Revit2025\%(RecursiveDir)%(Filename)%(Extension)</Link>
  </EmbeddedResource>
</ItemGroup>
```

## Step 6: Verify Resource Names

After building, you can verify the embedded resources are correct by:

1. Building the AutoInstaller project
2. Using a tool like `ILSpy` or `dotPeek` to inspect the EXE
3. Check that resources are named: `Speckle.AutoInstaller.Resources.Revit{Year}.{FileName}.dll`

## Troubleshooting

### DLLs Not Found During Extraction
- Check that DLLs are in `Resources/Revit{Year}/` folders
- Verify project file includes `<EmbeddedResource>` entries
- Check that DLLs are marked as "Embedded Resource" in Visual Studio (not "Content")

### Wrong Resource Names
- Resource names follow pattern: `{Namespace}.Resources.Revit{Year}.{FileName}`
- Namespace is `Speckle.AutoInstaller` (from RootNamespace in csproj)
- File names should match exactly

### Missing Dependencies
- Make sure all dependency DLLs are copied
- Check build output for all referenced assemblies
- Some dependencies might be in subfolders - copy them maintaining structure

## Quick Checklist

- [ ] Built all connector projects (2020-2025)
- [ ] Created `Resources/Revit{Year}/` folders
- [ ] Copied `SpeckleConnectorRevit.dll` for each version
- [ ] Copied all dependency DLLs for each version
- [ ] Updated `AutoInstaller.csproj` with `<EmbeddedResource>` entries
- [ ] Built AutoInstaller project
- [ ] Verified resources are embedded (check EXE with ILSpy)
- [ ] Tested installation on clean system

## Notes

- You only need to include DLLs for Revit versions you want to support
- If a user doesn't have a particular Revit version installed, those DLLs won't be extracted
- The installer will only install connectors for Revit versions that are detected on the system


