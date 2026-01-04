# How to Connect to AWS Server

## The Problem
Speckle Manager desktop app is NOT installed, so clicking "Manager" opens the web download page.

## Solution Options

### Option 1: Add Account Directly in Connector UI (EASIEST)

In the Revit connector panel:
1. Click the **dropdown** (where you see account names)
2. Look for **"Add another account"** option
3. Click it
4. Enter:
   - **Server URL**: `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`
   - **Email**: `shinesains@gmail.com`
   - **Password**: `Sidian2025!`
5. Click **Login/Add**

This should add the account directly without needing Speckle Manager!

### Option 2: Install Speckle Manager (If Option 1 doesn't work)

1. Go to: https://speckle.systems/download
2. Download **"Manager for Speckle"** (desktop app)
3. Install it
4. Open it
5. Add your AWS account
6. Restart Revit

### Option 3: Switch Account in Connector UI

If the account already exists but is on localhost:
1. In the connector dropdown, click on **"Mankirat Singh Sains"**
2. Look for options to:
   - **Switch account**
   - **Change server**
   - **Remove account** (then add new one)

## Quick Test

Try Option 1 first - look for "Add another account" in the dropdown menu in Revit connector panel.


