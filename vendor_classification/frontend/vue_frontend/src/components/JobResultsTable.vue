<template>
  <div class="mt-8 p-4 sm:p-6 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
    <h5 class="text-lg font-semibold text-gray-800 mb-4">Detailed Classification Results</h5>

    <!-- Search Input -->
    <div class="mb-4">
      <label for="results-search" class="sr-only">Search Results</label>
      <div class="relative rounded-md shadow-sm">
         <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon class="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
        <input
          type="text"
          id="results-search"
          v-model="searchTerm"
          placeholder="Search Vendor, Category, ID, Notes..."
          class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
        />
      </div>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="text-center py-5 text-gray-500">
      <svg class="animate-spin h-6 w-6 text-primary mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="mt-2 text-sm">Loading detailed results...</p>
    </div>
    <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
      Error loading results: {{ error }}
    </div>
    <div v-else-if="!results || results.length === 0" class="text-center py-5 text-gray-500">
      No detailed results found for this job.
    </div>

    <!-- Results Table -->
    <div v-else class="overflow-x-auto border border-gray-200 rounded-md">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <!-- Dynamically generate headers -->
            <th v-for="header in headers" :key="header.key"
                scope="col"
                @click="header.sortable ? sortBy(header.key) : null"
                :class="[
                  'px-3 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider',
                   header.sortable ? 'cursor-pointer hover:bg-gray-200' : '',
                   header.minWidth ? `min-w-[${header.minWidth}]` : ''
                ]">
              {{ header.label }}
              <SortIcon v-if="header.sortable" :direction="sortKey === header.key ? sortDirection : null" />
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="filteredAndSortedResults.length === 0">
            <td :colspan="headers.length" class="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-center">No results match your search criteria.</td>
          </tr>
          <tr v-for="(item, index) in filteredAndSortedResults" :key="item.vendor_name + '-' + index" class="hover:bg-gray-50 align-top">
            <td class="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.vendor_name }}</td>
            <!-- Level 1 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 1)">{{ item.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 1)">{{ item.level1_name || '-' }}</td>
            <!-- Level 2 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 2)">{{ item.level2_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 2)">{{ item.level2_name || '-' }}</td>
            <!-- Level 3 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 3)">{{ item.level3_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 3)">{{ item.level3_name || '-' }}</td>
            <!-- Level 4 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 4)">{{ item.level4_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 4)">{{ item.level4_name || '-' }}</td>
            <!-- Level 5 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 5)">{{ item.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 5)">{{ item.level5_name || '-' }}</td>
            <!-- Other columns -->
            <td class="px-3 py-2 whitespace-nowrap text-sm text-center">
              <span v-if="item.final_confidence !== null && item.final_confidence !== undefined"
                    :class="getConfidenceClass(item.final_confidence)">
                {{ (item.final_confidence * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-gray-400 text-xs">N/A</span>
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center">
               <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="getStatusClass(item.final_status)">
                {{ item.final_status }}
              </span>
            </td>
             <td class="px-3 py-2 whitespace-nowrap text-xs text-center">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="item.classification_source === 'Search' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'">
                {{ item.classification_source }}
              </span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-500 max-w-xs break-words">
              {{ item.classification_notes_or_reason || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

     <!-- Row Count -->
    <div class="mt-3 text-xs text-gray-500">
      Showing {{ filteredAndSortedResults.length }} of {{ results?.length || 0 }} results.
    </div>

    <!-- Pagination (Placeholder - Implement if needed for very large datasets) -->
    <!-- <div class="mt-4 flex justify-between items-center"> ... </div> -->

  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import type { JobResultItem } from '@/stores/job'; // Use the updated interface
import { ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon, MagnifyingGlassIcon } from '@heroicons/vue/20/solid';

// --- Define Header Interface ---
interface TableHeader {
  key: keyof JobResultItem; // Use keyof JobResultItem here
  label: string;
  sortable: boolean;
  minWidth?: string;
}
// --- END Define Header Interface ---

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
  targetLevel: { // Pass the job's target level
    type: Number,
    required: true,
  }
});

// --- Internal State ---
const searchTerm = ref('');
const sortKey = ref<keyof JobResultItem | null>('vendor_name'); // Default sort
const sortDirection = ref<'asc' | 'desc' | null>('asc'); // Default sort direction

// --- Table Headers Definition ---
// --- UPDATED: Apply TableHeader type ---
const headers = ref<TableHeader[]>([
  { key: 'vendor_name', label: 'Vendor Name', sortable: true, minWidth: '150px' },
  { key: 'level1_id', label: 'L1 ID', sortable: true, minWidth: '80px' },
  { key: 'level1_name', label: 'L1 Name', sortable: true, minWidth: '150px' },
  { key: 'level2_id', label: 'L2 ID', sortable: true, minWidth: '80px' },
  { key: 'level2_name', label: 'L2 Name', sortable: true, minWidth: '150px' },
  { key: 'level3_id', label: 'L3 ID', sortable: true, minWidth: '80px' },
  { key: 'level3_name', label: 'L3 Name', sortable: true, minWidth: '150px' },
  { key: 'level4_id', label: 'L4 ID', sortable: true, minWidth: '80px' },
  { key: 'level4_name', label: 'L4 Name', sortable: true, minWidth: '150px' },
  { key: 'level5_id', label: 'L5 ID', sortable: true, minWidth: '80px' },
  { key: 'level5_name', label: 'L5 Name', sortable: true, minWidth: '150px' },
  { key: 'final_confidence', label: 'Confidence', sortable: true, minWidth: '100px' },
  { key: 'final_status', label: 'Status', sortable: true, minWidth: '100px' },
  { key: 'classification_source', label: 'Source', sortable: true, minWidth: '80px' },
  { key: 'classification_notes_or_reason', label: 'Notes / Reason', sortable: false, minWidth: '200px' },
]);
// --- END UPDATED ---

// --- Computed Properties ---

const filteredAndSortedResults = computed(() => {
  if (!props.results) return [];

  let filtered = props.results;

  // Filtering (case-insensitive, searches across multiple relevant fields)
  if (searchTerm.value) {
    const lowerSearchTerm = searchTerm.value.toLowerCase();
    filtered = filtered.filter(item =>
      item.vendor_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level1_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level1_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level2_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level2_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level3_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level3_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level4_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level4_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level5_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level5_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.classification_notes_or_reason?.toLowerCase().includes(lowerSearchTerm) ||
      item.final_status?.toLowerCase().includes(lowerSearchTerm) ||
      item.classification_source?.toLowerCase().includes(lowerSearchTerm)
    );
  }

  // Sorting
  if (sortKey.value && sortDirection.value) {
    const key = sortKey.value;
    const direction = sortDirection.value === 'asc' ? 1 : -1;

    // Use slice() to avoid sorting the original array directly if it's reactive
    filtered = filtered.slice().sort((a, b) => {
      // Type assertion needed because TypeScript can't guarantee key is valid for both a and b
      const valA = a[key as keyof JobResultItem] as any;
      const valB = b[key as keyof JobResultItem] as any;

      // Handle null/undefined values consistently (e.g., push them to the end)
      const aIsNull = valA === null || valA === undefined || valA === '';
      const bIsNull = valB === null || valB === undefined || valB === '';

      if (aIsNull && bIsNull) return 0;
      if (aIsNull) return 1 * direction; // Nulls/empty last
      if (bIsNull) return -1 * direction; // Nulls/empty last

      // Type-specific comparison
      if (typeof valA === 'string' && typeof valB === 'string') {
        return valA.localeCompare(valB) * direction;
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return (valA - valB) * direction;
      }

      // Fallback for other types or mixed types (simple comparison)
      // Convert to string for consistent comparison if types differ or are complex
      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      if (strA < strB) return -1 * direction;
      if (strA > strB) return 1 * direction;
      return 0;
    });
  }

  return filtered;
});

// --- Methods ---

function sortBy(key: keyof JobResultItem) {
  if (sortKey.value === key) {
    // Cycle direction: asc -> desc -> null (no sort)
    if (sortDirection.value === 'asc') {
        sortDirection.value = 'desc';
    } else if (sortDirection.value === 'desc') {
        sortDirection.value = null;
        sortKey.value = null; // Clear key if sort is disabled
    } else { // Was null, start with asc
        sortDirection.value = 'asc';
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

function getStatusClass(status: string | null | undefined): string {
    switch(status?.toLowerCase()){
        case 'classified': return 'bg-green-100 text-green-800';
        case 'not possible': return 'bg-yellow-100 text-yellow-800';
        case 'error': return 'bg-red-100 text-red-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

// Highlight cells beyond the target classification depth
function getCellClass(item: JobResultItem, level: number): string {
    const baseClass = 'text-gray-700';
    const beyondDepthClass = 'text-gray-400 italic'; // Style for beyond depth

    // Check if the ID for this level exists and is not null/empty
    const levelIdKey = `level${level}_id` as keyof JobResultItem;
    const hasId = item[levelIdKey] !== null && item[levelIdKey] !== undefined && item[levelIdKey] !== '';

    if (level > props.targetLevel && hasId) {
        return beyondDepthClass;
    }
    return baseClass;
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
      <ChevronUpDownIcon v-else class="w-4 h-4 text-gray-400 opacity-50" />
    </span>
  `,
};

</script>

<style scoped>
/* Add minimum width to table cells if needed for better layout */
/* th, td { min-width: 100px; } */
/* th:first-child, td:first-child { min-width: 150px; } */ /* Vendor Name */
/* th:last-child, td:last-child { min-width: 200px; } */ /* Notes */

/* Ensure table layout is fixed if content wrapping becomes an issue */
/* table { table-layout: fixed; } */

/* Style for cells beyond requested depth */
.text-gray-400.italic {
    /* Add a visual cue, e.g., slightly lighter background or border */
    /* background-color: #f9fafb; */
}
</style>