# OAuth Connection Fix - Summary

## What Was Wrong

The Revit connector was failing to create accounts with the error:
```
Failed to create account from access code and challenge
```

**Root Cause**: The `GetToken()` method in `AccountManager.cs` was not checking if the HTTP response was successful before trying to deserialize it. When the server returned an error (like 400 Bad Request), it tried to deserialize an error response as a `TokenExchangeResponse`, which caused a cryptic failure.

## What I Fixed

I modified `speckle-sharp/Core/Core/Credentials/AccountManager.cs` (around line 764) to:

1. **Check the HTTP response status** before deserializing
2. **Log the actual error** from the server (status code + response body)
3. **Throw a more descriptive exception** that shows what went wrong

Now when OAuth fails, you'll see the actual error message from your AWS server, which will help diagnose the real issue.

## Next Steps

### 1. Rebuild the Connector

You need to rebuild the Core project and then the Revit connector:

```powershell
# From the workspace root
cd speckle-sharp\Core\Core
dotnet build Core.csproj

# Then rebuild the Revit connector
cd ..\..\ConnectorRevit\ConnectorRevit
dotnet build ConnectorRevit.projitems
```

### 2. Test the OAuth Flow Again

1. Open Revit
2. Go to the Sidian/Speckle connector panel
3. Click "Add Account" or similar
4. Enter your AWS server URL: `http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`
5. Complete the OAuth flow in the browser

### 3. Check the Error Message

If it still fails, you'll now see a detailed error message like:
```
Token exchange failed: HTTP 400. Server response: {"error": "Invalid app credentials"}
```

This will tell you exactly what's wrong.

## Common Issues & Solutions

### Issue: "Invalid app credentials" or "appId/appSecret not found"
**Solution**: Your AWS server needs to have an OAuth app configured with:
- `appId: "sca"`
- `appSecret: "sca"`

These are hardcoded in the connector. The server admin needs to configure this in the server's OAuth settings.

### Issue: "Access code expired" or "Invalid access code"
**Solution**: The OAuth flow might be timing out. Try again, and make sure to complete the browser login quickly.

### Issue: "Server not reachable"
**Solution**: Check that:
- The server URL is correct (no trailing slash)
- The server is accessible from your network
- Firewall isn't blocking the connection

## Alternative: Manual Account Creation

If OAuth continues to fail, you can manually create an account by:

1. Getting your token from the browser (F12 > Application > Local Storage)
2. Using a script to create the account programmatically
3. See `CreateAccountManually.cs` for reference

## Files Modified

- `speckle-sharp/Core/Core/Credentials/AccountManager.cs` - Added error checking to `GetToken()` method

## Testing

After rebuilding, try adding the account again. The error message should now be much more helpful in diagnosing the issue.


