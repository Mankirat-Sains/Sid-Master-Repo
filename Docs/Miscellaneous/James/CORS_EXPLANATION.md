# Why Electron Works But Browser Doesn't: CORS Explanation

## The Core Difference

### **Electron (Desktop App)**
- Electron runs as a **desktop application**, not a web browser
- It uses Chromium's rendering engine, but **does NOT enforce web browser security policies**
- **CORS (Cross-Origin Resource Sharing) is NOT enforced** in Electron
- Electron can make requests to ANY server from ANY origin without restrictions
- This is why your Electron app worked - it could directly fetch from the Speckle server

### **Web Browser (Chrome, Firefox, Safari, etc.)**
- Web browsers **strictly enforce CORS policies** for security
- CORS prevents websites from making unauthorized requests to other servers
- When your Nuxt app (running on `localhost:3000`) tries to fetch from the Speckle server (`k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com`), the browser checks:
  1. **Origin mismatch**: `localhost:3000` ≠ `ca-central-1.elb.amazonaws.com`
  2. **CORS headers check**: Browser looks for `Access-Control-Allow-Origin` header in the response
  3. **If missing or doesn't match**: Browser **blocks the request** before it even reaches the server

## What Happens in Each Case

### Electron Flow (WORKS ✅)
```
Electron App
    ↓ (no CORS check)
Direct HTTP request → Speckle Server
    ↓ (server responds with data)
Success! Model loads
```

### Browser Flow (FAILS ❌)
```
Nuxt App (localhost:3000)
    ↓ (browser checks CORS)
Browser: "Wait, this is a different origin..."
    ↓ (checks server response headers)
Browser: "No 'Access-Control-Allow-Origin' header found"
    ↓ (blocks request before it reaches server)
❌ CORS Error: Request blocked
```

## The Error You're Seeing

```
Access to fetch at 'http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com/objects/...' 
from origin 'http://localhost:3000' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

This means:
1. ✅ Your code is correct
2. ✅ Your token is working (UrlHelper.getResourceUrls succeeded)
3. ❌ The Speckle server is not configured to allow requests from `localhost:3000`
4. ❌ The browser enforces this security policy (Electron doesn't)

## Solutions

### Option 1: Server-Side CORS Configuration (Best)
The Speckle server needs to send these headers:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```

### Option 2: Production Proxy
Proxy requests through your own backend server (which doesn't have CORS restrictions):
```
Browser → Your Backend (localhost:3000) → Speckle Server
```
Your backend makes the request (no CORS check), then forwards the response.

### Option 3: Development Workaround
Use a browser extension that disables CORS (ONLY for development, never production!)

## Why This Security Exists

CORS exists to prevent malicious websites from:
- Stealing your data from other websites
- Making unauthorized API calls
- Accessing resources you don't want them to access

In Electron, this is less of a concern because:
- Users explicitly install your app
- The app runs locally on their machine
- There's less risk of malicious code injection from the web

## Summary

**Electron = No CORS enforcement = Works**
**Browser = CORS enforcement = Blocked unless server allows it**

Your code and token are correct - this is purely a browser security policy that the Speckle server needs to accommodate.

