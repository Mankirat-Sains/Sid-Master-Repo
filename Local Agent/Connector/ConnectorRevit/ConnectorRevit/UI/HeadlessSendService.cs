#nullable enable
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using DesktopUI2.Models;
using DesktopUI2.Models.Filters;
using DesktopUI2.Models.Settings;
using DesktopUI2.ViewModels;
using RevitSharedResources.Interfaces;
using RevitSharedResources.Models;
using RevitSharedResources.Extensions.SpeckleExtensions;
using ConnectorRevit.Storage;
using Speckle.ConnectorRevit.Storage;
using Speckle.Core.Api;
using Speckle.Core.Api.GraphQL.Enums;
using Speckle.Core.Api.GraphQL.Inputs;
using Speckle.Core.Credentials;
using Speckle.Core.Kits;
using Speckle.Core.Logging;
using Speckle.Core.Models;
using Speckle.Core.Transports;

namespace Speckle.ConnectorRevit.UI;

/// <summary>
/// Service for sending Revit documents to Speckle without UI interaction.
/// </summary>
public static class HeadlessSendService
{
  /// <summary>
  /// Sends the current document to Speckle using the provided configuration.
  /// </summary>
  /// <param name="uiApp">The Revit UIApplication</param>
  /// <param name="config">The automated send configuration</param>
  /// <param name="cancellationToken">Cancellation token</param>
  /// <param name="document">Optional document to send. If null, uses ActiveUIDocument.</param>
  /// <returns>Result of the send operation</returns>
  public static async Task<AutomatedSendResult> SendCurrentDocument(
    UIApplication uiApp,
    AutomatedSendConfig config,
    CancellationToken cancellationToken = default,
    Document? document = null
  )
  {
    SpeckleLog.Logger.Information("=== HeadlessSendService.SendCurrentDocument START ===");
    var stopwatch = Stopwatch.StartNew();
    var result = new AutomatedSendResult();
    
    try
    {
      // Use provided document or fall back to ActiveUIDocument
      SpeckleLog.Logger.Information("Getting document. Provided document: {doc}, ActiveUIDocument: {activeDoc}",
        document?.Title ?? "null", uiApp.ActiveUIDocument?.Document?.Title ?? "null");
      
      var doc = document ?? uiApp.ActiveUIDocument?.Document;
      if (doc == null)
      {
        SpeckleLog.Logger.Warning("Document is null, waiting 3 seconds and retrying...");
        // Wait a bit and retry for timing issues when launched from command line
        await Task.Delay(3000);
        doc = uiApp.ActiveUIDocument?.Document;
        SpeckleLog.Logger.Information("Document after retry: {documentName}", doc?.Title ?? "null");
        if (doc == null)
        {
          var error = "No active document found in Revit.";
          SpeckleLog.Logger.Error(error);
          throw new InvalidOperationException(error);
        }
      }

      SpeckleLog.Logger.Information("Using document: {documentName}, Path: {documentPath}", doc.Title, doc.PathName);
      result.DocumentName = doc.Title;
      result.DocumentPath = doc.PathName;

      // Get account first (needed for stream creation)
      SpeckleLog.Logger.Information("Resolving account for server: {serverUrl}, email: {email}",
        config.ServerUrl, config.AccountEmail ?? "default");
      var account = ResolveAccount(config.ServerUrl, config.AccountEmail);
      if (account == null)
      {
        var error = $"No account found for server '{config.ServerUrl}'" +
          (string.IsNullOrEmpty(config.AccountEmail) ? "" : $" with email '{config.AccountEmail}'") +
          ". Please add an account using Speckle Manager.";
        SpeckleLog.Logger.Error(error);
        throw new InvalidOperationException(error);
      }
      SpeckleLog.Logger.Information("Account resolved: {accountEmail}", account.userInfo?.email ?? "unknown");

      // Get or create stream ID
      string streamId;
      if (config.AutoCreateStream)
      {
        SpeckleLog.Logger.Information("AutoCreateStream is true, creating new project/stream for: {documentName}", doc.Title);
        // Create a new project/stream for this model
        streamId = await CreateOrGetStreamForDocument(account, doc.Title, config, cancellationToken)
          .ConfigureAwait(false);
        
        SpeckleLog.Logger.Information(
          "Created new project/stream for document: {documentName}, stream ID: {streamId}",
          doc.Title, streamId
        );
      }
      else
      {
        SpeckleLog.Logger.Information("AutoCreateStream is false, using configured stream ID");
        // Use configured stream ID
        streamId = config.GetStreamIdForDocument(doc.Title);
        if (string.IsNullOrEmpty(streamId))
        {
          var error = $"No stream ID configured for document '{doc.Title}' and AutoCreateStream is false. " +
            "Please set DefaultStreamId, add a mapping in StreamIdMapping, or set AutoCreateStream to true.";
          SpeckleLog.Logger.Error(error);
          throw new InvalidOperationException(error);
        }
        SpeckleLog.Logger.Information("Using stream ID: {streamId}", streamId);
      }
      
      result.StreamId = streamId;

      // Create filter
      SpeckleLog.Logger.Information("Creating filter: {filterType}", config.DefaultFilter);
      var filter = CreateFilter(config.DefaultFilter);

      // Create settings
      SpeckleLog.Logger.Information("Creating settings. Count: {count}", config.DefaultSettings?.Count ?? 0);
      var settings = CreateSettings(config.DefaultSettings);

      // Generate commit message
      var commitMessage = config.GenerateCommitMessage(doc.Title);
      SpeckleLog.Logger.Information("Commit message: {commitMessage}", commitMessage);

      // Send
      SpeckleLog.Logger.Information("=== Calling SendDocument ===");
      var commitId = await SendDocument(
        uiApp,
        doc,
        streamId,
        account,
        filter,
        settings,
        config.BranchName,
        commitMessage,
        cancellationToken
      ).ConfigureAwait(false);
      
      SpeckleLog.Logger.Information("=== SendDocument completed. Commit ID: {commitId} ===", commitId);

      result.Success = true;
      result.CommitId = commitId;
      
      SpeckleLog.Logger.Information(
        "=== SUCCESS: Sent document {documentName} to stream {streamId}, commit {commitId} ===",
        doc.Title, streamId, commitId
      );
    }
    catch (Exception ex)
    {
      result.Success = false;
      result.ErrorMessage = ex.Message;
      SpeckleLog.Logger.Error(ex, "=== ERROR: Failed to send document headlessly ===");
      SpeckleLog.Logger.Error("Exception type: {exceptionType}, Message: {message}", ex.GetType().Name, ex.Message);
      if (ex.InnerException != null)
      {
        SpeckleLog.Logger.Error("Inner exception: {innerMessage}", ex.InnerException.Message);
      }
    }
    finally
    {
      stopwatch.Stop();
      result.DurationSeconds = stopwatch.Elapsed.TotalSeconds;
      SpeckleLog.Logger.Information("Total duration: {duration} seconds", result.DurationSeconds);
    }

    // Write result file
    try
    {
      var resultsDir = AutomatedSendConfigManager.GetResultsDirectory(config);
      SpeckleLog.Logger.Information("Writing result file to: {resultsDir}", resultsDir);
      result.WriteToFile(resultsDir);
      SpeckleLog.Logger.Information("Result file written successfully");
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Error(ex, "Failed to write result file to: {resultsDir}", 
        AutomatedSendConfigManager.GetResultsDirectory(config));
    }

    SpeckleLog.Logger.Information("=== HeadlessSendService.SendCurrentDocument END. Success: {success} ===", result.Success);
    return result;
  }

  /// <summary>
  /// Sends a document to Speckle.
  /// </summary>
  private static async Task<string> SendDocument(
    UIApplication uiApp,
    Document doc,
    string streamId,
    Account account,
    ISelectionFilter filter,
    List<ISetting> settings,
    string branchName,
    string commitMessage,
    CancellationToken cancellationToken
  )
  {
    SpeckleLog.Logger.Information("=== SendDocument START ===");
    SpeckleLog.Logger.Information("Document: {documentName}, Stream ID: {streamId}, Branch: {branch}", 
      doc.Title, streamId, branchName);
    
    using var ctx = RevitConverterState.Push();

    // Get converter
    SpeckleLog.Logger.Information("Loading converter...");
    var converter = KitManager.GetDefaultKit().LoadConverter(ConnectorRevitUtils.RevitAppName);
    converter.SetContextDocument(doc);
    converter.Report.ReportObjects.Clear();
    SpeckleLog.Logger.Information("Converter loaded: {converterName}", converter.Name);

    // Set converter settings
    SpeckleLog.Logger.Information("Setting converter settings. Count: {count}", settings.Count);
    var settingsDict = new Dictionary<string, string>();
    foreach (var setting in settings)
    {
      settingsDict.Add(setting.Slug, setting.Selection);
    }
    converter.SetConverterSettings(settingsDict);

    // Create cache
    SpeckleLog.Logger.Information("Creating document cache...");
    var cache = new RevitDocumentAggregateCache(new UIDocumentProvider(uiApp));

    // Get elements based on filter
    SpeckleLog.Logger.Information("Getting elements from filter: {filterSlug}", filter.Slug);
    var selectedObjects = await APIContext
      .Run(_ => GetSelectionFilterObjects(doc, converter, filter, cache, settings))
      .ConfigureAwait(false);

    SpeckleLog.Logger.Information("Filter returned {count} objects", selectedObjects.Count);

    if (!selectedObjects.Any())
    {
      var error = "There are zero objects to send. The filter returned no elements.";
      SpeckleLog.Logger.Error(error);
      throw new InvalidOperationException(error);
    }

    SpeckleLog.Logger.Information("Found {count} objects to send", selectedObjects.Count);

    // Set up converter context
    converter.SetContextDocument(cache);
    converter.SetContextObjects(
      selectedObjects
        .Select(x => new ApplicationObject(x.UniqueId, x.GetType().ToString()) { applicationId = x.UniqueId })
        .ToList()
    );

    var commitObject = converter.ConvertToSpeckle(doc) ?? new Collection();
    
    if (converter is not IRevitCommitObjectBuilderExposer builderExposer)
    {
      throw new Exception(
        $"Converter {converter.Name} by {converter.Author} does not provide the necessary object builder."
      );
    }
    var commitObjectBuilder = builderExposer.commitObjectBuilder;

    // Convert objects
    SpeckleLog.Logger.Information("Starting conversion of {count} objects...", selectedObjects.Count);
    var convertedCount = 0;
    var processedCount = 0;
    await APIContext
      .Run(() =>
      {
        foreach (var revitElement in selectedObjects)
        {
          cancellationToken.ThrowIfCancellationRequested();
          processedCount++;

          if (processedCount % 100 == 0)
          {
            SpeckleLog.Logger.Information("Converting progress: {processed}/{total}", processedCount, selectedObjects.Count);
          }

          try
          {
            if (!converter.CanConvertToSpeckle(revitElement))
            {
              continue;
            }

            var result = converter.ConvertToSpeckle(revitElement);
            if (result != null)
            {
              result.applicationId = revitElement.UniqueId;
              commitObjectBuilder.IncludeObject(result, revitElement);
              convertedCount++;
            }
          }
          catch (Exception ex)
          {
            SpeckleLog.Logger.Warning(
              ex,
              "Failed to convert element {elementId} of type {elementType}",
              revitElement.Id.IntegerValue,
              revitElement.GetType().Name
            );
          }
        }
      })
      .ConfigureAwait(false);

    SpeckleLog.Logger.Information("Conversion complete. Processed: {processed}, Converted: {converted}", 
      processedCount, convertedCount);
    cache.InvalidateAll();

    cancellationToken.ThrowIfCancellationRequested();

    if (convertedCount == 0)
    {
      var error = "Zero objects converted successfully. Send stopped.";
      SpeckleLog.Logger.Error(error);
      throw new SpeckleException(error);
    }

    SpeckleLog.Logger.Information("Converted {count} objects successfully", convertedCount);

    // Build commit object
    SpeckleLog.Logger.Information("Building commit object...");
    commitObjectBuilder.BuildCommitObject(commitObject);
    SpeckleLog.Logger.Information("Commit object built");

    // Create client and transport
    SpeckleLog.Logger.Information("Creating Speckle client and transport...");
    var client = new Client(account);
    var transports = new List<ITransport> { new ServerTransport(account, streamId) };
    SpeckleLog.Logger.Information("Client and transport created");

    // Send to server
    SpeckleLog.Logger.Information("=== Starting upload to server ===");
    var objectId = await Operations
      .Send(
        @object: commitObject,
        cancellationToken: cancellationToken,
        transports: transports,
        onProgressAction: dict => 
        {
          if (dict.TryGetValue("RemoteTransport", out var progress))
          {
            SpeckleLog.Logger.Information("Upload progress: {progress}", progress);
          }
        },
        onErrorAction: (message, ex) => SpeckleLog.Logger.Error(ex, "Send error: {message}", message),
        disposeTransports: true
      )
      .ConfigureAwait(true);

    SpeckleLog.Logger.Information("=== Upload completed. Object ID: {objectId} ===", objectId);

    cancellationToken.ThrowIfCancellationRequested();

    // Create commit
    SpeckleLog.Logger.Information("Creating commit on server...");
    var commit = new CommitCreateInput
    {
      streamId = streamId,
      objectId = objectId,
      branchName = branchName,
      message = commitMessage ?? $"Sent {convertedCount} objects from {ConnectorRevitUtils.RevitAppName}.",
      sourceApplication = ConnectorRevitUtils.RevitAppName,
    };

    var commitId = await client.CommitCreate(commit, cancellationToken).ConfigureAwait(false);

    SpeckleLog.Logger.Information("=== Commit created successfully. Commit ID: {commitId} ===", commitId);
    SpeckleLog.Logger.Information("=== SendDocument COMPLETE ===");

    return commitId;
  }

  /// <summary>
  /// Gets elements based on the filter type.
  /// </summary>
  private static List<Element> GetSelectionFilterObjects(
    Document doc,
    ISpeckleConverter converter,
    ISelectionFilter filter,
    IRevitDocumentAggregateCache cache,
    List<ISetting> settings
  )
  {
    var selection = new List<Element>();

    switch (filter.Slug)
    {
      case "all":
        // Get all supported elements
        selection = GetAllElements(doc, cache);
        break;

      case "category":
        if (filter is ListSelectionFilter catFilter && catFilter.Selection.Any())
        {
          selection = GetElementsByCategory(doc, catFilter.Selection, cache);
        }
        else
        {
          selection = GetAllElements(doc, cache);
        }
        break;

      case "view":
        if (filter is ListSelectionFilter viewFilter && viewFilter.Selection.Any())
        {
          selection = GetElementsByView(doc, viewFilter.Selection.First());
        }
        else
        {
          selection = GetAllElements(doc, cache);
        }
        break;

      default:
        // Default to all elements
        selection = GetAllElements(doc, cache);
        break;
    }

    return selection;
  }

  /// <summary>
  /// Gets all supported elements from the document.
  /// </summary>
  private static List<Element> GetAllElements(Document doc, IRevitDocumentAggregateCache cache)
  {
    var selection = new List<Element>();

    // Add project info for non-family documents
    if (!doc.IsFamilyDocument)
    {
      selection.Add(doc.ProjectInformation);
    }

    // Add 2D and 3D views
    selection.AddRange(doc.Views2D());
    selection.AddRange(doc.Views3D());

    // Add all supported elements (excluding schedules for performance)
    var elements = doc.GetSupportedElements(cache).Where(e => e is not TableView);
    selection.AddRange(elements);

    // Add supported types
    selection.AddRange(doc.GetSupportedTypes(cache));

    return selection;
  }

  /// <summary>
  /// Gets elements by category.
  /// </summary>
  private static List<Element> GetElementsByCategory(
    Document doc,
    List<string> categoryNames,
    IRevitDocumentAggregateCache cache
  )
  {
    var selection = new List<Element>();
    var catIds = new List<ElementId>();

    foreach (var catName in categoryNames)
    {
      var category = cache.GetOrInitializeWithDefaultFactory<Category>().TryGet(catName);
      if (category != null)
      {
        catIds.Add(category.Id);
      }
    }

    if (!catIds.Any())
    {
      return GetAllElements(doc, cache);
    }

    using var categoryFilter = new ElementMulticategoryFilter(catIds);
    using var collector = new FilteredElementCollector(doc);
    
    selection.AddRange(
      collector
        .WhereElementIsNotElementType()
        .WhereElementIsViewIndependent()
        .WherePasses(categoryFilter)
        .ToList()
    );

    return selection;
  }

  /// <summary>
  /// Gets elements visible in a specific view.
  /// </summary>
  private static List<Element> GetElementsByView(Document doc, string viewName)
  {
    var selection = new List<Element>();

    using var collector = new FilteredElementCollector(doc);
    var view = collector
      .WhereElementIsNotElementType()
      .OfClass(typeof(View))
      .Cast<View>()
      .FirstOrDefault(v => v.Title == viewName && !v.IsTemplate);

    if (view == null)
    {
      throw new InvalidOperationException($"View '{viewName}' not found in document.");
    }

    selection.Add(view);

    using var viewCollector = new FilteredElementCollector(doc, view.Id);
    selection.AddRange(
      viewCollector
        .WhereElementIsNotElementType()
        .WhereElementIsViewIndependent()
        .ToList()
    );

    return selection;
  }

  /// <summary>
  /// Resolves an account from the configuration.
  /// </summary>
  private static Account? ResolveAccount(string serverUrl, string? accountEmail)
  {
    // Normalize URL: convert localhost to 127.0.0.1 for matching
    var normalizedUrl = NormalizeServerUrl(serverUrl);
    SpeckleLog.Logger.Information("Resolving account for server URL: {originalUrl} (normalized: {normalizedUrl})", 
      serverUrl, normalizedUrl);
    
    var accounts = AccountManager.GetAccounts(normalizedUrl).ToList();

    if (!accounts.Any())
    {
      SpeckleLog.Logger.Information("No accounts found for normalized URL, trying original URL...");
      // Try with original URL in case account was stored with different format
      accounts = AccountManager.GetAccounts(serverUrl).ToList();
    }

    if (!accounts.Any())
    {
      SpeckleLog.Logger.Information("No accounts found for server URL, trying default account...");
      // Try default account if no accounts for this server
      var defaultAccount = AccountManager.GetDefaultAccount();
      if (defaultAccount != null)
      {
        var defaultUrl = NormalizeServerUrl(defaultAccount.serverInfo?.url ?? "");
        if (defaultUrl == normalizedUrl || defaultUrl == NormalizeServerUrl(serverUrl))
        {
          SpeckleLog.Logger.Information("Using default account for server: {serverUrl}", defaultAccount.serverInfo?.url);
          return defaultAccount;
        }
      }
      return null;
    }

    // If email is specified, find matching account
    if (!string.IsNullOrEmpty(accountEmail))
    {
      var matchingAccount = accounts.FirstOrDefault(
        a => a.userInfo?.email?.Equals(accountEmail, StringComparison.OrdinalIgnoreCase) == true
      );
      if (matchingAccount != null)
      {
        SpeckleLog.Logger.Information("Found account matching email: {email}", accountEmail);
        return matchingAccount;
      }
    }

    // Return first account for this server, or default if available
    var defaultForServer = accounts.FirstOrDefault(a => a.isDefault);
    var selectedAccount = defaultForServer ?? accounts.First();
    SpeckleLog.Logger.Information("Selected account: {email} (isDefault: {isDefault})", 
      selectedAccount.userInfo?.email ?? "unknown", selectedAccount.isDefault);
    return selectedAccount;
  }

  /// <summary>
  /// Normalizes server URLs to handle localhost/127.0.0.1 differences.
  /// </summary>
  private static string NormalizeServerUrl(string url)
  {
    if (string.IsNullOrEmpty(url))
      return url;

    // Convert localhost to 127.0.0.1 for consistent matching
    var uri = new Uri(url);
    if (uri.Host.Equals("localhost", StringComparison.OrdinalIgnoreCase))
    {
      var normalized = new UriBuilder(uri)
      {
        Host = "127.0.0.1"
      };
      return normalized.Uri.ToString().TrimEnd('/');
    }

    return url.TrimEnd('/');
  }

  /// <summary>
  /// Creates a filter based on the filter slug.
  /// </summary>
  private static ISelectionFilter CreateFilter(string filterSlug)
  {
    return filterSlug?.ToLowerInvariant() switch
    {
      "all" => new AllSelectionFilter
      {
        Slug = "all",
        Name = "Everything",
        Icon = "CubeScan",
        Description = "Sends all supported elements and project information."
      },
      _ => new AllSelectionFilter
      {
        Slug = "all",
        Name = "Everything",
        Icon = "CubeScan",
        Description = "Sends all supported elements and project information."
      }
    };
  }

  /// <summary>
  /// Creates settings from the configuration dictionary.
  /// </summary>
  private static List<ISetting> CreateSettings(Dictionary<string, string> settingsDict)
  {
    var settings = new List<ISetting>();

    foreach (var kvp in settingsDict)
    {
      // For now, just create checkbox settings for boolean values
      if (bool.TryParse(kvp.Value, out var boolValue))
      {
        settings.Add(new CheckBoxSetting
        {
          Slug = kvp.Key,
          Name = kvp.Key,
          IsChecked = boolValue,
          Selection = kvp.Value
        });
      }
      else
      {
        // For other types, create a generic setting-like object
        settings.Add(new CheckBoxSetting
        {
          Slug = kvp.Key,
          Name = kvp.Key,
          Selection = kvp.Value
        });
      }
    }

    return settings;
  }

  /// <summary>
  /// Creates a new project/stream for the document.
  /// </summary>
  private static async Task<string> CreateOrGetStreamForDocument(
    Account account,
    string documentName,
    AutomatedSendConfig config,
    CancellationToken cancellationToken
  )
  {
    var client = new Client(account);

    // Generate project name and description
    var projectName = config.GenerateProjectName(documentName);
    var projectDescription = config.GenerateProjectDescription(documentName);

    // Parse visibility
    var visibility = ParseProjectVisibility(config.ProjectVisibility);

    try
    {
      // Create new project using the modern API
      SpeckleLog.Logger.Information(
        "Creating new project '{projectName}' for document '{documentName}'",
        projectName, documentName
      );

      var project = await client.Project
        .Create(
          new ProjectCreateInput(projectName, projectDescription, visibility),
          cancellationToken
        )
        .ConfigureAwait(false);

      SpeckleLog.Logger.Information(
        "Successfully created project '{projectName}' with ID {projectId}",
        project.name, project.id
      );

      return project.id;
    }
    catch (Exception ex)
    {
      SpeckleLog.Logger.Warning(
        ex,
        "Failed to create project using Project.Create API. Trying legacy StreamCreate API."
      );

      // Fallback to legacy StreamCreate API (for older servers)
      try
      {
        var streamId = await client.StreamCreate(
          new StreamCreateInput
          {
            name = projectName,
            description = projectDescription,
            isPublic = visibility == ProjectVisibility.Public
          },
          cancellationToken
        ).ConfigureAwait(false);

        SpeckleLog.Logger.Information(
          "Created stream using legacy API: {streamId}",
          streamId
        );

        return streamId;
      }
      catch (Exception legacyEx)
      {
        SpeckleLog.Logger.Error(
          legacyEx,
          "Failed to create stream using both modern and legacy APIs"
        );
        throw new InvalidOperationException(
          $"Failed to create project/stream for '{projectName}': {legacyEx.Message}",
          legacyEx
        );
      }
    }
  }

  /// <summary>
  /// Parses project visibility string to enum.
  /// </summary>
  private static ProjectVisibility ParseProjectVisibility(string visibility)
  {
    return visibility?.ToLowerInvariant() switch
    {
      "public" => ProjectVisibility.Public,
      "unlisted" => ProjectVisibility.Unlisted,
      "private" or _ => ProjectVisibility.Private
    };
  }
}

