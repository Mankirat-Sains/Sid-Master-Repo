# Implementation Notes

## What Has Been Created

### ✅ Complete Project Structure
- **AutoInstaller.csproj** - Windows Forms application project
- **Program.cs** - Main entry point with setup wizard flow
- **Models/** - Data models for configuration
- **Services/** - Core business logic services
- **UI/** - Windows Forms user interface components

### ✅ Core Components

1. **Setup Wizard (UI/SetupWizard.cs)**
   - Multi-step wizard interface
   - Navigation between steps
   - Data collection and validation

2. **Credential Panel (UI/CredentialPanel.cs)**
   - Email and password input
   - Server URL (pre-filled with AWS server)
   - Input validation

3. **Revit Selection Panel (UI/RevitSelectionPanel.cs)**
   - Automatic detection of installed Revit versions
   - Checkbox selection for multiple versions
   - Primary version selection dropdown
   - Select All/Deselect All buttons

4. **Schedule Panel (UI/SchedulePanel.cs)**
   - Run Now option
   - Run at Midnight (daily)
   - Run on Weekends
   - Run Daily at specific time
   - Run Weekly on specific days
   - Custom interval (hours)

5. **Folder Selection Panel (UI/FolderSelectionPanel.cs)**
   - Folder browser dialog
   - Subfolder monitoring option
   - Default folder suggestion

6. **Installer Service (Services/InstallerService.cs)**
   - Detects Revit installations
   - Creates add-in folder structure
   - Installs .addin manifest files
   - Extracts connector DLLs (placeholder for embedded resources)

7. **Account Setup Service (Services/AccountSetupService.cs)**
   - Creates Speckle accounts via OAuth flow
   - Handles authentication
   - Saves account to Speckle Manager

8. **Revit Detection Service (Services/RevitDetectionService.cs)**
   - Scans for Revit 2020-2025 installations
   - Returns version information

9. **Scheduled Background Service (Services/ScheduledBackgroundService.cs)**
   - Implements scheduling logic
   - Calculates next run times
   - Manages background watcher lifecycle

10. **Background Watcher Service (Services/BackgroundWatcherService.cs)**
    - FileSystemWatcher for folder monitoring
    - Queue system for file processing
    - Launches Revit and processes files

## What Still Needs to Be Done

### ⚠️ Embedded Resources (Critical)

The connector DLLs need to be embedded as resources in the EXE:

1. **Add DLLs as Embedded Resources**
   - For each Revit version (2020-2025), embed:
     - `SpeckleConnectorRevit.dll`
     - All dependency DLLs
   - Structure in project:
     ```
     Resources/
       Revit2020/
         SpeckleConnectorRevit.dll
         [dependencies...]
       Revit2021/
         ...
     ```

2. **Update InstallerService.cs**
   - Implement `ExtractEmbeddedResources()` method
   - Extract DLLs from embedded resources based on Revit version
   - Copy to appropriate add-in folder

3. **Project File Updates**
   - Add `<EmbeddedResource>` items for all DLLs
   - Organize by Revit version

### ⚠️ Integration with HeadlessSendService

Currently, the BackgroundWatcherService launches Revit and relies on auto-send. For better control:

1. **Option A**: Use HeadlessSendService directly (if possible without full Revit UI)
2. **Option B**: Monitor result files from HeadlessSendService
3. **Option C**: Use Revit API to trigger send command programmatically

### ⚠️ Error Handling & Logging

- Add more comprehensive error handling
- Improve logging throughout
- Add user notifications for errors
- Add retry logic for failed sends

### ⚠️ Testing

- Test on systems with multiple Revit versions
- Test all schedule types
- Test file processing with various file sizes
- Test error scenarios

### ⚠️ Build Configuration

- Set up build to create single EXE
- Configure embedded resources
- Add icon file
- Set up versioning

## Usage Flow

1. **User downloads EXE**
2. **First run**: Setup wizard appears
   - Step 1: Enter credentials
   - Step 2: Select Revit versions
   - Step 3: Choose schedule
   - Step 4: Select folder
3. **Installation happens**:
   - Connector DLLs extracted and installed
   - Account created in Speckle Manager
   - Configuration files created
4. **Background service starts**:
   - Monitors folder based on schedule
   - Processes files automatically
5. **Subsequent runs**: Service starts automatically (no wizard)

## Configuration Files

- `%APPDATA%\Speckle\RevitAutomatedSend.json` - Main config
- `%APPDATA%\Speckle\ScheduleConfig.json` - Schedule config
- `%APPDATA%\Speckle\AutoInstaller.configured` - Setup flag
- `%APPDATA%\Speckle\AutoInstaller.log` - Log file

## Next Steps

1. **Embed DLLs**: Add connector DLLs as embedded resources
2. **Test Installation**: Test on clean system
3. **Improve File Processing**: Better integration with HeadlessSendService
4. **Add Error Recovery**: Retry logic and better error handling
5. **Create Installer**: Optional MSI installer for easier distribution


