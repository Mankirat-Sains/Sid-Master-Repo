# SkyCiv Demo - Structural Analysis Viewer

A complete demo application that loads SkyCiv structural models, runs analysis via the SkyCiv API, and visualizes results in a 3D viewer.

## Project Structure

```
skyciv-demo/
├── backend/              # FastAPI service
│   ├── main.py          # API server
│   ├── skyciv_client.py # SkyCiv API client
│   └── requirements.txt
├── frontend/            # Vue components
│   ├── SkyCivViewer.vue # 3D viewer component
│   └── useSkyCiv.ts    # API composable
├── models/             # SkyCiv model files
│   ├── script1.json
│   └── script2.json
└── README.md
```

## Features

- ✅ Load SkyCiv model files (JSON format)
- ✅ Connect to SkyCiv API v3
- ✅ Run structural analysis (linear, nonlinear, etc.)
- ✅ 3D visualization with Three.js
- ✅ Interactive viewer with orbit controls
- ✅ Display analysis results

## Setup

### Backend Setup

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure credentials:**
The backend uses hardcoded credentials by default:
- Username: `admin@sidian.ai`
- API Key: `RxqSvo6QGRGphKlaLM2QcBKJqL1D4GXtFJLYMmt3cESAj82bjMTsCgkODJKHR88u`

To use environment variables, create a `.env` file:
```env
SKYCIV_USERNAME=your_email@example.com
SKYCIV_API_KEY=your_api_key
```

3. **Run the server:**
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Integration

The frontend components can be integrated into your Nuxt application:

1. **Copy components:**
   - Copy `SkyCivViewer.vue` to `Frontend/Frontend/components/`
   - Copy `useSkyCiv.ts` to `Frontend/Frontend/composables/`

2. **Install Three.js:**
```bash
cd Frontend/Frontend
npm install three
npm install --save-dev @types/three
```

3. **Install OrbitControls:**
```bash
npm install three
```

4. **Add environment variable** (optional):
Create or update `.env` in your Frontend directory:
```env
VITE_SKYCIV_API_URL=http://localhost:8000
```

5. **Use in a page:**
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

## API Endpoints

### GET `/models`
List available model files.

**Response:**
```json
{
  "models": [
    {
      "name": "script1",
      "description": "SkyCiv Model 1",
      "node_count": 150,
      "member_count": 200,
      "units": {...}
    }
  ]
}
```

### POST `/analyze`
Run analysis on a model.

**Request:**
```json
{
  "model_name": "script1",
  "analysis_type": "linear"
}
```

**Response:**
```json
{
  "session_id": "abc123...",
  "model_name": "script1",
  "status": "success",
  "results": {...},
  "visualization_data": {
    "nodes": [...],
    "members": [...],
    "forces": {...},
    "displacements": {...}
  }
}
```

### GET `/model/{model_name}`
Get detailed information about a specific model.

### GET `/health`
Health check endpoint.

## Usage Flow

1. **Start backend server:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Open frontend:**
   - The viewer component will automatically load available models
   - Select a model from the dropdown
   - Click "Run Analysis"
   - View the 3D model and results

## SkyCiv API Integration

The demo uses the SkyCiv API v3 workflow:

1. **Start Session:** `S3D.session.start`
2. **Set Model:** `S3D.model.set` (with your model JSON)
3. **Solve:** `S3D.model.solve`
4. **Get Results:** `S3D.results.get`

All API calls include authentication:
```json
{
  "auth": {
    "username": "admin@sidian.ai",
    "key": "RxqSvo6QGRGphKlaLM2QcBKJqL1D4GXtFJLYMmt3cESAj82bjMTsCgkODJKHR88u"
  }
}
```

## 3D Viewer Features

- **Interactive Controls:** Orbit, pan, zoom
- **Visualization:**
  - Green spheres for nodes
  - Blue cylinders for members
  - Grid and axes helpers
- **Auto-fit:** Camera automatically frames the model
- **Supports:** Both Y-up and Z-up coordinate systems

## Troubleshooting

### Backend Issues

- **Connection errors:** Verify SkyCiv API credentials
- **Model loading errors:** Check that model files exist in `models/` directory
- **Analysis failures:** Check SkyCiv API response for error messages

### Frontend Issues

- **Three.js errors:** Ensure Three.js and OrbitControls are installed
- **API connection:** Verify `VITE_SKYCIV_API_URL` points to running backend
- **Viewer not showing:** Check browser console for errors

## Next Steps

- Add result visualization (forces, displacements)
- Implement parametric model updates
- Add load case selection
- Export results to PDF/Excel
- Integrate with IFC/Speckle import

## References

- [SkyCiv API Documentation](https://platform.skyciv.com/api/v3)
- [SkyCiv S3D Model Docs](https://skyciv.com/api/v3/docs/S3D.model)
- [Three.js Documentation](https://threejs.org/docs/)

