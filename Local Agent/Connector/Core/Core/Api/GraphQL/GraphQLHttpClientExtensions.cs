using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using GraphQL;
using GraphQL.Client.Http;
using Speckle.Core.Api.GraphQL.Models;
using Speckle.Core.Api.GraphQL.Models.Responses;
using Speckle.Core.Logging;

namespace Speckle.Core.Api.GraphQL;

public static class GraphQLHttpClientExtensions
{
  /// <summary>
  /// Gets the version of the current server. Useful for guarding against unsupported api calls on newer or older servers.
  /// </summary>
  /// <param name="cancellationToken">[Optional] defaults to an empty cancellation token</param>
  /// <returns><see cref="Version"/> object excluding any strings (eg "2.7.2-alpha.6995" becomes "2.7.2.6995")</returns>
  /// <exception cref="SpeckleGraphQLException{ServerInfoResponse}"></exception>
  public static async Task<System.Version> GetServerVersion(
    this GraphQLHttpClient client,
    CancellationToken cancellationToken = default
  )
  {
    var request = new GraphQLRequest
    {
      Query =
        @"query Server {
                    serverInfo {
                        version
                      }
                  }"
    };

    var response = await client.SendQueryAsync<ServerInfoResponse>(request, cancellationToken).ConfigureAwait(false);

    if (response.Errors != null)
    {
      throw new SpeckleGraphQLException<ServerInfoResponse>(
        $"Query {nameof(GetServerVersion)} failed",
        request,
        response
      );
    }

    if (string.IsNullOrWhiteSpace(response.Data.serverInfo.version))
    {
      throw new SpeckleGraphQLException<ServerInfoResponse>(
        $"Query {nameof(GetServerVersion)} did not provide a valid server version",
        request,
        response
      );
    }

    if (response.Data.serverInfo.version == "dev")
    {
      return new System.Version(999, 999, 999);
    }

    string versionString = response.Data.serverInfo.version.Split('-').First().Trim();

    // Try to parse the version
    if (System.Version.TryParse(versionString, out System.Version? parsedVersion))
    {
      return parsedVersion;
    }

    // If parsing fails, default to a safe older version (< 2.18.5)
    // This ensures we use the compatible query format without migration field
    // Log a warning so the issue is known
    SpeckleLog.Logger.Warning(
      "Unable to parse server version '{VersionString}' from server, defaulting to version 2.0.0 for compatibility. Server returned: '{FullVersion}'",
      versionString,
      response.Data.serverInfo.version
    );

    return new System.Version(2, 0, 0); // Safe default: < 2.18.5
  }
}
