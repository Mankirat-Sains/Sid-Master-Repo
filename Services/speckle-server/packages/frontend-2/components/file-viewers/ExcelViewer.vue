<template>
  <div class="flex flex-col h-full">
    <!-- Excel Controls -->
    <div
      v-if="sheets.length > 0"
      class="flex items-center justify-between p-4 border-b border-outline-3"
    >
      <div class="flex items-center gap-2">
        <label class="text-body-sm mr-2">Sheet:</label>
        <select
          v-model="selectedSheet"
          class="px-3 py-1 rounded border border-outline-3 bg-foundation-2 text-foreground text-body-sm"
          @change="loadSheet"
        >
          <option v-for="(sheet, index) in sheets" :key="index" :value="index">
            {{ sheet }}
          </option>
        </select>
      </div>
    </div>

    <!-- Excel Table Container -->
    <div class="flex-1 overflow-auto bg-foundation-3 p-4">
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="size-8 animate-spin mx-auto mb-2 text-foreground-2" />
          <p class="text-body-sm text-foreground-2">Loading Excel file...</p>
        </div>
      </div>
      <div v-else-if="error" class="flex items-center justify-center h-full">
        <div class="text-center">
          <TriangleAlert class="size-8 mx-auto mb-2 text-danger" />
          <p class="text-body-sm text-foreground-2">{{ error }}</p>
        </div>
      </div>
      <div
        v-else-if="data.length === 0"
        class="flex items-center justify-center h-full"
      >
        <p class="text-body-sm text-foreground-2">No data available</p>
      </div>
      <div v-else class="overflow-auto max-h-full">
        <table
          class="min-w-full border-collapse border border-outline-3 bg-foundation-2"
        >
          <thead>
            <tr>
              <th
                v-for="(header, colIndex) in headers"
                :key="colIndex"
                class="border border-outline-3 px-4 py-2 text-left text-body-sm font-medium bg-foundation-3 sticky top-0"
              >
                {{ header || `Column ${colIndex + 1}` }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, rowIndex) in data"
              :key="rowIndex"
              :class="rowIndex % 2 === 0 ? 'bg-foundation-2' : 'bg-foundation-3'"
            >
              <td
                v-for="(cell, colIndex) in row"
                :key="colIndex"
                class="border border-outline-3 px-4 py-2 text-body-sm text-foreground"
              >
                {{ formatCell(cell) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Loader2, TriangleAlert } from 'lucide-vue-next'

// Dynamically import XLSX only on client side to avoid SSR issues
let XLSX: typeof import('xlsx') | null = null
const isClient = typeof window !== 'undefined'

const props = defineProps<{
  url: string
}>()

const loading = ref(true)
const error = ref<string | null>(null)
const workbook = ref<any>(null)
const sheets = ref<string[]>([])
const selectedSheet = ref(0)
const headers = ref<string[]>([])
const data = ref<(string | number)[][]>([])

const formatCell = (value: any): string => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number') {
    // Format numbers with commas for thousands
    if (Number.isInteger(value)) {
      return value.toLocaleString()
    }
    return value.toFixed(2)
  }
  return String(value)
}

const loadExcel = async () => {
  if (!isClient) return

  try {
    loading.value = true
    error.value = null

    // Ensure XLSX is loaded
    if (!XLSX) {
      XLSX = await import('xlsx')
    }

    const response = await fetch(props.url)
    if (!response.ok) {
      throw new Error(`Failed to fetch Excel file: ${response.statusText}`)
    }

    const arrayBuffer = await response.arrayBuffer()
    const wb = XLSX.read(arrayBuffer, { type: 'array' })
    workbook.value = wb

    sheets.value = wb.SheetNames
    selectedSheet.value = 0

    loadSheet()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load Excel file'
    console.error('Excel loading error:', err)
  } finally {
    loading.value = false
  }
}

const loadSheet = () => {
  if (!workbook.value || !XLSX || sheets.value.length === 0) return

  try {
    const sheetName = sheets.value[selectedSheet.value]
    const worksheet = workbook.value.Sheets[sheetName]

    if (!worksheet) {
      error.value = `Sheet "${sheetName}" not found`
      return
    }

    // Convert to JSON array format
    const jsonData = XLSX.utils.sheet_to_json(worksheet, {
      header: 1,
      defval: ''
    }) as (string | number)[][]

    if (jsonData.length === 0) {
      headers.value = []
      data.value = []
      return
    }

    // First row as headers
    headers.value = (jsonData[0] || []).map((cell) => String(cell || ''))
    // Rest as data
    data.value = jsonData.slice(1)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load sheet'
    console.error('Excel sheet loading error:', err)
  }
}

watch(() => props.url, loadExcel)

onMounted(() => {
  if (isClient) {
    loadExcel()
  }
})
</script>
