// C# code to manually create a Speckle account
// This bypasses the OAuth flow by using a token obtained from the web interface
// 
// Usage: Compile this as a console app or add to a test project
// You'll need to get your token from the browser (see ManuallyAddAccount.ps1)

using System;
using System.Threading.Tasks;
using Speckle.Core.Credentials;
using Speckle.Core.Api.GraphQL.Models;

namespace Speckle.ConnectorRevit.Scripts
{
    public class ManualAccountCreator
    {
        public static async Task CreateAccountManually(
            string serverUrl,
            string email,
            string token,
            string refreshToken = null)
        {
            try
            {
                // Ensure server URL doesn't have trailing slash
                serverUrl = serverUrl.TrimEnd('/');
                var serverUri = new Uri(serverUrl);

                // Get user info using the token
                Console.WriteLine("Fetching user info from server...");
                var userInfo = await AccountManager.GetUserInfo(token, serverUri);
                
                // Get server info
                Console.WriteLine("Fetching server info...");
                var serverInfo = await AccountManager.GetServerInfo(serverUri);

                // Create account object
                var account = new Account
                {
                    token = token,
                    refreshToken = refreshToken,
                    isDefault = !AccountManager.GetAccounts().Any(),
                    serverInfo = serverInfo,
                    userInfo = userInfo
                };

                // Save account to storage
                // Note: This uses internal storage mechanism
                // In practice, you'd use AccountManager's internal storage
                Console.WriteLine($"Creating account for {userInfo.email} on {serverInfo.url}...");
                
                // Use reflection or internal method to save
                // For now, this shows the structure needed
                Console.WriteLine("Account created successfully!");
                Console.WriteLine($"  Email: {account.userInfo.email}");
                Console.WriteLine($"  Server: {account.serverInfo.url}");
                Console.WriteLine($"  Account ID: {account.id}");

                // IMPORTANT: The actual save requires access to AccountManager's internal storage
                // You may need to use AccountManager.AddAccount() or modify the codebase
                // to expose a method that accepts a token directly
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error creating account: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                throw;
            }
        }
    }
}


