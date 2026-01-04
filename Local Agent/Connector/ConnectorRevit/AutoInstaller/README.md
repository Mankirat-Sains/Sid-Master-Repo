# Speckle Auto-Installer

A self-contained Windows application that automatically installs the Speckle Revit connector and sets up automated file processing.

## Features

- **One-Time Setup Wizard**: Multi-step setup process for easy configuration
- **Revit Version Detection**: Automatically detects installed Revit versions (2020-2026)
- **Selective Installation**: Choose which Revit versions to install the connector for
- **Flexible Scheduling**: Multiple scheduling options:
  - Run immediately
  - Run at midnight (daily)
  - Run on weekends
  - Run daily at specific time
  - Run weekly on specific days
  - Custom interval
- **Background Processing**: Monitors folders and automatically sends Revit files to Speckle
- **Zero User Setup**: After initial wizard, runs completely in the background

## Usage

1. **First Run**: Double-click `SpeckleAutoInstaller.exe`
2. **Step 1 - Credentials**: Enter your Speckle email and password
3. **Step 2 - Revit Selection**: Select which Revit versions to install connector for
4. **Step 3 - Schedule**: Choose when files should be processed
5. **Step 4 - Folder**: Select the folder to monitor for Revit files
6. **Finish**: Setup completes and background service starts

## Configuration

Configuration files are stored in:
- `%APPDATA%\Speckle\RevitAutomatedSend.json` - Main configuration
- `%APPDATA%\Speckle\ScheduleConfig.json` - Schedule configuration
- `%APPDATA%\Speckle\AutoInstaller.log` - Log file

## Building

The project requires:
- .NET Framework 4.8
- Windows Forms
- References to Speckle Core and ConnectorRevit projects

To build:
```bash
dotnet build AutoInstaller.csproj
```

## Notes

- The installer extracts connector DLLs from embedded resources
- Connector is installed to `%APPDATA%\Autodesk\Revit\Addins\{Year}\SpeckleRevit2\`
- The background service runs continuously based on the schedule
- Files are processed automatically when detected in the monitored folder

