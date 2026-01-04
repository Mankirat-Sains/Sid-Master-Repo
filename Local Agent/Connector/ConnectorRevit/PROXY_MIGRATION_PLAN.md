# Proxy Logic Migration Plan

## Overview
This document outlines the plan to migrate proxy creation logic from the new connector (`speckle-sharp-connectors`) to the old connector (`speckle-sharp`).

## Key Components to Migrate

### 1. Proxy Keys
- **Source**: `speckle-sharp-connectors/Sdk/Speckle.Connectors.Common/Operations/ProxyKeys.cs`
- **Destination**: Create in old connector's converter or shared resources
- **Purpose**: Defines constant keys for proxy types in root object

### 2. RevitToSpeckleCacheSingleton
- **Source**: `speckle-sharp-connectors/Converters/Revit/Speckle.Converters.RevitShared/Helpers/RevitToSpeckleCacheSingleton.cs`
- **Destination**: `Objects/Converters/ConverterRevit/ConverterRevitShared/` or similar
- **Purpose**: Manages proxy cache during conversion
- **Key Methods**:
  - `GetRenderMaterialProxyListForObjects()`
  - `GetInstanceDefinitionProxiesForObjects()`
  - `GetBaseObjectsForObjects()`
  - `AddMeshToMaterialProxy()`

### 3. LevelUnpacker
- **Source**: `speckle-sharp-connectors/Connectors/Revit/Speckle.Connectors.RevitShared/HostApp/LevelUnpacker.cs`
- **Destination**: `Objects/Converters/ConverterRevit/ConverterRevitShared/`
- **Purpose**: Creates LevelProxy objects from Revit elements
- **Dependencies**: LevelExtractor, PropertiesExtractor

### 4. Instance Proxy Creation Logic
- **Source**: `speckle-sharp-connectors/Converters/Revit/Speckle.Converters.RevitShared/ToSpeckle/TopLevel/RevitElementTopLevelConverterToSpeckle.cs`
- **Key Method**: `ProcessDisplayValues()` - creates InstanceProxy and InstanceDefinitionProxy
- **Destination**: Integrate into old converter's display value processing

### 5. Proxy Attachment in BuildCommitObject
- **Source**: `speckle-sharp-connectors/Connectors/Revit/Speckle.Connectors.RevitShared/Operations/Send/RevitRootObjectBuilder.cs` (lines 244-263)
- **Destination**: `Objects/Converters/ConverterRevit/ConverterRevitShared/RevitCommitObjectBuilder.cs`
- **Purpose**: Attach proxies to root commit object before sending

## Implementation Steps

1. **Copy ProxyKeys.cs** - Simple constants file
2. **Copy RevitToSpeckleCacheSingleton** - Core caching mechanism
3. **Copy LevelUnpacker and dependencies** - Level proxy creation
4. **Modify converter to populate cache** - During conversion, populate the cache
5. **Modify BuildCommitObject** - Add proxy attachment logic
6. **Test** - Verify proxies are created correctly

## Notes

- The old connector uses `IRevitCommitObjectBuilder` pattern
- Need to ensure cache is accessible during conversion and build phases
- May need to modify converter to track elements for proxy creation
- Instance proxy logic is complex and integrated into display value extraction

