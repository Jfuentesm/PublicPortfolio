<template>
  <div class="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
    <h5 class="text-lg font-semibold text-gray-800 mb-4">Classification Results</h5>

    <!-- Search Input -->
    <div class="mb-4">
      <label for="results-search" class="sr-only">Search Results</label>
      <input
        type="text"
        id="results-search"
        v-model="searchTerm"
        placeholder="Search by Vendor Name or NAICS..."
        class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="text-center py-5 text-gray-500">
      <svg class="animate-spin h-6 w-6 text-primary mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="mt-2 text-sm">Loading results...</p>
    </div>
    <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
      Error loading results: {{ error }}
    </div>
    <div v-else-if="!results || results.length === 0" class="text-center py-5 text-gray-500">
      No results found for this job.
    </div>

    <!-- Results Table -->
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200 border border-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <th scope="col" @click="sortBy('vendor_name')" class="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-200">
              Vendor Name <SortIcon :direction="sortKey === 'vendor_name' ? sortDirection : null" />
            </th>
            <th scope="col" @click="sortBy('naics_code')" class="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-200">
              NAICS Code <SortIcon :direction="sortKey === 'naics_code' ? sortDirection : null" />
            </th>
            <th scope="col" @click="sortBy('naics_name')" class="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-200">
              NAICS Name <SortIcon :direction="sortKey === 'naics_name' ? sortDirection : null" />
            </th>
            <th scope="col" @click="sortBy('confidence')" class="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-200">
              Confidence <SortIcon :direction="sortKey === 'confidence' ? sortDirection : null" />
            </th>
            <th scope="col" @click="sortBy('source')" class="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-200">
              Source <SortIcon :direction="sortKey === 'source' ? sortDirection : null" />
            </th>
            <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
              Notes / Reason
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="filteredAndSortedResults.length === 0">
            <td colspan="6" class="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-center">No results match your search.</td>
          </tr>
          <tr v-for="item in filteredAndSortedResults" :key="item.vendor_name" class="hover:bg-gray-50">
            <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.vendor_name }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 font-mono">{{ item.naics_code || 'N/A' }}</td>
            <td class="px-4 py-3 text-sm text-gray-700">{{ item.naics_name || 'N/A' }}</td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
              <span v-if="item.confidence !== null && item.confidence !== undefined"
                    :class="getConfidenceClass(item.confidence)">
                {{ (item.confidence * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-gray-400">N/A</span>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="item.source === 'Search' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'">
                {{ item.source }}
              </span>
            </td>
            <td class="px-4 py-3 text-xs text-gray-500 max-w-xs break-words">
              {{ item.notes || item.reason || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination (Optional - Simple example) -->
    <!-- <div class="mt-4 flex justify-between items-center">
      <span class="text-sm text-gray-700">Showing X to Y of Z results</span>
      <div class="space-x-1">
        <button class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-100 disabled:opacity-50" disabled>Previous</button>
        <button class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-100">Next</button>
      </div>
    </div> -->

  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import type { JobResultItem } from '@/stores/job'; // Assuming interface defined in store
import { ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon } from '@heroicons/vue/20/solid';

// --- Props ---
const props = defineProps({
  results: {
    type: Array as PropType<JobResultItem[] | null>,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String as PropType<string | null>,
    default: null,
  },
});

// --- Internal State ---
const searchTerm = ref('');
const sortKey = ref<keyof JobResultItem | null>(null); // Key to sort by
const sortDirection = ref<'asc' | 'desc' | null>(null); // Sort direction

// --- Computed Properties ---

const filteredAndSortedResults = computed(() => {
  if (!props.results) return [];

  let filtered = props.results;

  // Filtering
  if (searchTerm.value) {
    const lowerSearchTerm = searchTerm.value.toLowerCase();
    filtered = filtered.filter(item =>
      item.vendor_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.naics_code?.toLowerCase().includes(lowerSearchTerm) ||
      item.naics_name?.toLowerCase().includes(lowerSearchTerm)
    );
  }

  // Sorting
  if (sortKey.value && sortDirection.value) {
    const key = sortKey.value;
    const direction = sortDirection.value === 'asc' ? 1 : -1;

    filtered.sort((a, b) => {
      const valA = a[key];
      const valB = b[key];

      if (valA === null || valA === undefined) return 1 * direction;
      if (valB === null || valB === undefined) return -1 * direction;

      if (typeof valA === 'string' && typeof valB === 'string') {
        return valA.localeCompare(valB) * direction;
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return (valA - valB) * direction;
      }
      // Fallback for other types or mixed types (simple comparison)
      if (valA < valB) return -1 * direction;
      if (valA > valB) return 1 * direction;
      return 0;
    });
  }

  return filtered;
});

// --- Methods ---

function sortBy(key: keyof JobResultItem) {
  if (sortKey.value === key) {
    // Cycle direction: asc -> desc -> null (no sort)
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : null;
    if (sortDirection.value === null) {
        sortKey.value = null; // Clear key if sort is disabled
    }
  } else {
    // Start new sort
    sortKey.value = key;
    sortDirection.value = 'asc';
  }
}

function getConfidenceClass(confidence: number | null | undefined): string {
  if (confidence === null || confidence === undefined) return 'text-gray-400';
  if (confidence >= 0.8) return 'text-green-700 font-medium';
  if (confidence >= 0.5) return 'text-yellow-700';
  return 'text-red-700';
}

// --- Helper Component for Sort Icons ---
const SortIcon = {
  props: {
    direction: {
      type: String as PropType<'asc' | 'desc' | null>,
      default: null,
    },
  },
  components: { ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon },
  template: `
    <span class="inline-block ml-1 w-4 h-4 align-middle">
      <ChevronUpIcon v-if="direction === 'asc'" class="w-4 h-4 text-gray-700" />
      <ChevronDownIcon v-else-if="direction === 'desc'" class="w-4 h-4 text-gray-700" />
      <ChevronUpDownIcon v-else class="w-4 h-4 text-gray-400" />
    </span>
  `,
};

</script>

<style scoped>
/* Add any specific styles if needed */
th {
  user-select: none; /* Prevent text selection on header click */
}
</style>