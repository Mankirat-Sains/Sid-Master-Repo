# Autodesk APS (Forge) Revit → IFC Conversion Pipeline

Complete automated solution for batch converting Revit (RVT) files to IFC format using Supabase Storage and Autodesk Platform Services (APS, formerly Forge) Design Automation API.

## Project Structure

```
readrevit/
├── forge-ifc-exporter/          # APS AppBundle project (C#)
│   ├── src/                     # C# source code
│   ├── bundle/                  # AppBundle package
│   └── README.md                # AppBundle setup instructions
├── supabase_client.py           # Supabase REST API client helper
├── convert_all_rvt.py          # Main automated pipeline script
├── supabase_setup.py            # Setup and verification script
├── run_aps_setup.py             # APS CLI command generator
├── .env                         # Environment variables (you create this)
├── out/                         # Output directory (auto-created)
│   ├── ifc/                     # Converted IFC files
│   └── logs/                    # Pipeline logs and processed files
└── README.md                    # This file
```

## Prerequisites

1. **Python 3.7+** with required packages:
   ```bash
   pip install supabase python-dotenv requests
   ```
   Note: We use REST API directly, but `requests` is required.

2. **Autodesk APS CLI** installed:
   ```bash
   npm install -g @aps/cli
   ```

3. **Supabase Account** with:
   - Project URL
   - Service role key (for storage operations)

4. **APS Account** with:
   - Client ID
   - Client Secret
   - Design Automation API access

5. **.env file** in the root directory:
   ```env
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_SERVICE_KEY=xxxxxx
   client_id=xxxx
   client_secret=xxxx
   ```

## Quick Start

### 1. Install Dependencies

```bash
pip install python-dotenv requests
```

### 2. Setup Environment

Create a `.env` file in the `readrevit` directory:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
client_id=your_aps_client_id
client_secret=your_aps_client_secret
```

### 3. Verify Setup

Run the setup script to verify your configuration:

```bash
python supabase_setup.py
```

This will:
- Verify all environment variables are present
- Check Supabase connection
- Ensure the `rvtfiles` bucket exists (creates it if missing)
- Print signed URL instructions

### 4. Run the Pipeline

Place your `.rvt` files in:
```
/Volumes/J:/Projects/rvtfiles
```

Then run:

```bash
python convert_all_rvt.py
```

## How the Pipeline Works

### Overview

The automated pipeline performs the following steps for each `.rvt` file:

1. **File Discovery**: Scans `/Volumes/J:/Projects/rvtfiles` for all `.rvt` files
2. **Supabase Upload**: Uploads each RVT file to Supabase storage bucket `rvtfiles`
3. **Signed URL Generation**: Creates a signed URL valid for 2 hours (7200 seconds)
4. **APS WorkItem Creation**: Submits a workitem to APS Design Automation API
5. **Status Tracking**: Logs all operations and tracks processed files

### Detailed Flow

```
RVT File → Supabase Upload → Signed URL → APS WorkItem → IFC Output
   ↓              ↓              ↓              ↓              ↓
Local Disk    Storage Bucket   Temporary    APS Processing  OSS Bucket
                              (2hr valid)                  → Download
```

### File Processing

- **Input**: `.rvt` files from `/Volumes/J:/Projects/rvtfiles`
- **Upload Location**: `rvtfiles/{filename}.rvt` in Supabase
- **Output**: IFC files in `out/ifc/{filename}.ifc` (after APS processing)
- **Logs**: Pipeline logs in `out/logs/`

### Skipping Already Processed Files

The pipeline maintains a `processed_files.json` log that tracks:
- Files already submitted to APS
- Processing status (submitted, failed)
- Workitem IDs and timestamps

Files with status `submitted` are automatically skipped.

## Scripts

### `convert_all_rvt.py`

Main pipeline script that:
- Finds all `.rvt` files in the source directory
- Uploads to Supabase with retry logic (max 3 retries)
- Generates signed URLs (2-hour expiration)
- Creates APS workitems via CLI
- Logs all operations
- Handles errors gracefully
- Skips already processed files

**Usage:**
```bash
python convert_all_rvt.py
```

**Features:**
- Automatic directory creation (`out/ifc/`, `out/logs/`)
- Retry logic for uploads and APS submissions
- Progress tracking with timestamps
- Detailed logging to `out/logs/pipeline_YYYYMMDD_HHMMSS.log`
- Processed files tracking in `out/logs/processed_files.json`

### `supabase_setup.py`

Setup and verification script that:
- Verifies all required environment variables
- Tests Supabase connection
- Ensures `rvtfiles` bucket exists
- Creates bucket if missing
- Prints signed URL instructions

**Usage:**
```bash
python supabase_setup.py
```

### `supabase_client.py`

Helper module for Supabase REST API operations:
- `bucket_exists()` - Check if bucket exists
- `create_bucket()` - Create bucket if missing
- `upload_file()` - Upload file to storage
- `create_signed_url()` - Generate signed URL (2-hour expiration)
- `file_exists()` - Check if file exists in bucket

### `run_aps_setup.py`

Generates APS CLI commands (does not execute):
- Authentication command
- AppBundle upload command
- Activity creation command
- WorkItem creation command

**Usage:**
```bash
python run_aps_setup.py
```

## APS Activity Setup

Before running the pipeline, you must:

1. **Build the AppBundle** (see `forge-ifc-exporter/README.md`)
2. **Upload AppBundle**:
   ```bash
   cd forge-ifc-exporter/bundle
   aps appbundle create IFCExportAppBundle \
     --engine Revit \
     --description "Revit to IFC Export" \
     --zip IFCExportAppBundle.zip
   ```

3. **Create Activity**:
   ```bash
   aps activity create IFCExporterActivity \
     --engine Revit \
     --appbundle IFCExportAppBundle \
     --description "Export Revit to IFC"
   ```

**Important**: The activity name must be `IFCExporterActivity` (as configured in `convert_all_rvt.py`).

## Verifying Results

### Check Supabase Uploads

1. **Via Supabase Dashboard**:
   - Go to Storage → `rvtfiles` bucket
   - Verify uploaded `.rvt` files

2. **Via Script**:
   ```python
   from supabase_client import SupabaseClient
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   client = SupabaseClient(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
   exists = client.file_exists('rvtfiles', 'your-file.rvt')
   print(f"File exists: {exists}")
   ```

### Check APS WorkItems

1. **Check WorkItem Status**:
   ```bash
   aps workitem status <workitem-id>
   ```

2. **List Recent WorkItems**:
   ```bash
   aps workitem list
   ```

3. **Download IFC Output**:
   ```bash
   aps workitem output <workitem-id> --output-dir ./out/ifc
   ```

### Check Pipeline Logs

- **Pipeline Log**: `out/logs/pipeline_YYYYMMDD_HHMMSS.log`
- **Processed Files**: `out/logs/processed_files.json`

The processed files JSON contains:
```json
{
  "filename.rvt": {
    "status": "submitted",
    "timestamp": "2025-01-15T10:30:00",
    "details": {
      "object_name": "filename.rvt",
      "workitem_id": "abc123...",
      "output_filename": "filename.ifc"
    }
  }
}
```

## Configuration

### Change Source Directory

Edit `convert_all_rvt.py`:
```python
RVT_SOURCE_DIR = "/your/custom/path"
```

### Change Bucket Name

Edit both `convert_all_rvt.py` and `supabase_setup.py`:
```python
BUCKET_NAME = "your-bucket-name"
```

### Change Activity Name

Edit `convert_all_rvt.py`:
```python
APS_ACTIVITY = "YourActivityName"
```

### Adjust Retry Settings

Edit `convert_all_rvt.py`:
```python
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
```

### Change Signed URL Expiration

Edit `convert_all_rvt.py` in the `create_signed_url()` call:
```python
success, signed_url = create_signed_url(
    supabase_client, 
    BUCKET_NAME, 
    object_name,
    expires_in=3600  # 1 hour instead of 2
)
```

## Error Handling

The pipeline includes comprehensive error handling:

- **File Not Found**: Skips missing files with error message
- **Upload Failures**: Retries up to 3 times with 5-second delays
- **Signed URL Failures**: Retries up to 3 times
- **APS WorkItem Failures**: Retries up to 3 times
- **Network Errors**: Logged and retried
- **Missing Environment Variables**: Exits with clear error message

All errors are logged to both console and log files.

## Troubleshooting

### "Missing environment variables"

- Ensure `.env` file exists in the `readrevit` directory
- Verify all required variables are present
- Run `python supabase_setup.py` to verify

### "Bucket does not exist"

- Run `python supabase_setup.py` to create the bucket
- Or manually create it via Supabase dashboard

### "APS authentication failed"

- Verify `client_id` and `client_secret` in `.env`
- Manually authenticate: `aps auth login --client-id ... --client-secret ...`

### "WorkItem creation failed"

- Verify APS Activity exists: `aps activity list`
- Check activity name matches `IFCExporterActivity`
- Verify signed URL is still valid (2-hour expiration)

### "No .rvt files found"

- Verify source directory path: `/Volumes/J:/Projects/rvtfiles`
- Check directory exists and is accessible
- Ensure files have `.rvt` extension

### "Signed URL expired"

- Signed URLs expire after 2 hours
- Re-run the pipeline to generate new URLs
- Pipeline automatically creates fresh URLs for each run

## Production Considerations

### Path Safety

- All paths use `Path` objects for cross-platform compatibility
- Directory creation is automatic
- File paths are sanitized (forward slashes for Supabase)

### Signed URL Expiration

- URLs are valid for 2 hours (7200 seconds)
- Pipeline creates URLs immediately before use
- If processing takes longer than 2 hours, re-run the pipeline

### Logging

- All operations logged with timestamps
- Separate log file per pipeline run
- Processed files tracked in JSON for resumability

### Resumability

- Pipeline skips already processed files
- Can safely re-run after interruption
- Processed files log persists between runs

## Advanced Usage

### Process Specific Files

Modify `convert_all_rvt.py` to filter files:
```python
# Only process files matching pattern
rvt_files = [f for f in find_rvt_files(RVT_SOURCE_DIR) 
             if 'pattern' in f.name]
```

### Custom Output Naming

Modify output filename generation:
```python
output_filename = f"custom_prefix_{filename.replace('.rvt', '.ifc')}"
```

### Parallel Processing

For large batches, consider processing files in parallel (requires additional implementation).

## References

- [Autodesk APS Design Automation Documentation](https://aps.autodesk.com/en/docs/design-automation/v3)
- [Supabase Storage REST API](https://supabase.com/docs/reference/javascript/storage-from)
- [APS CLI Documentation](https://aps.autodesk.com/en/docs/cli/v1)
- [Revit IFC Export API](https://www.revitapidocs.com/2023/)

## License

Copyright © MantleAI 2025

