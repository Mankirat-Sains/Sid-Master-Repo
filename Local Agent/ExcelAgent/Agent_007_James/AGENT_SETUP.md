# Local Excel Sync Agent - Setup Guide

## Overview

This agent runs on your local machine or shared drive server to sync Excel calculation data with the cloud platform in real-time.

## Requirements

- Python 3.8 or higher
- Access to Excel files on local/shared drive
- Network connectivity to the platform API

## Installation

### 1. Install Python Dependencies

```bash
pip install openpyxl requests watchdog
```

### 2. Configure the Agent

Create a `config.json` file based on `config.example.json`:

```json
{
  "platform_url": "https://your-platform.com",
  "api_key": "your-api-key-here",
  "poll_interval": 30,
  "auto_sync_on_change": false,
  "projects": [
    {
      "project_id": "metro-line-5",
      "project_name": "Metro Line 5 Extension",
      "excel_file": "C:/SharedDrive/Projects/MetroLine5/Structural_Calcs.xlsx",
      "sheet_name": "INFO",
      "cell_mappings": {
        "ground_snow_load": "B6",
        "wind_load": "B8",
        "roof_pitch": "B9"
      }
    }
  ]
}
```

### Configuration Options

| Field | Description |
|-------|-------------|
| `platform_url` | Base URL of your platform API |
| `api_key` | Authentication key provided by platform |
| `poll_interval` | How often (seconds) to check for sync requests |
| `auto_sync_on_change` | Whether to auto-sync when Excel files change |
| `projects` | Array of project configurations |

### Project Configuration

Each project needs:
- `project_id`: Unique identifier matching platform
- `excel_file`: Full path to Excel file
- `sheet_name`: Name of sheet to read (e.g., "INFO")
- `cell_mappings`: Map field names to Excel cell references

## Usage

### Mode 1: Polling Mode (Recommended)

Agent checks for sync requests from platform every N seconds:

```bash
python local_sync_agent.py --config config.json --mode polling
```

### Mode 2: Watch Mode

Agent monitors Excel files for changes and optionally auto-syncs:

```bash
python local_sync_agent.py --config config.json --mode watch
```

### Mode 3: Manual Sync

Sync once and exit (useful for testing):

```bash
python local_sync_agent.py --config config.json --sync-now
```

## Running as a Service

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At system startup
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `C:\path\to\local_sync_agent.py --config C:\path\to\config.json --mode polling`

### Linux/Mac (systemd)

Create `/etc/systemd/system/excel-sync-agent.service`:

```ini
[Unit]
Description=Excel Sync Agent
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/agent
ExecStart=/usr/bin/python3 local_sync_agent.py --config config.json --mode polling
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable excel-sync-agent
sudo systemctl start excel-sync-agent
```

## Logs

All activity is logged to `sync_agent.log` in the same directory.

## Security Notes

- Keep `config.json` secure (contains API key)
- Use HTTPS for platform communication
- Agent only reads specified cells (no full file access)
- All communication is authenticated via API key

## Troubleshooting

### "Sheet not found" Error
- Verify sheet name matches exactly (case-sensitive)
- Check that Excel file is not corrupted

### Network Errors
- Verify `platform_url` is correct
- Check firewall settings
- Ensure API key is valid

### File Access Errors
- Ensure Excel file is not open/locked
- Check file path is correct
- Verify read permissions

## Support

For issues or questions, contact your platform administrator.
