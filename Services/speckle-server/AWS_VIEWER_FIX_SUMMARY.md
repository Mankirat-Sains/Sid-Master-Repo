# AWS Viewer Fix - Diagnostic Summary & Solution

## Problem Summary
The viewer works locally but fails on AWS with 404 errors for `/objects/` paths when loading models.

## Root Causes Identified

### 1. **Critical: Ingress Path Order Issue** ✅ FIXED
**Location:** `utils/helm/speckle-server/templates/minion.ingress.yml`

**Problem:** The catch-all path `/` was listed FIRST in the paths array, causing it to intercept `/objects/` requests before the more specific `/objects/` path in `objects.minion.ingress.yml` could handle them.

**Error Pattern:**
```
Failed to load resource: 404 (Page not found: /objects/02f1e7abe0/7d53bcf28c6696ecac8781684a0aa006/single)
```

**Fix Applied:** Moved the catch-all `/` path to the END of the paths array so more specific paths are evaluated first.

### 2. **Missing /streams/ Path** ✅ FIXED
**Location:** `utils/helm/speckle-server/templates/objects.minion.ingress.yml`

**Problem:** The viewer constructs initial URLs like `/streams/{projectId}/objects/{objectId}`, but the ingress had no `/streams/` path configured.

**Fix Applied:** Added `/streams/` path routing to `speckle-objects` service (lines 54-60).

## How the Viewer Loads Objects

1. **Initial URL Construction:**
   - Frontend uses: `${apiOrigin}/streams/${projectId}/objects/${objectId}`
   - See: `packages/frontend-2/lib/viewer/composables/viewer.ts:296`

2. **ObjectLoader2 URL Construction:**
   - Parses the `/streams/` URL and extracts `serverUrl`, `streamId`, `objectId`
   - Then constructs: `${serverUrl}/objects/${streamId}/${objectId}/single`
   - See: `packages/objectloader2/src/core/stages/serverDownloader.ts:59-61`

3. **Why It Works Locally:**
   - Local dev servers typically proxy all requests to the backend
   - No strict ingress routing - everything goes to one server
   - Path conflicts don't occur

4. **Why It Fails on AWS:**
   - Strict ingress-based routing
   - Path matching order matters
   - Catch-all `/` was intercepting requests before specific paths

## Files Modified

### 1. `utils/helm/speckle-server/templates/minion.ingress.yml`
- **Change:** Moved catch-all `/` path from first position to last position
- **Reason:** Ensures more specific paths (like `/objects/`, `/api/`, etc.) are matched before the catch-all

### 2. `utils/helm/speckle-server/templates/objects.minion.ingress.yml`
- **Change:** Added `/streams/` path routing (lines 54-60)
- **Reason:** Viewer needs this path for initial object URL construction

## Deployment Steps

1. **Navigate to Helm chart directory:**
   ```powershell
   cd C:\Users\shine\speckle1\speckle-server\utils\helm\speckle-server
   ```

2. **Upgrade the Helm release:**
   ```powershell
   helm upgrade --install speckle-server . `
     --namespace speckle-production `
     --values C:\Users\shine\speckle1\speckle-server\infrastructure\helm-values-aws.yaml
   ```

3. **Verify ingress resources:**
   ```powershell
   # Check all ingress resources
   kubectl get ingress -n speckle-production
   
   # Verify objects ingress has /objects/ and /streams/ paths
   kubectl describe ingress speckle-server-minion-api-objects -n speckle-production
   
   # Verify main ingress has catch-all at the end
   kubectl describe ingress speckle-server-minion -n speckle-production
   ```

4. **Wait for ALB update (1-2 minutes):**
   - AWS ALB Ingress Controller will automatically update the load balancer
   - Monitor in AWS Console or wait and test

5. **Test the viewer:**
   - Navigate to a model page
   - Check browser console for errors
   - Models should now load successfully

## Verification Checklist

- [ ] Helm chart deployed successfully
- [ ] Ingress resources show correct paths
- [ ] `/objects/` path routes to `speckle-objects` service
- [ ] `/streams/` path routes to `speckle-objects` service
- [ ] Catch-all `/` is last in `minion.ingress.yml`
- [ ] No 404 errors in browser console
- [ ] Models load in viewer

## Expected Behavior After Fix

1. Viewer constructs: `/streams/{projectId}/objects/{objectId}` ✅ Routes to objects service
2. ObjectLoader2 requests: `/objects/{streamId}/{objectId}/single` ✅ Routes to objects service
3. Objects load successfully ✅ No 404 errors

## Additional Notes

- The `/objects/` path was already configured but wasn't being matched due to path order
- Both fixes are required for the viewer to work correctly
- The changes are minimal and low-risk (just routing configuration)
- No application code changes needed



