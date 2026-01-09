<template>
  <div class="skyciv-viewer-container bg-[#1a1a1a] rounded-lg overflow-hidden border border-[#3a3a3a]">
    <!-- Header with Model Selection -->
    <div class="p-4 border-b border-[#3a3a3a] bg-[#2a2a2a]">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-white font-semibold text-lg">SkyCiv Structural Analysis</h3>
        <button
          v-if="results"
          @click="resetViewer"
          class="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 rounded text-white"
        >
          Reset
        </button>
      </div>
      
      <div class="flex gap-2 items-center">
        <select
          v-model="selectedModel"
          :disabled="loading"
          class="px-3 py-2 bg-[#1a1a1a] border border-[#3a3a3a] rounded text-white text-sm focus:outline-none focus:border-blue-500"
        >
          <option value="" disabled>Select a model...</option>
          <option v-for="model in availableModels" :key="model.name" :value="model.name">
            {{ model.description }} ({{ model.node_count }} nodes, {{ model.member_count }} members)
          </option>
        </select>
        
        <button
          @click="analyzeModel"
          :disabled="loading || !selectedModel"
          class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded text-white font-medium text-sm"
        >
          {{ loading ? "Analyzing..." : "Run Analysis" }}
        </button>
      </div>
      
      <div v-if="error" class="mt-2 p-2 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">
        {{ error }}
      </div>
    </div>

    <!-- 3D Viewer -->
    <div ref="viewerContainer" class="viewer-canvas" :style="{ height: height }"></div>

    <!-- Results Panel -->
    <div v-if="results" class="p-4 border-t border-[#3a3a3a] bg-[#2a2a2a]">
      <h3 class="text-white font-semibold mb-3">Analysis Results</h3>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-gray-400">Model:</span>
          <span class="text-white ml-2">{{ results.model_name }}</span>
        </div>
        <div>
          <span class="text-gray-400">Status:</span>
          <span class="text-green-400 ml-2">{{ results.status }}</span>
        </div>
        <div class="col-span-2">
          <span class="text-gray-400">Session ID:</span>
          <span class="text-white ml-2 font-mono text-xs">{{ results.session_id }}</span>
        </div>
      </div>
      
      <div v-if="visualizationData.nodes" class="mt-3 text-sm text-gray-400">
        Visualizing {{ visualizationData.nodes.length }} nodes and {{ visualizationData.members.length }} members
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { useSkyCiv } from './useSkyCiv'

const props = defineProps<{
  height?: string
}>()

const height = props.height || '600px'
const selectedModel = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const results = ref<any>(null)
const visualizationData = ref<any>({})
const availableModels = ref<any[]>([])
const viewerContainer = ref<HTMLElement | null>(null)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let animationFrameId: number | null = null
let isDragging = false
let previousMousePosition = { x: 0, y: 0 }

const { listModels, analyzeModel: analyzeModelAPI } = useSkyCiv()

onMounted(async () => {
  initViewer()
  await loadAvailableModels()
})

onUnmounted(() => {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
  }
  // Cleanup event listeners
  if (renderer && (renderer.domElement as any).__cleanupControls) {
    (renderer.domElement as any).__cleanupControls()
  }
  
  if (renderer) {
    renderer.dispose()
  }
  
  window.removeEventListener('resize', onWindowResize)
})

async function loadAvailableModels() {
  try {
    const models = await listModels()
    availableModels.value = models
  } catch (err) {
    console.error('Failed to load models:', err)
    error.value = 'Failed to load available models'
  }
}

function initViewer() {
  if (!viewerContainer.value) return

  // Scene setup
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a1a)

  // Camera
  const aspect = viewerContainer.value.clientWidth / parseInt(height)
  camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 10000)
  camera.position.set(50, 50, 50)
  camera.lookAt(0, 0, 0)

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(viewerContainer.value.clientWidth, parseInt(height))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  viewerContainer.value.appendChild(renderer.domElement)

  // Simple mouse controls for rotation and zoom
  const handleMouseDown = (e: MouseEvent) => {
    isDragging = true
    previousMousePosition = { x: e.clientX, y: e.clientY }
  }
  
  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return
    
    const deltaX = e.clientX - previousMousePosition.x
    const deltaY = e.clientY - previousMousePosition.y
    
    // Simple rotation using spherical coordinates
    const spherical = new THREE.Spherical()
    spherical.setFromVector3(camera.position)
    spherical.theta -= deltaX * 0.01
    spherical.phi += deltaY * 0.01
    spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi))
    
    camera.position.setFromSpherical(spherical)
    camera.lookAt(0, 0, 0)
    
    previousMousePosition = { x: e.clientX, y: e.clientY }
  }
  
  const handleMouseUp = () => {
    isDragging = false
  }
  
  const handleWheel = (e: WheelEvent) => {
    e.preventDefault()
    const scale = e.deltaY > 0 ? 1.1 : 0.9
    camera.position.multiplyScalar(scale)
  }
  
  renderer.domElement.addEventListener('mousedown', handleMouseDown)
  renderer.domElement.addEventListener('mousemove', handleMouseMove)
  renderer.domElement.addEventListener('mouseup', handleMouseUp)
  renderer.domElement.addEventListener('wheel', handleWheel)
  
  // Store cleanup function
  const cleanupControls = () => {
    renderer.domElement.removeEventListener('mousedown', handleMouseDown)
    renderer.domElement.removeEventListener('mousemove', handleMouseMove)
    renderer.domElement.removeEventListener('mouseup', handleMouseUp)
    renderer.domElement.removeEventListener('wheel', handleWheel)
  }
  
  // Store cleanup for later
  ;(renderer.domElement as any).__cleanupControls = cleanupControls

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(50, 50, 50)
  directionalLight.castShadow = true
  directionalLight.shadow.mapSize.width = 2048
  directionalLight.shadow.mapSize.height = 2048
  scene.add(directionalLight)

  // Grid helper
  const gridHelper = new THREE.GridHelper(200, 20, 0x444444, 0x222222)
  scene.add(gridHelper)

  // Axes helper
  const axesHelper = new THREE.AxesHelper(20)
  scene.add(axesHelper)

  // Handle window resize
  window.addEventListener('resize', onWindowResize)

  animate()
}

function onWindowResize() {
  if (!viewerContainer.value || !camera || !renderer) return
  
  const width = viewerContainer.value.clientWidth
  const heightValue = parseInt(height)
  
  camera.aspect = width / heightValue
  camera.updateProjectionMatrix()
  renderer.setSize(width, heightValue)
}

function animate() {
  animationFrameId = requestAnimationFrame(animate)
  
  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

async function analyzeModel() {
  if (!selectedModel.value || loading.value) return

  loading.value = true
  error.value = null
  
  try {
    const response = await analyzeModelAPI(selectedModel.value)
    
    if (response.status === 'error') {
      error.value = response.error || 'Analysis failed'
      return
    }
    
    results.value = response
    visualizationData.value = response.visualization_data || {}
    
    // Visualize the model
    visualizeModel(visualizationData.value)
    
  } catch (err: any) {
    console.error('Analysis error:', err)
    error.value = err.message || 'Failed to analyze structure'
  } finally {
    loading.value = false
  }
}

function visualizeModel(data: any) {
  if (!scene || !data.nodes || !data.members) return

  // Clear existing geometry
  const objectsToRemove: THREE.Object3D[] = []
  scene.traverse((obj) => {
    if (obj instanceof THREE.Mesh || obj instanceof THREE.Line) {
      if (obj.userData.isModelElement) {
        objectsToRemove.push(obj)
      }
    }
  })
  objectsToRemove.forEach((obj) => {
    if (obj instanceof THREE.Mesh) {
      obj.geometry.dispose()
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose())
      } else {
        obj.material.dispose()
      }
    } else if (obj instanceof THREE.Line) {
      obj.geometry.dispose()
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose())
      } else {
        obj.material.dispose()
      }
    }
    scene.remove(obj)
  })

  // Determine vertical axis (Y or Z)
  const verticalAxis = data.vertical_axis || 'Y'
  const isYUp = verticalAxis === 'Y'

  // Create node spheres
  const nodeGeometry = new THREE.SphereGeometry(0.5, 16, 16)
  const nodeMaterial = new THREE.MeshPhongMaterial({ 
    color: 0x00ff00,
    emissive: 0x002200
  })
  const nodes: { [key: string]: THREE.Mesh } = {}

  data.nodes.forEach((node: any) => {
    const sphere = new THREE.Mesh(nodeGeometry, nodeMaterial)
    
    if (isYUp) {
      sphere.position.set(node.x, node.y, node.z)
    } else {
      // Z-up to Y-up conversion
      sphere.position.set(node.x, node.z, node.y)
    }
    
    sphere.userData.isModelElement = true
    nodes[node.id] = sphere
    scene.add(sphere)
  })

  // Create member lines/cylinders
  const memberMaterial = new THREE.MeshPhongMaterial({ 
    color: 0x00aaff,
    emissive: 0x001122
  })
  
  data.members.forEach((member: any) => {
    const startNode = nodes[member.start]
    const endNode = nodes[member.end]
    
    if (startNode && endNode) {
      // Create cylinder for member
      const start = startNode.position
      const end = endNode.position
      const length = start.distanceTo(end)
      
      if (length > 0.01) {
        const cylinderGeometry = new THREE.CylinderGeometry(0.3, 0.3, length, 16)
        const cylinder = new THREE.Mesh(cylinderGeometry, memberMaterial)
        cylinder.userData.isModelElement = true
        
        // Position and orient cylinder
        const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5)
        cylinder.position.copy(midPoint)
        
        // Orient cylinder to point from start to end
        const direction = new THREE.Vector3().subVectors(end, start).normalize()
        const up = new THREE.Vector3(0, 1, 0)
        const quaternion = new THREE.Quaternion().setFromUnitVectors(up, direction)
        cylinder.quaternion.copy(quaternion)
        
        scene.add(cylinder)
      }
    }
  })

  // Update camera to fit model
  if (data.nodes.length > 0) {
    const positions = data.nodes.map((n: any) => {
      if (isYUp) {
        return new THREE.Vector3(n.x, n.y, n.z)
      } else {
        return new THREE.Vector3(n.x, n.z, n.y)
      }
    })
    
    const box = new THREE.Box3().setFromPoints(positions)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())
    const maxDim = Math.max(size.x, size.y, size.z)
    
    if (maxDim > 0) {
      const distance = maxDim * 2
      camera.position.set(
        center.x + distance * 0.7,
        center.y + distance * 0.7,
        center.z + distance * 0.7
      )
      camera.lookAt(center)
      
      // Camera is already positioned and looking at center
    }
  }
}

function resetViewer() {
  results.value = null
  visualizationData.value = {}
  selectedModel.value = ''
  error.value = null
  
  // Clear model geometry
  const objectsToRemove: THREE.Object3D[] = []
  scene.traverse((obj) => {
    if (obj instanceof THREE.Mesh || obj instanceof THREE.Line) {
      if (obj.userData.isModelElement) {
        objectsToRemove.push(obj)
      }
    }
  })
  objectsToRemove.forEach((obj) => {
    if (obj instanceof THREE.Mesh) {
      obj.geometry.dispose()
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose())
      } else {
        obj.material.dispose()
      }
    } else if (obj instanceof THREE.Line) {
      obj.geometry.dispose()
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose())
      } else {
        obj.material.dispose()
      }
    }
    scene.remove(obj)
  })
}
</script>

<style scoped>
.skyciv-viewer-container {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.viewer-canvas {
  flex: 1;
  position: relative;
  min-height: 400px;
}

.viewer-canvas canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>

