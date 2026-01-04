# Fix OAuth Token Exchange Issue

## The Problem

The OAuth flow is failing at the token exchange step. The browser shows "Success" but the connector throws:
```
Failed to create account from access code and challenge
```

## Root Cause

Looking at `AccountManager.GetToken()` in `Core/Core/Credentials/AccountManager.cs` (line 748):

```csharp
var response = await client.PostAsync($"{server}/auth/token", content).ConfigureAwait(false);
return JsonConvert.DeserializeObject<TokenExchangeResponse>(
    await response.Content.ReadAsStringAsync().ConfigureAwait(false)
);
```

**The code doesn't check if the HTTP response is successful!** If the server returns an error (400, 401, 500, etc.), it tries to deserialize an error response as `TokenExchangeResponse`, which fails.

## Solution Options

### Option 1: Fix the GetToken Method (Recommended)

Modify `GetToken` to check the response status and show the actual error:

```csharp
private static async Task<TokenExchangeResponse> GetToken(string accessCode, string challenge, string server)
{
    try
    {
        using var client = Http.GetHttpProxyClient();

        var body = new
        {
            appId = "sca",
            appSecret = "sca",
            accessCode,
            challenge
        };

        using var content = new StringContent(JsonConvert.SerializeObject(body));
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var response = await client.PostAsync($"{server}/auth/token", content).ConfigureAwait(false);

        var responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        
        // CHECK RESPONSE STATUS
        if (!response.IsSuccessStatusCode)
        {
            SpeckleLog.Logger.Error(
                "Token exchange failed: HTTP {statusCode} - {responseBody}",
                (int)response.StatusCode,
                responseContent
            );
            throw new SpeckleException(
                $"Token exchange failed: HTTP {(int)response.StatusCode} - {responseContent}"
            );
        }

        return JsonConvert.DeserializeObject<TokenExchangeResponse>(responseContent);
    }
    catch (Exception ex) when (!ex.IsFatal())
    {
        throw new SpeckleException($"Failed to get authentication token from {server}", ex);
    }
}
```

### Option 2: Check Server OAuth Configuration

The AWS server might not have the OAuth app configured with:
- `appId: "sca"`
- `appSecret: "sca"`

These are hardcoded in the connector. The server admin needs to configure an OAuth app with these exact values.

### Option 3: Manual Account Creation (Workaround)

If OAuth continues to fail, you can manually create an account by:
1. Getting a token from the browser (localStorage or Network tab)
2. Using that token to fetch user info
3. Manually saving the account

## Next Steps

1. **First**: Add the error checking to `GetToken` method to see the actual error
2. **Then**: Check if the server has the OAuth app configured
3. **If needed**: Use manual account creation as a workaround


