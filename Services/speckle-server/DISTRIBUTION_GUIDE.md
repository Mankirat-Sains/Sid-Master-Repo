# Speckle Server Distribution Guide

This guide covers options for packaging the Speckle Server for client distribution, including Docker containers, desktop applications, and performance optimization.

## Table of Contents

1. [Docker Packaging Options](#docker-packaging-options)
2. [Desktop Application Options](#desktop-application-options)
3. [Performance Issues & Solutions](#performance-issues--solutions)

---

## Docker Packaging Options

### Option 1: Docker Compose (Recommended for Clients)

Create a `docker-compose.yml` that bundles everything together:

```yaml
version: '3.8'

services:
  postgres:
    image: 'postgres:16.4-alpine3.20'
    restart: always
    environment:
      POSTGRES_DB: speckle
      POSTGRES_USER: speckle
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-speckle}
    volumes:
      - postgres-data:/var/lib/postgresql/data/
    ports:
      - '127.0.0.1:5432:5432'

  redis:
    image: 'valkey/valkey:8.1-alpine'
    restart: always
    volumes:
      - redis-data:/data
    ports:
      - '127.0.0.1:6379:6379'

  server:
    build:
      context: .
      dockerfile: packages/server/Dockerfile
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://speckle:speckle@postgres:5432/speckle
      - REDIS_URL=redis://redis:6379
      # Add other required environment variables
    ports:
      - '3000:3000'
    volumes:
      # Optional: mount config files
      - ./config:/app/config

  frontend:
    build:
      context: .
      dockerfile: packages/frontend-2/Dockerfile
    depends_on:
      - server
    environment:
      - NUXT_PUBLIC_API_ORIGIN=http://localhost:3000
    ports:
      - '8080:8080'

volumes:
  postgres-data:
  redis-data:
```

**To distribute:**

1. Create a zip file with:

   - `docker-compose.yml`
   - `Dockerfile` files (or provide pre-built images)
   - Configuration files
   - README with setup instructions

2. Client runs:
   ```bash
   docker compose up -d
   ```

### Option 2: Single Docker Image (All-in-One)

Create a Dockerfile that includes server + frontend in one container:

```dockerfile
FROM node:22-bookworm-slim AS base

# Install dependencies
RUN apt-get update && apt-get install -y postgresql-client redis-tools

WORKDIR /app

# Copy and build server
COPY packages/server ./server
WORKDIR /app/server
RUN yarn install && yarn build

# Copy and build frontend
WORKDIR /app
COPY packages/frontend-2 ./frontend
WORKDIR /app/frontend
RUN yarn install && yarn build

# Production image
FROM node:22-bookworm-slim
WORKDIR /app
COPY --from=base /app/server/dist ./server/dist
COPY --from=base /app/frontend/.output ./frontend/.output

# Use a startup script that runs both
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
```

### Option 3: Pre-built Docker Images

Build and push images to a registry (Docker Hub, AWS ECR, etc.):

```bash
# Build images
docker build -t mycompany/speckle-server:latest -f packages/server/Dockerfile .
docker build -t mycompany/speckle-frontend:latest -f packages/frontend-2/Dockerfile .

# Push to registry
docker push mycompany/speckle-server:latest
docker push mycompany/speckle-frontend:latest
```

Clients can then pull and run:

```bash
docker pull mycompany/speckle-server:latest
docker run -d mycompany/speckle-server:latest
```

---

## Desktop Application Options

### Option 1: Electron Wrapper

Wrap the Docker containers in an Electron app:

**Tools:**

- [Electron](https://www.electronjs.org/) - Desktop app framework
- [Docker Desktop SDK](https://docs.docker.com/desktop/dev-desktop/use-dev-desktop-sdk/) - Manage Docker from Electron
- [Tauri](https://tauri.app/) - Alternative to Electron (smaller, more secure)

**Architecture:**

```
┌─────────────────────────────────┐
│  Electron/Tauri Desktop App     │
│  ┌───────────────────────────┐  │
│  │  Embedded Browser (UI)    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Docker Container Manager │  │
│  │  - Start/Stop containers  │  │
│  │  - Health checks          │  │
│  │  - Logs viewer            │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Local Docker Containers  │  │
│  │  - Postgres               │  │
│  │  - Redis                  │  │
│  │  - Server                 │  │
│  │  - Frontend               │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Option 2: Native Installer (Windows/Mac/Linux)

Use tools to create native installers:

**Windows:**

- [Inno Setup](https://jrsoftware.org/isinfo.php) - Creates `.exe` installers
- [WiX Toolset](https://wixtoolset.org/) - MSI installer creation

**Mac:**

- [create-dmg](https://github.com/sindresorhus/create-dmg) - Creates `.dmg` files
- Xcode (for `.app` bundles)

**Linux:**

- [AppImage](https://appimage.org/) - Portable Linux apps
- [Snap](https://snapcraft.io/) - Ubuntu snap packages
- [Flatpak](https://flatpak.org/) - Universal Linux packages

**Example with Electron Builder:**

```json
{
  "build": {
    "appId": "com.yourcompany.speckle",
    "productName": "Speckle Server",
    "win": {
      "target": ["nsis", "portable"]
    },
    "mac": {
      "target": ["dmg"]
    },
    "linux": {
      "target": ["AppImage", "deb", "rpm"]
    }
  }
}
```

### Option 3: Portable Distribution

Create a portable folder that clients can run without installation:

```
speckle-portable/
├── docker-compose.yml
├── start.bat (Windows)
├── start.sh (Linux/Mac)
├── config/
│   └── .env
└── README.txt
```

**start.bat (Windows):**

```batch
@echo off
echo Starting Speckle Server...
docker compose up -d
echo Server starting at http://localhost:8080
pause
```

**start.sh (Linux/Mac):**

```bash
#!/bin/bash
echo "Starting Speckle Server..."
docker compose up -d
echo "Server starting at http://localhost:8080"
```

---

## Performance Issues & Solutions

### Development Mode Performance Issues

The slow/glitchy interface in development is typically caused by:

#### 1. **Hot Module Replacement (HMR) Overhead**

**Issue:** Nuxt/Vue dev server constantly watches and rebuilds files

**Solutions:**

- **Use production build for testing:**

  ```bash
  # Frontend
  cd packages/frontend-2
  yarn build
  yarn preview

  # Server
  cd packages/server
  yarn build
  NODE_ENV=production node dist/app.js
  ```

- **Disable DevTools in development:**
  ```typescript
  // nuxt.config.ts
  modules: [...(process.env.NODE_ENV === 'development' ? ['@nuxt/devtools'] : [])]
  ```

#### 2. **Large Bundle Size**

**Issue:** Development mode includes source maps, unminified code, and dev tools

**Check bundle size:**

```bash
cd packages/frontend-2
yarn build
# Check .output/public/_nuxt/ for file sizes
```

**Optimize:**

- Enable code splitting (already in nuxt.config.ts)
- Lazy load heavy components
- Tree-shake unused dependencies

#### 3. **GraphQL Code Generation**

**Issue:** GraphQL codegen watches and regenerates types on every schema change

**Solution:** Run codegen only when needed:

```bash
# Instead of watch mode, regenerate manually
yarn gqlgen
```

#### 4. **TypeScript Compilation**

**Issue:** TypeScript checking on every save

**Solutions:**

- Disable strict type checking in dev:

  ```json
  // tsconfig.json (dev mode)
  {
    "compilerOptions": {
      "noEmit": true,
      "incremental": true
    }
  }
  ```

- Use `skipLibCheck: true` for faster builds

#### 5. **File Watching Issues (Windows)**

**Issue:** Windows file watchers can be slow with large codebases

**Solutions:**

- Exclude `node_modules` from watching:

  ```typescript
  // nuxt.config.ts
  vite: {
    server: {
      watch: {
        ignored: ['**/node_modules/**', '**/dist/**']
      }
    }
  }
  ```

- Increase Node.js file watcher limit:
  ```bash
  # Windows PowerShell
  $env:NODE_OPTIONS="--max-old-space-size=4096"
  ```

#### 6. **Memory Issues**

**Issue:** Development servers use more memory

**Solutions:**

- Increase Node.js memory:

  ```bash
  NODE_OPTIONS=--max-old-space-size=8192 yarn dev
  ```

- Close unnecessary browser tabs/extensions
- Restart dev servers periodically

### Production Performance Optimizations

#### Frontend Optimizations:

```typescript
// nuxt.config.ts additions
export default defineNuxtConfig({
  // Enable compression
  nitro: {
    compressPublicAssets: true,
    minify: true,
    prerender: {
      // Pre-render common routes
      routes: ['/']
    }
  },

  // Optimize images
  image: {
    quality: 80,
    format: ['webp', 'avif']
  },

  // Enable caching
  routeRules: {
    '/**': {
      headers: {
        'Cache-Control': 'public, max-age=31536000, immutable'
      }
    }
  }
})
```

#### Server Optimizations:

```typescript
// Server optimizations
- Enable connection pooling for PostgreSQL
- Use Redis caching for frequently accessed data
- Enable gzip compression
- Use CDN for static assets
```

### Quick Performance Check Commands

```bash
# Check bundle sizes
cd packages/frontend-2
yarn build
du -sh .output/public/_nuxt/*

# Analyze bundle
yarn analyze

# Check server startup time
cd packages/server
time yarn dev

# Monitor memory usage
node --trace-warnings --max-old-space-size=8192 run.ts
```

---

## Recommended Distribution Strategy

### For Technical Clients (Docker Experience):

**→ Use Docker Compose** - Most flexible, easy to update

### For Non-Technical Clients:

**→ Use Electron/Tauri Desktop App** - One-click install, hides complexity

### For Quick Demos/Prototypes:

**→ Use Portable Distribution** - No installation, just run

### For Enterprise/Cloud:

**→ Use Pre-built Docker Images** - Deploy to their infrastructure

---

## Next Steps

1. **Choose your distribution method** based on client needs
2. **Create production builds** and test performance
3. **Package with appropriate tooling** (Docker Compose, Electron, etc.)
4. **Create user documentation** for your chosen method
5. **Set up CI/CD** to automate builds and distribution

---

## Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Electron Documentation](https://www.electronjs.org/docs)
- [Tauri Documentation](https://tauri.app/)
- [Nuxt Performance Guide](https://nuxt.com/docs/getting-started/performance)
- [Vite Performance Optimization](https://vitejs.dev/guide/performance.html)




