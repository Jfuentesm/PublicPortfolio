<template>
  <div class="bg-white shadow rounded-lg p-4 flex items-center space-x-4">
    <div :class="['rounded-full p-3 flex items-center justify-center', iconBackgroundClass]">
      <component :is="iconComponent" class="h-6 w-6" :class="iconColorClass" />
    </div>
    <div>
      <p class="text-sm font-medium text-gray-500 truncate">{{ title }}</p>
      <p class="mt-1 text-2xl font-semibold" :class="valueClass">{{ formattedValue }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  UsersIcon,
  BriefcaseIcon,
  CogIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  CurrencyDollarIcon, // Example for cost
  QuestionMarkCircleIcon // Default
} from '@heroicons/vue/24/outline'; // Using outline icons

const props = defineProps<{
  title: string;
  value: number | string | null | undefined;
  icon: 'users' | 'briefcase' | 'cog' | 'exclamation-triangle' | 'check-circle' | 'currency-dollar' | string; // Allow known icons or string fallback
  error?: boolean; // Optional flag for error state styling
}>();

const formattedValue = computed(() => {
  if (props.value === null || props.value === undefined) {
    return 'N/A';
  }
  // Add formatting if needed (e.g., large numbers)
  return props.value.toLocaleString();
});

const iconComponent = computed(() => {
  switch (props.icon) {
    case 'users': return UsersIcon;
    case 'briefcase': return BriefcaseIcon;
    case 'cog': return CogIcon;
    case 'exclamation-triangle': return ExclamationTriangleIcon;
    case 'check-circle': return CheckCircleIcon;
    case 'currency-dollar': return CurrencyDollarIcon;
    default: return QuestionMarkCircleIcon;
  }
});

const baseIconBg = 'bg-indigo-100';
const errorIconBg = 'bg-red-100';
const baseIconColor = 'text-indigo-600';
const errorIconColor = 'text-red-600';

const iconBackgroundClass = computed(() => (props.error ? errorIconBg : baseIconBg));
const iconColorClass = computed(() => (props.error ? errorIconColor : baseIconColor));
const valueClass = computed(() => (props.error ? 'text-red-600' : 'text-gray-900'));

</script>