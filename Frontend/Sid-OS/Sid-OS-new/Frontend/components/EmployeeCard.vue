<template>
  <div
    class="bg-white/90 backdrop-blur-xl border border-gray-200 rounded-2xl p-6 cursor-pointer transition-all hover:shadow-xl hover:scale-[1.02] shadow-xl"
    @click="$emit('click')"
  >
    <!-- Header -->
    <div class="mb-4">
      <h3 class="text-lg font-semibold text-gray-900">{{ employee.name }}</h3>
      <span class="inline-block mt-2 px-2 py-1 text-xs rounded-lg bg-gray-100 text-gray-600">
        {{ employee.role }}
      </span>
    </div>

    <!-- Hours Display -->
    <div class="mb-4">
      <p class="text-sm text-gray-500">{{ getHoursLabel() }}</p>
      <p class="text-2xl font-bold text-gray-900">{{ employee.weeklyHours }}h</p>
    </div>

    <!-- Pie Chart (Vue version of v0 donut chart) -->
    <div class="mb-4 flex items-center justify-center h-48">
      <svg
        viewBox="0 0 100 100"
        class="w-full h-full max-h-48"
        aria-hidden="true"
      >
        <g transform="translate(50,50)">
          <path
            v-for="(slice, index) in slices"
            :key="index"
            :d="slice.d"
            :fill="slice.color"
          />
          <!-- Inner hole for donut effect -->
          <circle
            cx="0"
            cy="0"
            r="22"
            class="fill-white"
          />
        </g>
      </svg>
    </div>

    <!-- Breakdown List -->
    <div class="space-y-2">
      <div
        v-for="(item, index) in employee.weeklyBreakdown.slice(0, 3)"
        :key="index"
        class="flex items-center justify-between text-sm"
      >
        <div class="flex items-center gap-2">
          <div
            class="h-3 w-3 rounded-sm"
            :style="{ backgroundColor: COLORS[index % COLORS.length] }"
          />
          <span class="text-gray-500">{{ item.name }}</span>
        </div>
        <span class="font-medium text-gray-900">{{ item.value }}h</span>
      </div>
      <div
        v-if="employee.weeklyBreakdown.length > 3"
        class="text-xs text-gray-500 text-center pt-2"
      >
        +{{ employee.weeklyBreakdown.length - 3 }} more
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Employee } from '~/data/employees'

interface Props {
  employee: Employee & { weeklyHours: number; weeklyBreakdown: Array<{ name: string; value: number }> }
  timeScale?: 'weekly' | 'monthly' | 'yearly'
}

defineEmits<{
  click: []
}>()

const COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Green
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#8b5cf6', // Purple
  '#ec4899', // Pink
]

const props = defineProps<Props>()

const slices = computed(() => {
  const total = props.employee.weeklyBreakdown.reduce((sum, item) => sum + item.value, 0)
  if (!total) return []

  let startAngle = 0
  const radius = 40

  return props.employee.weeklyBreakdown.map((item, index) => {
    const angle = (item.value / total) * Math.PI * 2
    const endAngle = startAngle + angle
    const d = describeArc(0, 0, radius, (startAngle * 180) / Math.PI, (endAngle * 180) / Math.PI)
    const slice = {
      d,
      color: COLORS[index % COLORS.length],
    }
    startAngle = endAngle
    return slice
  })
})

function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  }
}

function describeArc(x: number, y: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(x, y, radius, endAngle)
  const end = polarToCartesian(x, y, radius, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'

  return [
    'M',
    start.x,
    start.y,
    'A',
    radius,
    radius,
    0,
    largeArcFlag,
    0,
    end.x,
    end.y,
    'L',
    x,
    y,
    'Z',
  ].join(' ')
}

function getHoursLabel() {
  const timeScale = props.timeScale || 'weekly'
  switch (timeScale) {
    case 'monthly':
      return 'Monthly Hours'
    case 'yearly':
      return 'Yearly Hours'
    default:
      return 'Weekly Hours'
  }
}
</script>

