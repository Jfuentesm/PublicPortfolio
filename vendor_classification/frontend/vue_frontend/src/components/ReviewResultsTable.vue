<template>
  <div class="mt-8 p-4 sm:p-6 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
    <h5 class="text-lg font-semibold text-gray-800 mb-4">Reviewed Classification Results</h5>
    <p class="text-sm text-gray-600 mb-4">
      Showing results after applying user hints. Target classification level for this review was **Level {{ targetLevel }}**. You can flag items again for further review if needed.
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
            <th scope="col" class="sticky left-0 z-10 bg-gray-100 px-2 py-3 text-center text-xs font-medium text-gray-600 uppercase tracking-wider w-12">Flag</th>
            <!-- Dynamically generate headers -->
            <th v-for="header in headers" :key="header.key"
                scope="col"
                @click="header.sortable ? sortBy(header.key) : null"
                :class="[
                  'px-3 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider whitespace-nowrap',
                   header.sortable ? 'cursor-pointer hover:bg-gray-200' : '',
                   header.sticky ? 'sticky left-[48px] z-10 bg-gray-100' : '', // Adjusted left offset for flag column
                   header.minWidth ? `min-w-[${header.minWidth}]` : '',
                   header.isOriginal ? 'bg-blue-50' : '', // Style original columns
                   header.isNew ? 'bg-green-50' : '', // Style new columns
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
          <tr v-for="(item, index) in filteredAndSortedResults" :key="item.vendor_name + '-' + index" class="hover:bg-gray-50 align-top" :class="{'bg-indigo-50': jobStore.isFlagged(item.vendor_name)}">
            <!-- Flag Button Cell (Sticky) -->
            <td class="sticky left-0 z-10 bg-white px-2 py-2 text-center align-middle" :class="{'bg-indigo-50': jobStore.isFlagged(item.vendor_name)}">
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
            <!-- Vendor Name Cell (Sticky) -->
            <td class="sticky left-[48px] z-10 bg-white px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900" :class="{'bg-indigo-50': jobStore.isFlagged(item.vendor_name)}">{{ item.vendor_name }}</td>
            <!-- Hint Cell -->
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
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500 bg-blue-50">{{ item.original_result?.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500 bg-blue-50">{{ item.original_result?.level1_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500 bg-blue-50">{{ item.original_result?.level2_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500 bg-blue-50">{{ item.original_result?.level2_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500 bg-blue-50">{{ item.original_result?.level3_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500 bg-blue-50">{{ item.original_result?.level3_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500 bg-blue-50">{{ item.original_result?.level4_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500 bg-blue-50">{{ item.original_result?.level4_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500 bg-blue-50">{{ item.original_result?.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500 bg-blue-50">{{ item.original_result?.level5_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center text-gray-500 bg-blue-50">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                      :class="getStatusClass(item.original_result?.final_status)">
                    {{ item.original_result?.final_status }}
                </span>
            </td>

            <!-- New Classification -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono bg-green-50" :class="getCellClass(item.new_result, 1)">{{ item.new_result?.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs bg-green-50" :class="getCellClass(item.new_result, 1)">{{ item.new_result?.level1_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono bg-green-50" :class="getCellClass(item.new_result, 2)">{{ item.new_result?.level2_id || '-' }}</td>
            <td class="px-3 py-2 text-xs bg-green-50" :class="getCellClass(item.new_result, 2)">{{ item.new_result?.level2_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono bg-green-50" :class="getCellClass(item.new_result, 3)">{{ item.new_result?.level3_id || '-' }}</td>
            <td class="px-3 py-2 text-xs bg-green-50" :class="getCellClass(item.new_result, 3)">{{ item.new_result?.level3_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono bg-green-50" :class="getCellClass(item.new_result, 4)">{{ item.new_result?.level4_id || '-' }}</td>
            <td class="px-3 py-2 text-xs bg-green-50" :class="getCellClass(item.new_result, 4)">{{ item.new_result?.level4_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono bg-green-50" :class="getCellClass(item.new_result, 5)">{{ item.new_result?.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs bg-green-50" :class="getCellClass(item.new_result, 5)">{{ item.new_result?.level5_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-sm text-center bg-green-50">
              <span v-if="item.new_result?.final_confidence !== null && item.new_result?.final_confidence !== undefined"
                    :class="getConfidenceClass(item.new_result.final_confidence)">
                {{ (item.new_result.final_confidence * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-gray-400 text-xs">N/A</span>
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center bg-green-50">
               <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="getStatusClass(item.new_result?.final_status)">
                {{ item.new_result?.final_status }}
              </span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-500 max-w-xs break-words bg-green-50">
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
  sticky?: boolean; // For sticky columns
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
// ADDED HEADERS FOR L2, L3, L4 for both Original and New sections
const headers = ref<ReviewTableHeader[]>([
  { key: 'vendor_name', label: 'Vendor Name', sortable: true, sticky: true, minWidth: '150px' }, // Make Vendor sticky
  { key: 'hint', label: 'User Hint', sortable: true, minWidth: '180px' },
  // Original Results
  { key: 'original_result.level1_id', label: 'Orig L1 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level1_name', label: 'Orig L1 Name', sortable: true, minWidth: '120px', isOriginal: true },
  { key: 'original_result.level2_id', label: 'Orig L2 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level2_name', label: 'Orig L2 Name', sortable: true, minWidth: '120px', isOriginal: true },
  { key: 'original_result.level3_id', label: 'Orig L3 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level3_name', label: 'Orig L3 Name', sortable: true, minWidth: '120px', isOriginal: true },
  { key: 'original_result.level4_id', label: 'Orig L4 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level4_name', label: 'Orig L4 Name', sortable: true, minWidth: '120px', isOriginal: true },
  { key: 'original_result.level5_id', label: 'Orig L5 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level5_name', label: 'Orig L5 Name', sortable: true, minWidth: '120px', isOriginal: true },
  { key: 'original_result.final_status', label: 'Orig Status', sortable: true, minWidth: '100px', isOriginal: true },
  // New Results
  { key: 'new_result.level1_id', label: 'New L1 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level1_name', label: 'New L1 Name', sortable: true, minWidth: '120px', isNew: true },
  { key: 'new_result.level2_id', label: 'New L2 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level2_name', label: 'New L2 Name', sortable: true, minWidth: '120px', isNew: true },
  { key: 'new_result.level3_id', label: 'New L3 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level3_name', label: 'New L3 Name', sortable: true, minWidth: '120px', isNew: true },
  { key: 'new_result.level4_id', label: 'New L4 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level4_name', label: 'New L4 Name', sortable: true, minWidth: '120px', isNew: true },
  { key: 'new_result.level5_id', label: 'New L5 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level5_name', label: 'New L5 Name', sortable: true, minWidth: '120px', isNew: true },
  { key: 'new_result.final_confidence', label: 'New Confidence', sortable: true, minWidth: '100px', isNew: true },
  { key: 'new_result.final_status', label: 'New Status', sortable: true, minWidth: '100px', isNew: true },
  { key: 'new_result.classification_notes_or_reason', label: 'New Notes / Reason', sortable: false, minWidth: '200px', isNew: true },
]);

// --- Computed Properties ---

// Helper to get nested values for sorting/filtering
const getNestedValue = (obj: any, path: string): any => {
  // Handle cases where obj might be null or undefined early
  if (!obj) return null;
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
      // Search within original results (L1-L5)
      getNestedValue(item, 'original_result.level1_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level1_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level2_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level2_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level3_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level3_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level4_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level4_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level5_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.level5_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'original_result.final_status')?.toLowerCase().includes(lowerSearchTerm) ||
      // Search within new results (L1-L5)
      getNestedValue(item, 'new_result.level1_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level1_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level2_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level2_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level3_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level3_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level4_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level4_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level5_id')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.level5_name')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.final_status')?.toLowerCase().includes(lowerSearchTerm) ||
      getNestedValue(item, 'new_result.classification_notes_or_reason')?.toLowerCase().includes(lowerSearchTerm)
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
      if (aIsNull) return 1 * direction; // Nulls/empty last when ascending
      if (bIsNull) return -1 * direction; // Nulls/empty last when ascending

      if (typeof valA === 'string' && typeof valB === 'string') {
        return valA.localeCompare(valB) * direction;
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return (valA - valB) * direction;
      }

      // Fallback: compare as strings
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
        // Cycle back to no sort instead of asc
        sortDirection.value = null;
        sortKey.value = null;
    } else { // Was null
        sortDirection.value = 'asc'; // Start with asc
        sortKey.value = key;
    }
  } else {
    sortKey.value = key;
    sortDirection.value = 'asc'; // Default to asc when changing column
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
// Or if the ID itself is null/empty
function getCellClass(item: JobResultItem | null | undefined, level: number): string {
    const baseClass = 'text-gray-700';
    const beyondDepthClass = 'text-gray-400 italic'; // Style for levels beyond target
    const nullClass = 'text-gray-400'; // Style for null/empty values

    if (!item) return nullClass; // Handle case where new_result might be null

    const levelIdKey = `level${level}_id` as keyof JobResultItem;
    const hasId = item[levelIdKey] !== null && item[levelIdKey] !== undefined && String(item[levelIdKey]).trim() !== '';

    if (!hasId) {
        return nullClass; // Use null style if ID is missing/empty
    }

    // Check if the *achieved* level for the *new* result is less than the current cell's level
    const achievedLevel = item.achieved_level ?? 0;
    if (level > achievedLevel) {
         // If the classification stopped before this level, but the ID somehow exists (unlikely but possible), style it as less important
         // Or, more likely, the ID *is* null, handled above. This check is secondary.
         // Let's prioritize the null check. If it has an ID, show it normally unless it's beyond the *target* level.
    }

    // Style differently if the cell's level is beyond the *job's* target level
    if (level > props.targetLevel) {
        return beyondDepthClass;
    }

    return baseClass; // Default style if it has an ID and is within target level
}

// --- Flagging and Hint Handling ---
function toggleFlag(vendorName: string) {
    if (jobStore.isFlagged(vendorName)) {
        jobStore.unflagVendor(vendorName);
    } else {
        // Pre-populate hint if available from the current item's hint field
        const currentItem = props.results?.find(r => r.vendor_name === vendorName);
        const initialHint = currentItem?.hint || ''; // Use existing hint or empty string
        jobStore.flagVendor(vendorName);
        jobStore.setHint(vendorName, initialHint); // Set the initial hint when flagging
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
/* Ensure sticky header cells have appropriate background */
thead th.sticky {
  position: sticky;
  /* Apply background color matching the thead */
  background-color: #f3f4f6; /* bg-gray-100 */
}

/* Ensure sticky body cells have appropriate background */
tbody td.sticky {
    position: sticky;
    /* Apply background color matching the row's background (consider hover/flagged states) */
    background-color: inherit; /* Inherit from parent tr */
}

/* Add slight borders for visual separation */
th.isOriginal, td.isOriginal {
    border-left: 1px solid #e5e7eb; /* gray-200 */
}
th.isNew, td.isNew {
    border-left: 1px solid #e5e7eb; /* gray-200 */
}
th:first-child, td:first-child {
    border-left: none;
}

</style>