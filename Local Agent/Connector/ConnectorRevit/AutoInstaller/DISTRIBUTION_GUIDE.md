# Distribution Guide

## What to Distribute

**Yes, you only need to distribute the `bin\Release\net48\` folder contents.**

### Required Files

Copy **all files** from this folder:
```
bin\Release\net48\
```

### Essential Files (Minimum)

At minimum, you need:
- ✅ `SpeckleAutoInstaller.exe` - The main executable
- ✅ `SpeckleAutoInstaller.exe.config` - Configuration file (required!)
- ✅ All `.dll` files - Runtime dependencies

### What's Included

The folder contains:
- **SpeckleAutoInstaller.exe** (~249 MB) - Main executable with embedded connector DLLs
- **SpeckleAutoInstaller.exe.config** - Assembly binding redirects (critical!)
- **Runtime DLLs** - .NET Framework dependencies (Core, GraphQL, Serilog, etc.)

### Distribution Methods

#### Option 1: Zip the Entire Folder
1. Zip the entire `bin\Release\net48\` folder
2. Send the ZIP file to clients
3. They extract and run `SpeckleAutoInstaller.exe`

#### Option 2: Copy Folder Contents
1. Copy all files from `bin\Release\net48\` to a USB drive or network share
2. Clients copy to their computer
3. They run `SpeckleAutoInstaller.exe`

#### Option 3: Create Installer (Future Enhancement)
- Package everything into a single installer (e.g., InnoSetup, NSIS)
- Clients run installer, everything gets set up automatically

### Important Notes

⚠️ **The `.exe.config` file is REQUIRED** - Without it, the application may fail to load dependencies correctly.

⚠️ **All DLLs must be in the same folder** as the EXE - Don't separate them.

✅ **The connector DLLs are embedded** - They're inside the EXE, so you don't need to distribute separate connector DLLs.

### Quick Distribution Checklist

- [ ] Copy entire `bin\Release\net48\` folder
- [ ] Verify `SpeckleAutoInstaller.exe` is included
- [ ] Verify `SpeckleAutoInstaller.exe.config` is included
- [ ] Verify all `.dll` files are included
- [ ] Test on a clean machine (without .NET development tools)
- [ ] Zip and distribute

### Testing Before Distribution

1. Copy the `bin\Release\net48\` folder to a test location
2. Run `SpeckleAutoInstaller.exe` from that location
3. Verify the setup wizard works
4. Complete the installation
5. Verify connectors install correctly

### File Size

Total distribution size: ~**250-260 MB** (includes all embedded connector DLLs for Revit 2020-2026)

