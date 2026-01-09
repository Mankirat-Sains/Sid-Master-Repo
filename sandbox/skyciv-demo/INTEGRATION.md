# Integration Guide

## Quick Start

### Backend (Standalone)

1. Navigate to backend directory:
```bash
cd sandbox/skyciv-demo/backend
```

2. Install and run:
```bash
./run.sh
# OR
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

3. Verify it's running:
- Open http://localhost:8000/health
- Check API docs at http://localhost:8000/docs

### Frontend (Nuxt Integration)

1. **Copy components to your Nuxt app:**
```bash
# From sandbox/skyciv-demo/frontend/
cp SkyCivViewer.vue /path/to/Frontend/Frontend/components/
cp useSkyCiv.ts /path/to/Frontend/Frontend/composables/
```

2. **Install Three.js:**
```bash
cd /path/to/Frontend/Frontend
npm install three
npm install --save-dev @types/three
```

3. **Create a page:**
Create `pages/skyciv-demo.vue`:
```vue
<template>
  <div class="container mx-auto p-4">
    <SkyCivViewer height="700px" />
  </div>
</template>

<script setup lang="ts">
import SkyCivViewer from '~/components/SkyCivViewer.vue'
</script>
```

4. **Set environment variable** (optional):
In your `.env` file:
```env
VITE_SKYCIV_API_URL=http://localhost:8000
```

5. **Run your Nuxt app:**
```bash
npm run dev
```

6. **Access the demo:**
Navigate to `http://localhost:3000/skyciv-demo` (or your Nuxt port)

## API Configuration

The backend uses hardcoded credentials by default. To change them:

1. Edit `backend/main.py`:
```python
skyciv_client = SkyCivClient(
    username=os.getenv("SKYCIV_USERNAME", "your_email@example.com"),
    api_key=os.getenv("SKYCIV_API_KEY", "your_api_key")
)
```

2. Or set environment variables:
```bash
export SKYCIV_USERNAME=your_email@example.com
export SKYCIV_API_KEY=your_api_key
```

## Model Files

Model files should be placed in:
```
sandbox/skyciv-demo/models/
├── script1.json
└── script2.json
```

The backend automatically detects JSON files in this directory and lists them via the `/models` endpoint.

## Troubleshooting

### Backend won't start
- Check Python version (3.8+)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check port 8000 is available

### Frontend can't connect
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings (backend allows all origins by default)
- Verify `VITE_SKYCIV_API_URL` matches backend URL

### Viewer not showing
- Check browser console for errors
- Verify Three.js is installed: `npm list three`
- Check that model files exist in `models/` directory

### SkyCiv API errors
- Verify credentials are correct
- Check SkyCiv API status
- Review API response in backend logs

## Development

### Backend Development
- Auto-reload enabled: `uvicorn main:app --reload`
- Logs show API calls and responses
- Check `/docs` for interactive API testing

### Frontend Development
- Component is self-contained
- Uses Vue 3 Composition API
- Three.js handles 3D rendering

## Next Steps

- Add result visualization (forces, displacements)
- Implement parametric updates
- Add export functionality
- Integrate with other Sidian systems

