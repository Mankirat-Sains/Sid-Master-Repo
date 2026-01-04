using System;
using System.Linq;
using System.Threading.Tasks;
using Speckle.Core.Credentials;
using Speckle.Core.Logging;

namespace Speckle.AutoInstaller.Services
{
  public class AccountSetupService
  {
    public async Task<Account> CreateAccountAsync(string serverUrl, string email, string password)
    {
      try
      {
        // Check if account already exists
        var existingAccounts = AccountManager.GetAccounts(serverUrl);
        foreach (var account in existingAccounts)
        {
          if (account.userInfo?.email?.Equals(email, StringComparison.OrdinalIgnoreCase) == true)
          {
            return account;
          }
        }

        // Use OAuth flow to create account
        // This will open a browser for the user to authenticate
        await AccountManager.AddAccount(serverUrl).ConfigureAwait(false);

        // Get the newly created account
        var accounts = AccountManager.GetAccounts(serverUrl);
        var newAccount = accounts.FirstOrDefault(
          a => a.userInfo?.email?.Equals(email, StringComparison.OrdinalIgnoreCase) == true
        );

        if (newAccount == null && accounts.Any())
        {
          // If email doesn't match but account was created, return the first one
          newAccount = accounts.First();
        }

        return newAccount;
      }
      catch (Exception ex)
      {
        System.Diagnostics.Debug.WriteLine($"Failed to create account: {ex.Message}");
        throw;
      }
    }

    // Alternative method if you have a token directly
    public Account CreateAccountFromToken(string serverUrl, string email, string token)
    {
      try
      {
        // This would require creating an Account object directly
        // Note: This is a simplified version - you'd need to get user info from the server
        // For now, we'll use the OAuth flow method above
        
        throw new NotImplementedException("Direct token creation not yet implemented. Use OAuth flow.");
      }
      catch (Exception ex)
      {
        System.Diagnostics.Debug.WriteLine($"Failed to create account from token: {ex.Message}");
        throw;
      }
    }
  }
}

