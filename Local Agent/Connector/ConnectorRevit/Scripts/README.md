# Speckle Revit Automated/Batch Send

This folder contains scripts and documentation for automatically sending Revit models to Speckle without manual interaction.

## Overview

The automated send feature allows you to:
- Send Revit models to Speckle automatically when they're opened
- Process entire folders of .rvt files in batch mode
- Configure default stream IDs, accounts, and other settings via a JSON config file

## Prerequisites

1. **Revit** must be installed (2020-2025 supported)
2. **Speckle Revit Connector** must be installed and built
3. **Speckle Account** must be configured in Speckle Manager
4. For local server: **Speckle Server** must be running

## Configuration

### Config File Location

The configuration file is located at:
```
%APPDATA%\Speckle\RevitAutomatedSend.json
```

A sample config file is automatically created when you first load the connector.

### Config File Structure

```json
{
  "ServerUrl": "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com",
  "AccountEmail": "shinesains@gmail.com",
  "DefaultStreamId": "your-stream-id-here",
  "StreamIdMapping": {
    "ProjectA": "stream-id-for-project-a",
    "ProjectB": "stream-id-for-project-b"
  },
  "DefaultFilter": "all",
  "DefaultSettings": {
    "linkedmodels-send": "false"
  },
  "AutoSendOnDocumentOpen": false,
  "BranchName": "main",
  "CommitMessageTemplate": "Automated send: {DocumentName} at {Timestamp}",
  "CloseDocumentAfterSend": true,
  "CloseRevitAfterSend": false,
  "ResultsDirectory": ""
}
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `ServerUrl` | string | Your Speckle server URL (e.g., `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`) |
| `AccountEmail` | string | Email of the account to use. Leave empty for default account. |
| `DefaultStreamId` | string | Default stream ID to send to if no mapping matches |
| `StreamIdMapping` | object | Map Revit project names to specific stream IDs |
| `DefaultFilter` | string | Filter type: `"all"` sends everything |
| `DefaultSettings` | object | Converter settings (key-value pairs) |
| `AutoSendOnDocumentOpen` | bool | Auto-send when a document is opened |
| `BranchName` | string | Branch to commit to (default: `"main"`) |
| `CommitMessageTemplate` | string | Commit message template. Supports `{DocumentName}` and `{Timestamp}` |
| `CloseDocumentAfterSend` | bool | Close document after sending (for batch processing) |
| `CloseRevitAfterSend` | bool | Close Revit after sending (for single-file automation) |
| `ResultsDirectory` | string | Where to write result JSON files. Default: `%TEMP%\SpeckleAutoSend` |

## Usage

### Method 1: Manual Button Click

1. Open Revit
2. Open your .rvt file
3. Go to the **Sidian** tab in the ribbon
4. Click the **Auto Send** button
5. The model will be sent to the configured stream

### Method 2: Auto-Send on Document Open

1. Edit `RevitAutomatedSend.json`
2. Set `"AutoSendOnDocumentOpen": true`
3. Open Revit and open a .rvt file
4. The model will automatically be sent to Speckle

### Method 3: Batch Processing (PowerShell Script)

Use the `BatchSendToSpeckle.ps1` script to process multiple files:

```powershell
# Basic usage - process all .rvt files in a folder
.\BatchSendToSpeckle.ps1 -FolderPath "C:\RevitProjects" -RevitYear 2024

# With specific Revit path
.\BatchSendToSpeckle.ps1 -FolderPath "C:\RevitProjects" -RevitPath "C:\Program Files\Autodesk\Revit 2024\Revit.exe"

# Recursive search in subfolders
.\BatchSendToSpeckle.ps1 -FolderPath "C:\RevitProjects" -RevitYear 2024 -Recursive

# With custom timeout (60 minutes per file)
.\BatchSendToSpeckle.ps1 -FolderPath "C:\RevitProjects" -RevitYear 2024 -TimeoutMinutes 60
```

#### Script Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `-FolderPath` | Yes | - | Path to folder with .rvt files |
| `-RevitPath` | No | Auto-detect | Full path to Revit.exe |
| `-RevitYear` | No | 2024 | Revit version year |
| `-ConfigPath` | No | Auto | Path to config JSON file |
| `-Recursive` | No | false | Search subfolders |
| `-MaxParallel` | No | 1 | Max parallel Revit instances |
| `-TimeoutMinutes` | No | 30 | Timeout per file |
| `-OutputPath` | No | FolderPath | Where to save summary |

## Result Files

After each send operation, a JSON result file is created:

```json
{
  "Success": true,
  "CommitId": "abc123...",
  "StreamId": "stream-id",
  "DocumentName": "MyProject.rvt",
  "DocumentPath": "C:\\Projects\\MyProject.rvt",
  "ErrorMessage": null,
  "Timestamp": "2024-01-15T10:30:00",
  "ObjectCount": 1500,
  "DurationSeconds": 45.5
}
```

Result files are saved to the configured `ResultsDirectory` (or `%TEMP%\SpeckleAutoSend`).

## Setting Up Your Speckle Server and Stream

### 1. Get Your Stream ID

1. Open your Speckle server in a browser (e.g., `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`)
2. Create a new project/stream or open an existing one
3. Copy the stream ID from the URL: `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com/streams/{stream-id}`

### 2. Configure Your Account

1. Open **Speckle Manager**
2. Add your server: click "Add Account" and enter your server URL:
   - **Server URL**: `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`
   - **Email**: `shinesains@gmail.com`
   - **Password**: `Sidian2025!`
3. Log in with your credentials
4. The account will now be available for automated sends

**Note**: Use `http://` (not `https://`) since SSL hasn't been set up yet. This is the same URL you use to access Speckle in your browser.

### 3. Update the Config File

```json
{
  "ServerUrl": "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com",
  "AccountEmail": "shinesains@gmail.com",
  "DefaultStreamId": "paste-your-stream-id-here"
}
```

## Troubleshooting

### "No account found for server"
- Make sure you've added your server account in Speckle Manager
- Check that `ServerUrl` in the config matches exactly (including port)

### "No stream ID configured"
- Add either `DefaultStreamId` or a mapping in `StreamIdMapping`

### "Zero objects to send"
- The model may be empty or unsupported
- Check that the filter is set to `"all"` or a valid filter type

### Revit doesn't close after send
- The auto-close feature requires `CloseDocumentAfterSend: true`
- Some operations may prevent automatic closing

### Timeout during batch processing
- Increase `-TimeoutMinutes` for large files
- Large models may take 30+ minutes to convert and send

## Advanced: Stream ID Mapping

You can map specific Revit project names to different streams:

```json
{
  "StreamIdMapping": {
    "Building_A": "stream-id-1",
    "Building_B": "stream-id-2",
    "Site_Model": "stream-id-3"
  },
  "DefaultStreamId": "fallback-stream-id"
}
```

The matching is done by the Revit document title (without `.rvt` extension).

## Security Notes

- The config file stores no passwords or tokens
- Authentication uses the accounts configured in Speckle Manager
- Result files may contain project names and paths - handle accordingly

## Support

For issues or feature requests, please visit:
- [Speckle Community Forum](https://speckle.community/)
- [Speckle GitHub](https://github.com/specklesystems)




