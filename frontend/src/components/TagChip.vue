<script setup>
import { computed } from 'vue'
import { stringToHslColor } from '@/utils/stringToHslColor'

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
  to: {
    type: [String, Object],
    default: null,
  },
  active: {
    type: Boolean,
    default: false,
  },
})

const color = computed(() => stringToHslColor(props.name))
const textColor = computed(() => {
  const hue = parseInt(stringToHslColor(props.name).match(/\d+/)[0])
  return `hsl(${hue}, 60%, 30%)`
})

const ringColorClass = computed(() => {
  if (!props.active) return ''
  const hue = parseInt(stringToHslColor(props.name).match(/\d+/)[0])
  // Map hue to nearest Tailwind color
  if (hue < 15 || hue >= 345) return 'ring-red-300'
  if (hue < 45) return 'ring-orange-300'
  if (hue < 60) return 'ring-amber-300'
  if (hue < 75) return 'ring-yellow-300'
  if (hue < 90) return 'ring-lime-300'
  if (hue < 105) return 'ring-green-300'
  if (hue < 135) return 'ring-emerald-300'
  if (hue < 165) return 'ring-teal-300'
  if (hue < 195) return 'ring-cyan-300'
  if (hue < 225) return 'ring-sky-300'
  if (hue < 255) return 'ring-blue-300'
  if (hue < 275) return 'ring-indigo-300'
  if (hue < 315) return 'ring-violet-300'
  return 'ring-purple-300'
})
</script>

<template>
  <component
    :is="to ? 'router-link' : 'span'"
    :to="to"
    class="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-base font-semibold transition-colors hover:opacity-80"
    :class="[active ? 'ring-2 ring-offset-1' : '', ringColorClass]"
    :style="{
      backgroundColor: color,
      color: textColor,
    }"
  >
    #{{ name }}
  </component>
</template>
