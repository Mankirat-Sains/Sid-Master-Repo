<template>
  <div class="flex items-center gap-2 bg-gray-100 rounded-xl p-1 backdrop-blur-sm">
    <button
      v-for="option in options"
      :key="option.value"
      @click="$emit('update:modelValue', option.value)"
      :class="[
        'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
        modelValue === option.value
          ? 'bg-blue-500 text-white shadow-md'
          : 'text-gray-600 hover:text-gray-900'
      ]"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
interface Option {
  value: 'weekly' | 'monthly' | 'yearly'
  label: string
}

const props = defineProps<{
  modelValue: 'weekly' | 'monthly' | 'yearly'
}>()

defineEmits<{
  'update:modelValue': [value: 'weekly' | 'monthly' | 'yearly']
}>()

const options: Option[] = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
]
</script>

