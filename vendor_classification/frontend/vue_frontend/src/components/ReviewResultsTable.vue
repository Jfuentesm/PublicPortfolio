<template>
  <div class="mt-8 p-4 sm:p-6 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
    <h5 class="text-lg font-semibold text-gray-800 mb-4">Reviewed Classification Results</h5>
    <p class="text-sm text-gray-600 mb-4">
      Showing results after applying user hints. You can flag items again for further review if needed.
    </p>

    <!-- Search Input -->
    <div class="mb-4">
      <label for="review-results-search" class="sr-only">Search Reviewed Results</label>
      <div class="relative rounded-md shadow-sm">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon class="h-5 w-5 text-gray-400" aria-hidden="true" />
        </div>
        <input
          type="text"
          id="review-results-search"
          v-model="searchTerm"
          placeholder="Search Vendor, Hint, Category, ID, Notes..."
          class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
        />
      </div>
    </div>

     <!-- Action Buttons (Submit Flags) -->
    <div class="mb-4 text-right" v-if="jobStore.hasFlaggedItems">
        <button
          type="button"
          @click="submitFlags"
          :disabled="jobStore.reclassifyLoading"
          class="inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
        >
          <ArrowPathIcon v-if="jobStore.reclassifyLoading" class="animate-spin -ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
          <PaperAirplaneIcon v-else class="-ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
          Submit {{ jobStore.flaggedForReview.size }} Flag{{ jobStore.flaggedForReview.size !== 1 ? 's' : '' }} for Re-classification
        </button>
        <p v-if="jobStore.reclassifyError" class="text-xs text-red-600 mt-1 text-right">{{ jobStore.reclassifyError }}</p>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="text-center py-5 text-gray-500">
      <svg class="animate-spin h-6 w-6 text-primary mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="mt-2 text-sm">Loading reviewed results...</p>
    </div>
    <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
      Error loading reviewed results: {{ error }}
    </div>
    <div v-else-if="!results || results.length === 0" class="text-center py-5 text-gray-500">
      No reviewed results found for this job.
    </div>

    <!-- Results Table -->
    <div v-else class="overflow-x-auto border border-gray-200 rounded-md">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <!-- Flag Column -->
            <th scope="col" class="px-2 py-3 text-center text-xs font-medium text-gray-600 uppercase tracking-wider w-12">Flag</th>
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
            <td :colspan="headers.length + 1" class="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-center">No results match your search criteria.</td>
          </tr>
          <tr v-for="(item, index) in filteredAndSortedResults" :key="item.vendor_name + '-' + index" class="hover:bg-gray-50 align-top" :class="{'bg-blue-50': jobStore.isFlagged(item.vendor_name)}">
            <!-- Flag Button Cell -->
            <td class="px-2 py-2 text-center align-middle">
                 <button
                    @click="toggleFlag(item.vendor_name)"
                    :title="jobStore.isFlagged(item.vendor_name) ? 'Remove flag and hint' : 'Flag for re-classification'"
                    class="p-1 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary"
                    :class="jobStore.isFlagged(item.vendor_name) ? 'text-primary' : 'text-gray-400 hover:text-primary-dark'"
                  >
                    <FlagIconSolid v-if="jobStore.isFlagged(item.vendor_name)" class="h-5 w-5" aria-hidden="true" />
                    <FlagIconOutline v-else class="h-5 w-5" aria-hidden="true" />
                    <span class="sr-only">Flag item</span>
                  </button>
            </td>
            <!-- Data Cells -->
            <td class="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.vendor_name }}</td>
            <td class="px-3 py-2 text-xs text-gray-600 max-w-xs break-words">
                <span v-if="!jobStore.isFlagged(item.vendor_name)">{{ item.hint }}</span>
                 <!-- Inline Hint Editor when Flagged -->
                <textarea v-else
                          rows="2"
                          :value="jobStore.getHint(item.vendor_name)"
                          @input="updateHint(item.vendor_name, ($event.target as HTMLTextAreaElement).value)"
                          placeholder="Enter new hint..."
                          class="block w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                ></textarea>
            </td>
            <!-- Original Classification -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500">{{ item.original_result?.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500">{{ item.original_result?.level1_name || '-' }}</td>
            <!-- ... Add other original levels L2-L5 similarly ... -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500">{{ item.original_result?.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500">{{ item.original_result?.level5_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center text-gray-500">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                      :class="getStatusClass(item.original_result?.final_status)">
                    {{ item.original_result?.final_status }}
                </span>
            </td>

            <!-- New Classification -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item.new_result, 1)">{{ item.new_result?.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item.new_result, 1)">{{ item.new_result?.level1_name || '-' }}</td>
            <!-- ... Add other new levels L2-L5 similarly ... -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item.new_result, 5)">{{ item.new_result?.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item.new_result, 5)">{{ item.new_result?.level5_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-sm text-center">
              <span v-if="item.new_result?.final_confidence !== null && item.new_result?.final_confidence !== undefined"
                    :class="getConfidenceClass(item.new_result.final_confidence)">
                {{ (item.new_result.final_confidence * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-gray-400 text-xs">N/A</span>
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center">
               <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="getStatusClass(item.new_result?.final_status)">
                {{ item.new_result?.final_status }}
              </span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-500 max-w-xs break-words">
              {{ item.new_result?.classification_notes_or_reason || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

     <!-- Row Count -->
    <div class="mt-3 text-xs text-gray-500">
      Showing {{ filteredAndSortedResults.length }} of {{ results?.length || 0 }} reviewed results.
    </div>

    <!-- Hint Input Modal -->
    <!-- <HintInputModal
        :open="showHintModal"
        :vendor-name="selectedVendorForHint"
        :initial-hint="jobStore.getHint(selectedVendorForHint)"
        @close="showHintModal = false"
        @save="saveHint"
    /> -->
     <!-- Note: Using inline editor instead of modal for now -->

  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import { useJobStore, type ReviewResultItem, type JobResultItem } from '@/stores/job';
import { FlagIcon as FlagIconOutline, MagnifyingGlassIcon, PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { FlagIcon as FlagIconSolid, ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon } from '@heroicons/vue/20/solid';
// import HintInputModal from './HintInputModal.vue'; // Import if using modal

// --- Define Header Interface ---
interface ReviewTableHeader {
  key: string; // Use string for complex/nested keys
  label: string;
  sortable: boolean;
  minWidth?: string;
  isOriginal?: boolean; // Flag for styling/grouping
  isNew?: boolean;      // Flag for styling/grouping
}
// --- END Define Header Interface ---

// --- Props ---
const props = defineProps({
  results: {
    type: Array as PropType<ReviewResultItem[] | null>,
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

const emit = defineEmits(['submit-flags']); // Emit event when submit button is clicked

// --- Store ---
const jobStore = useJobStore();

// --- Internal State ---
const searchTerm = ref('');
const sortKey = ref<string | null>('vendor_name'); // Default sort by vendor name
const sortDirection = ref<'asc' | 'desc' | null>('asc'); // Default sort direction
// const showHintModal = ref(false); // State for modal
// const selectedVendorForHint = ref(''); // State for modal

// --- Table Headers Definition ---
const headers = ref<ReviewTableHeader[]>([
  { key: 'vendor_name', label: 'Vendor Name', sortable: true, minWidth: '150px' },
  { key: 'hint', label: 'User Hint', sortable: true, minWidth: '180px' },
  // Original Results
  { key: 'original_result.level1_id', label: 'Orig L1 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level1_name', label: 'Orig L1 Name', sortable: true, minWidth: '120px', isOriginal: true },
  // Add L2-L4 original if needed
  { key: 'original_result.level5_id', label: 'Orig L5 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level5_name', label: 'Orig L5 Name', sortable: true, minWidth: '120px', isOriginal: true },
  { key: 'original_result.final_status', label: 'Orig Status', sortable: true, minWidth: '100px', isOriginal: true },
  // New Results
  { key: 'new_result.level1_id', label: 'New L1 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level1_name', label: 'New L1 Name', sortable: true, minWidth: '120px', isNew: true },
   // Add L2-L4 new if needed
  { key: 'new_result.level5_id', label: 'New L5 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level5_name', label: 'New L5 Name', sortable: true, minWidth: '120px', isNew: true },
  { key: 'new_result.final_confidence', label: 'New Confidence', sortable: true, minWidth: '100px', isNew: true },
  { key: 'new_result.final_status', label: 'New Status', sortable: true, minWidth: '100px', isNew: true },
  { key: 'new_result.classification_notes_or_reason', label: 'New Notes / Reason', sortable: false, minWidth: '200px', isNew: true },
]);

// --- Computed Properties ---

// Helper to get nested values for sorting/filtering
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((value, key) => (value && value[key] !== undefined ? value[key] : null), obj);
};


const filteredAndSortedResults = computed(() => {
  if (!props.results) return [];

  let filtered = props.results;

  // Filtering
  if (searchTerm.value) {
    const lowerSearchTerm = searchTerm.value.toLowerCase();
    filtered = filtered.filter(item =>
      item.vendor_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.hint?.toLowerCase().includes(lowerSearchTerm) ||
      // Search within original results
      item.original_result?.level1_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.original_result?.level1_name?.toLowerCase().includes(lowerSearchTerm) ||
      // ... add other original levels ...
      item.original_result?.level5_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.original_result?.level5_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.original_result?.final_status?.toLowerCase().includes(lowerSearchTerm) ||
      // Search within new results
      item.new_result?.level1_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.level1_name?.toLowerCase().includes(lowerSearchTerm) ||
      // ... add other new levels ...
      item.new_result?.level5_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.level5_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.final_status?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.classification_notes_or_reason?.toLowerCase().includes(lowerSearchTerm)
    );
  }

  // Sorting
  if (sortKey.value && sortDirection.value) {
    const key = sortKey.value;
    const direction = sortDirection.value === 'asc' ? 1 : -1;

    filtered = filtered.slice().sort((a, b) => {
      const valA = getNestedValue(a, key);
      const valB = getNestedValue(b, key);

      const aIsNull = valA === null || valA === undefined || valA === '';
      const bIsNull = valB === null || valB === undefined || valB === '';

      if (aIsNull && bIsNull) return 0;
      if (aIsNull) return 1 * direction;
      if (bIsNull) return -1 * direction;

      if (typeof valA === 'string' && typeof valB === 'string') {
        return valA.localeCompare(valB) * direction;
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return (valA - valB) * direction;
      }

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

function sortBy(key: string) { // Key is now string due to nesting
  if (sortKey.value === key) {
    if (sortDirection.value === 'asc') {
        sortDirection.value = 'desc';
    } else if (sortDirection.value === 'desc') {
        sortDirection.value = null;
        sortKey.value = null;
    } else {
        sortDirection.value = 'asc';
    }
  } else {
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

// Highlight cells beyond the target classification depth in the *new* result
function getCellClass(item: JobResultItem | null | undefined, level: number): string {
    const baseClass = 'text-gray-700';
    const beyondDepthClass = 'text-gray-400 italic';

    if (!item) return baseClass; // Handle case where new_result might be null

    const levelIdKey = `level${level}_id` as keyof JobResultItem;
    const hasId = item[levelIdKey] !== null && item[levelIdKey] !== undefined && item[levelIdKey] !== '';

    if (level > props.targetLevel && hasId) {
        return beyondDepthClass;
    }
    return baseClass;
}

// --- Flagging and Hint Handling ---
function toggleFlag(vendorName: string) {
    if (jobStore.isFlagged(vendorName)) {
        jobStore.unflagVendor(vendorName);
    } else {
        jobStore.flagVendor(vendorName);
        // Optionally open modal here if using one
        // selectedVendorForHint.value = vendorName;
        // showHintModal.value = true;
    }
}

function updateHint(vendorName: string, hint: string) {
    jobStore.setHint(vendorName, hint);
}

// function saveHint(hint: string) {
//     if (selectedVendorForHint.value) {
//         jobStore.setHint(selectedVendorForHint.value, hint);
//     }
//     selectedVendorForHint.value = ''; // Clear selection
// }

async function submitFlags() {
    emit('submit-flags'); // Notify parent (JobStatus) to handle submission logic
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
/* Add styles for visually separating original vs new columns if desired */
/* e.g., a subtle border or background */
/* th[isOriginal="true"], td[isOriginal="true"] { ... } */
/* th[isNew="true"], td[isNew="true"] { ... } */
</style>