# Revit 2026 Support - Setup Complete

## Summary

Revit 2026 support has been fully integrated into the Speckle connector system. All necessary components have been created and configured.

## What Was Added

### 1. Core Components
- ✅ **ConnectorRevit2026** - Main connector project for Revit 2026
- ✅ **RevitSharedResources2026** - Shared resources project
- ✅ **ConverterRevit2026** - Converter project for Revit 2026

### 2. Updated Files
- ✅ `Core/Core/Kits/Applications.cs` - Added `v2026` and `vRevit2026` to enum
- ✅ `ConnectorRevit/Entry/App.cs` - Added REVIT2026 version detection
- ✅ `ConnectorRevit/ConnectorRevitUtils.cs` - Added REVIT2026 app name mapping
- ✅ `ConnectorRevit.sln` - Added all new projects with proper configurations

### 3. AutoInstaller Updates
- ✅ `RevitDetectionService.cs` - Now detects Revit 2026 (2020-2026 range)
- ✅ `BackgroundWatcherService.cs` - Updated to handle Revit 2026
- ✅ `README.md` - Updated documentation

### 4. Templates
- ✅ Created `Templates/2026` folder (copied from 2025 templates)

## Project Structure

```
ConnectorRevit/
├── ConnectorRevit2026/
│   ├── ConnectorRevit2026.csproj
│   └── Properties/
│       └── launchSettings.json
├── RevitSharedResources2026/
│   └── RevitSharedResources2026.csproj
└── ...

Objects/Converters/ConverterRevit/
├── ConverterRevit2026/
│   └── ConverterRevit2026.csproj
└── Templates/
    └── 2026/ (6 template files)
```

## Dependencies

All projects reference:
- `Speckle.Revit.API` version **2026.0.0**
- Core, Objects, DesktopUI2 projects
- RevitSharedResources2026

## Building

### Build Individual Projects
```bash
# Build connector
dotnet build ConnectorRevit/ConnectorRevit2026/ConnectorRevit2026.csproj -c Release

# Build converter
dotnet build Objects/Converters/ConverterRevit/ConverterRevit2026/ConverterRevit2026.csproj -c Release

# Build shared resources
dotnet build ConnectorRevit/RevitSharedResources2026/RevitSharedResources2026.csproj -c Release
```

### Build Entire Solution
```bash
dotnet build ConnectorRevit/ConnectorRevit.sln -c Release
```

## Installation

### Manual Installation
1. Build the `ConnectorRevit2026` project in Release mode
2. Copy output from `bin/Release/win-x64/` to:
   ```
   %APPDATA%\Autodesk\Revit\Addins\2026\SpeckleRevit2\
   ```
3. Copy the `.addin` file to:
   ```
   %APPDATA%\Autodesk\Revit\Addins\2026\
   ```

### Using AutoInstaller
The AutoInstaller will automatically:
1. Detect Revit 2026 installation
2. Allow user to select it for installation
3. Extract and install connector DLLs
4. Create the `.addin` manifest file

## Testing Checklist

- [ ] Build all projects successfully
- [ ] Verify connector loads in Revit 2026
- [ ] Test send operation
- [ ] Test receive operation
- [ ] Verify AutoInstaller detects Revit 2026
- [ ] Test AutoInstaller installation for Revit 2026
- [ ] Verify templates are copied correctly

## Notes

- The connector follows the same architecture as Revit 2025
- All conditional compilation uses `#if REVIT2026` directives
- The converter is loaded dynamically via KitManager (no direct project reference needed)
- Templates are automatically copied to user's AppData on first use

## Next Steps

1. **Build and Test**: Build all projects and test in Revit 2026
2. **Update AutoInstaller Resources**: Embed Revit 2026 DLLs in AutoInstaller (see `CopyDLLsToResources.ps1`)
3. **Distribution**: Update distribution package to include Revit 2026 connector
4. **Documentation**: Update any client-facing documentation

## References

- New repo structure: `speckle-connectors-2026/speckle-sharp-connectors`
- Follows same pattern as Revit 2025 implementation
- Maintains compatibility with original repo architecture


