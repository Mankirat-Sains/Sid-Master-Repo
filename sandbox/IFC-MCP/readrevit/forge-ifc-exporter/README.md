# Autodesk APS (Forge) Revit → IFC Converter

This project provides an automated solution for converting Revit (RVT) files to IFC format using Autodesk Platform Services (APS, formerly Forge) Design Automation API.

## Project Structure

```
forge-ifc-exporter/
├── src/                    # C# source code
│   ├── IFCExport.csproj   # Visual Studio project file
│   ├── RevitCommand.cs    # Main automation logic
│   └── Properties/        # Assembly info
├── bundle/                # AppBundle package
│   ├── packageContents.xml # Revit add-in manifest
│   └── IFCExport.dll      # (Compiled DLL - you build this)
└── README.md              # This file
```

## Prerequisites

1. **Visual Studio 2019 or later** with .NET Framework 4.8 support
2. **Revit 2023** installed (for RevitAPI.dll references)
3. **Autodesk APS CLI** installed:
   ```bash
   npm install -g @aps/cli
   ```
4. **Python 3.x** with `python-dotenv`:
   ```bash
   pip install python-dotenv
   ```
5. **APS Account** with Design Automation API access
6. **.env file** in the root directory with:
   ```
   client_id=your_client_id
   client_secret=your_client_secret
   ```

## Step-by-Step Setup

### 1. Build the DLL in Visual Studio

1. Open Visual Studio
2. Open the project: `File → Open → Project/Solution` → Navigate to `src/IFCExport.csproj`
3. Verify project references:
   - The project references RevitAPI.dll, RevitAPIUI.dll, and DesignAutomationFramework.dll
   - These should point to your Revit 2023 installation path
   - If Revit is installed in a different location, update the HintPath in `IFCExport.csproj`
4. Build the project:
   - Select `Release` configuration
   - Right-click project → `Build` (or press `Ctrl+Shift+B`)
5. Locate the compiled DLL:
   - Output location: `src/bin/Release/IFCExport.dll`

### 2. Prepare the AppBundle

1. Copy the compiled DLL to the bundle folder:
   ```bash
   cp src/bin/Release/IFCExport.dll forge-ifc-exporter/bundle/
   ```
2. Ensure `packageContents.xml` is in the bundle folder
3. Create a ZIP file of the bundle contents:
   ```bash
   cd forge-ifc-exporter/bundle
   zip -r IFCExportAppBundle.zip IFCExport.dll packageContents.xml
   ```
   **Important:** Zip the contents (DLL + XML), not the folder itself!

### 3. Authenticate with APS

Run the setup script to see your authentication command:
```bash
python run_aps_setup.py
```

Or authenticate directly:
```bash
aps auth login --client-id <your_client_id> --client-secret <your_client_secret>
```

### 4. Upload AppBundle

```bash
cd forge-ifc-exporter/bundle
aps appbundle create IFCExportAppBundle \
  --engine Revit \
  --description "Revit to IFC Export Automation" \
  --zip IFCExportAppBundle.zip
```

**Note:** AppBundle names must be unique. If you need to update, use:
```bash
aps appbundle update IFCExportAppBundle --zip IFCExportAppBundle.zip
```

### 5. Create Activity

```bash
aps activity create IFCExportActivity \
  --engine Revit \
  --appbundle IFCExportAppBundle \
  --description "Export Revit files to IFC format"
```

### 6. Run WorkItem

#### Step 6a: Upload RVT File to OSS

First, create an OSS bucket (if you don't have one):
```bash
aps oss create-bucket <bucket-key> --policy transient
```

Upload your Revit file:
```bash
aps oss upload <bucket-key> <path-to-your-file.rvt>
```

#### Step 6b: Create and Run WorkItem

```bash
aps workitem create IFCExportActivity \
  --input-rvt <oss-object-name> \
  --output-ifc output.ifc
```

The workitem will return a workitem ID. Save this ID for status checking.

#### Step 6c: Monitor WorkItem Status

```bash
aps workitem status <workitem-id>
```

Status values:
- `pending` - WorkItem is queued
- `inprogress` - WorkItem is being processed
- `success` - WorkItem completed successfully
- `failed` - WorkItem failed (check reportUrl for details)

#### Step 6d: Download Results

Once status is `success`, download the IFC file:
```bash
aps workitem output <workitem-id> --output-dir ./output
```

The IFC file will be saved as `output.ifc` in the specified output directory.

## Where the IFC File Ends Up

1. **During Processing:** The IFC file is created in the same directory as the input RVT file in the APS processing environment
2. **After Completion:** The IFC file is uploaded to your OSS bucket as `output.ifc`
3. **After Download:** The IFC file is saved to your local `./output` directory (or wherever you specify with `--output-dir`)

## Troubleshooting

### DLL Build Issues

- **Missing RevitAPI.dll:** Ensure Revit 2023 is installed and update the HintPath in `IFCExport.csproj`
- **.NET Framework 4.8 not found:** Install .NET Framework 4.8 Developer Pack
- **DesignAutomationFramework not found:** This DLL is included with Revit 2023

### AppBundle Upload Issues

- **Invalid ZIP format:** Ensure you zip the contents (DLL + XML), not the folder
- **AppBundle name conflict:** Use a unique name or update existing AppBundle

### WorkItem Issues

- **Authentication errors:** Re-authenticate with `aps auth login`
- **File not found:** Verify OSS object name matches uploaded file
- **Processing fails:** Check workitem reportUrl for detailed error messages

### IFC Export Issues

- **Empty IFC file:** Check Revit file is valid and contains geometry
- **Export options:** Modify `IFCExportOptions` in `RevitCommand.cs` for custom settings

## Advanced Configuration

### Custom IFC Export Options

Edit `src/RevitCommand.cs` to customize export settings:

```csharp
IFCExportOptions options = new IFCExportOptions();
options.FileVersion = IFCVersion.IFC4;
options.SpaceBoundaryLevel = 2;
options.ExportBaseQuantities = true;
// Add more options as needed
```

### Multiple Output Formats

To export multiple formats, modify the `Run` method to export additional file types.

## References

- [Autodesk APS Design Automation Documentation](https://aps.autodesk.com/en/docs/design-automation/v3)
- [Revit IFC Export API](https://www.revitapidocs.com/2023/)
- [APS CLI Documentation](https://aps.autodesk.com/en/docs/cli/v1)

## License

Copyright © MantleAI 2025

