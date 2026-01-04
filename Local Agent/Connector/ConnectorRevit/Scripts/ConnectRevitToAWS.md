# How to Connect Revit to AWS Server

## Step 1: Add Account in Speckle Manager

1. **Open Speckle Manager** (search in Windows Start menu)
2. Click **"Add Account"** or the **"+"** button
3. Enter:
   - **Server URL**: `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`
   - **Email**: `shinesains@gmail.com`
   - **Password**: `Sidian2025!`
4. Click **"Login"** or **"Add Account"**
5. Verify the account appears in your accounts list

## Step 2: Restart Revit

- **Close Revit completely** (not just the file)
- **Reopen Revit**
- This ensures Revit picks up the new account from Speckle Manager

## Step 3: Verify Connection in Revit

1. Open any Revit file
2. Go to the **"Sidian"** tab in the ribbon
3. Click the **"Sidian"** button (opens the connector panel)
4. The connector should now show:
   - Your AWS server URL
   - Your account (shinesains@gmail.com)
   - Your projects from the AWS server

## Step 4: If Still Not Connected

If you still see `http://127.0.0.1:3000` or `localhost:3000`:

1. **Check the connector panel** - Look for a server selector dropdown
2. **Select your AWS server** from the dropdown if available
3. **Or check the config file** - It should already be updated to AWS:
   - Location: `%APPDATA%\Speckle\RevitAutomatedSend.json`
   - Should show: `"ServerUrl": "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com"`

## Troubleshooting

### "No account found for server"
- Make sure you added the account in **Speckle Manager** (not just logged into web)
- Make sure the server URL matches EXACTLY (including `http://`)

### Still showing localhost
- Restart Revit completely
- Check that the account in Speckle Manager has the AWS URL (not localhost)

### Connector panel not showing
- Make sure the connector is installed: Check `%APPDATA%\Autodesk\Revit\Addins\{Year}\SpeckleRevit2\`
- Restart Revit if you just installed it

## Quick Check Commands

Run this to verify your config:
```powershell
Get-Content "$env:APPDATA\Speckle\RevitAutomatedSend.json" | ConvertFrom-Json | Select-Object ServerUrl
```

Should show: `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`


