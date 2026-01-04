# Next Steps - AutoInstaller Setup

## ✅ What's Been Completed

1. **UI Updated** - Credential panel now clarifies that a browser will open for OAuth login
2. **ExtractEmbeddedResources Method** - Fully implemented to extract DLLs from embedded resources
3. **Project File Updated** - Configured to embed DLLs from `Resources/Revit{Year}/` folders
4. **DLL Setup Guide Created** - Complete instructions in `DLL_SETUP_GUIDE.md`

## 📋 What You Need To Do Now

### Step 1: Build Connector Projects (30-60 minutes)

Build each Revit connector project you want to support:

```bash
# Navigate to connector directory
cd speckle-sharp/ConnectorRevit

# Build each version (choose Release or Debug)
dotnet build ConnectorRevit2020/ConnectorRevit2020.csproj -c Release
dotnet build ConnectorRevit2021/ConnectorRevit2021.csproj -c Release
dotnet build ConnectorRevit2022/ConnectorRevit2022.csproj -c Release
dotnet build ConnectorRevit2023/ConnectorRevit2023.csproj -c Release
dotnet build ConnectorRevit2024/ConnectorRevit2024.csproj -c Release
dotnet build ConnectorRevit2025/ConnectorRevit2025.csproj -c Release
```

Or use Visual Studio:
- Open `ConnectorRevit.sln`
- Build Solution (or build each project individually)
- Make sure to build in **Release** configuration

### Step 2: Create Resources Folder Structure (5 minutes)

Create these folders in the AutoInstaller project:

```
speckle-sharp/ConnectorRevit/AutoInstaller/
  Resources/
    Revit2020/
    Revit2021/
    Revit2022/
    Revit2023/
    Revit2024/
    Revit2025/
```

### Step 3: Copy DLLs to Resources Folders (15-30 minutes)

For each Revit version you built:

1. **Find the built DLLs:**
   - Location: `ConnectorRevit{Year}/bin/Release/` (or Debug)
   - Main file: `SpeckleConnectorRevit.dll`

2. **Copy all DLLs:**
   - Copy `SpeckleConnectorRevit.dll`
   - Copy ALL dependency DLLs from the same folder
   - Include DLLs from: Core, DesktopUI2, Objects, RevitSharedResources, etc.

3. **Paste into Resources folder:**
   - Paste all DLLs into `AutoInstaller/Resources/Revit{Year}/`

**Important:** Copy ALL DLLs that are in the build output folder. The connector needs all its dependencies.

### Step 4: Build AutoInstaller (5 minutes)

```bash
cd speckle-sharp/ConnectorRevit/AutoInstaller
dotnet build AutoInstaller.csproj -c Release
```

Or in Visual Studio:
- Right-click `AutoInstaller.csproj` → Build
- Check for any errors

### Step 5: Test Installation (15 minutes)

1. **Run the installer:**
   - Navigate to `bin/Release/` (or Debug)
   - Run `SpeckleAutoInstaller.exe`

2. **Complete the wizard:**
   - Step 1: Enter email (shinesains@gmail.com) - browser will open for password
   - Step 2: Select Revit versions to install
   - Step 3: Choose schedule
   - Step 4: Select folder

3. **Verify installation:**
   - Check `%APPDATA%\Autodesk\Revit\Addins\{Year}\SpeckleRevit2\` for DLLs
   - Check `%APPDATA%\Autodesk\Revit\Addins\{Year}\SpeckleRevit2.addin` exists

4. **Test in Revit:**
   - Open Revit
   - Check if "Sidian" tab appears in ribbon
   - Verify connector loads without errors

## 🔍 Troubleshooting

### "No embedded resources found" Warning
- **Cause:** DLLs not copied to Resources folders yet
- **Fix:** Complete Steps 2-3 above

### DLLs Not Extracting During Installation
- **Cause:** Resource names don't match expected pattern
- **Fix:** Check that DLLs are in `Resources/Revit{Year}/` (not subfolders)
- **Verify:** Build project, then check embedded resources in EXE using ILSpy

### Missing Dependency DLLs
- **Cause:** Not all DLLs copied from build output
- **Fix:** Copy ALL DLLs from the connector build output folder

### Connector Doesn't Load in Revit
- **Cause:** Missing dependencies or wrong paths
- **Fix:** 
  - Check `.addin` file paths are correct
  - Verify all DLLs are in the connector folder
  - Check Revit journal for errors

## 📝 Quick Checklist

- [ ] Built connector projects (all versions you need)
- [ ] Created `Resources/Revit{Year}/` folders
- [ ] Copied `SpeckleConnectorRevit.dll` for each version
- [ ] Copied ALL dependency DLLs for each version
- [ ] Built AutoInstaller project
- [ ] Tested installation on clean system
- [ ] Verified connector loads in Revit

## 🎯 Current Status

**Code is ready!** You just need to:
1. Build the connector DLLs
2. Copy them to Resources folders
3. Build and test

The extraction code will automatically handle the rest when DLLs are embedded.

## 📚 Additional Resources

- See `DLL_SETUP_GUIDE.md` for detailed instructions
- See `README.md` for general information
- See `IMPLEMENTATION_NOTES.md` for technical details


