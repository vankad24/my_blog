<script setup>
import { computed } from 'vue'
import { stringToHue } from '@/utils/stringFunctions'

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

const hue = computed(() => stringToHue(props.name))
const color = computed(() => `hsl(${hue.value}, 80%, 90%)`)
const textColor = computed(() => `hsl(${hue.value}, 60%, 30%)`)

const ringColorClass = computed(() => {
  if (!props.active) return ''
  const h = hue.value
  // Map hue to nearest Tailwind color
  if (h < 15 || h >= 345) return 'ring-red-300'
  if (h < 45) return 'ring-orange-300'
  if (h < 60) return 'ring-amber-300'
  if (h < 75) return 'ring-yellow-300'
  if (h < 90) return 'ring-lime-300'
  if (h < 105) return 'ring-green-300'
  if (h < 135) return 'ring-emerald-300'
  if (h < 165) return 'ring-teal-300'
  if (h < 195) return 'ring-cyan-300'
  if (h < 225) return 'ring-sky-300'
  if (h < 255) return 'ring-blue-300'
  if (h < 275) return 'ring-indigo-300'
  if (h < 315) return 'ring-violet-300'
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
