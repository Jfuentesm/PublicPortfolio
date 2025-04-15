<template>
  <div class="mt-8 p-4 sm:p-6 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
    <h5 class="text-lg font-semibold text-gray-800 mb-4">
      {{ isIntegratedView ? 'Integrated Classification Results' : 'Detailed Classification Results' }}
    </h5>
    <p v-if="isIntegratedView" class="text-sm text-gray-600 mb-4">
      Showing original classification results alongside the latest reviewed results (if available). Target level: **Level {{ targetLevel }}**.
    </p>
     <p v-else class="text-sm text-gray-600 mb-4">
      Target classification level for this job was **Level {{ targetLevel }}**.
    </p>

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
          placeholder="Search Vendor, Category, ID, Hint, Notes..."
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
      <p class="mt-2 text-sm">Loading detailed results...</p>
    </div>
    <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
      Error loading results: {{ error }}
    </div>
    <div v-else-if="!originalResults || originalResults.length === 0" class="text-center py-5 text-gray-500">
      No detailed results found for this job.
    </div>

    <!-- Results Table -->
    <div v-else class="overflow-x-auto border border-gray-200 rounded-md">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <!-- Flag Column (Sticky) -->
            <th scope="col" class="sticky left-0 z-10 bg-gray-100 px-2 py-3 text-center text-xs font-medium text-gray-600 uppercase tracking-wider w-12">Flag</th>
            <!-- Dynamically generate headers -->
            <th v-for="header in dynamicHeaders" :key="header.key"
                scope="col"
                @click="header.sortable ? sortBy(header.key) : null"
                :class="[
                  'px-3 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider whitespace-nowrap',
                   header.sortable ? 'cursor-pointer hover:bg-gray-200' : '',
                   header.sticky ? 'sticky left-[48px] z-10 bg-gray-100' : '', // Adjusted left offset for flag column
                   header.minWidth ? `min-w-[${header.minWidth}]` : '',
                   header.isOriginal && isIntegratedView ? 'bg-blue-50' : '', // Style original columns only in integrated view
                   header.isNew ? 'bg-green-50' : '', // Style new columns
                ]">
              {{ header.label }}
              <SortIcon v-if="header.sortable" :direction="sortKey === header.key ? sortDirection : null" />
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="filteredAndSortedItems.length === 0">
            <td :colspan="dynamicHeaders.length + 1" class="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-center">No results match your search criteria.</td>
          </tr>
          <!-- Iterate through combined/processed items -->
          <tr v-for="(item, index) in filteredAndSortedItems" :key="item.vendor_name + '-' + index" class="hover:bg-gray-50 align-top" :class="{'bg-indigo-50': jobStore.isFlagged(item.vendor_name)}">
             <!-- Flag Button Cell (Sticky) -->
             <td class="sticky left-0 z-10 bg-white px-2 py-2 text-center align-middle" :class="{'bg-indigo-50': jobStore.isFlagged(item.vendor_name)}">
                 <button
                    @click="toggleFlag(item.vendor_name, item.review_hint)"
                    :title="jobStore.isFlagged(item.vendor_name) ? 'Edit hint or remove flag' : 'Flag for re-classification'"
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

             <!-- Hint Cell (Only in Integrated View) -->
             <td v-if="isIntegratedView" class="px-3 py-2 text-xs text-gray-600 max-w-xs break-words">
                 <span v-if="!jobStore.isFlagged(item.vendor_name)">{{ item.review_hint || '-' }}</span>
                 <!-- Inline Hint Editor when Flagged -->
                 <div v-else>
                    <label :for="'hint-' + index" class="sr-only">Hint for {{ item.vendor_name }}</label>
                    <textarea :id="'hint-' + index"
                              rows="2"
                              :value="jobStore.getHint(item.vendor_name)"
                              @input="updateHint(item.vendor_name, ($event.target as HTMLTextAreaElement).value)"
                              placeholder="Enter hint..."
                              class="block w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                    ></textarea>
                    <p v-if="!jobStore.getHint(item.vendor_name)" class="text-red-600 text-xs mt-1">Hint required for submission.</p>
                 </div>
             </td>

             <!-- Original Classification Columns -->
             <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="[getCellClass(item.original_result, 1), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level1_id || '-' }}</td>
             <td class="px-3 py-2 text-xs" :class="[getCellClass(item.original_result, 1), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level1_name || '-' }}</td>
             <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="[getCellClass(item.original_result, 2), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level2_id || '-' }}</td>
             <td class="px-3 py-2 text-xs" :class="[getCellClass(item.original_result, 2), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level2_name || '-' }}</td>
             <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="[getCellClass(item.original_result, 3), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level3_id || '-' }}</td>
             <td class="px-3 py-2 text-xs" :class="[getCellClass(item.original_result, 3), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level3_name || '-' }}</td>
             <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="[getCellClass(item.original_result, 4), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level4_id || '-' }}</td>
             <td class="px-3 py-2 text-xs" :class="[getCellClass(item.original_result, 4), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level4_name || '-' }}</td>
             <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="[getCellClass(item.original_result, 5), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level5_id || '-' }}</td>
             <td class="px-3 py-2 text-xs" :class="[getCellClass(item.original_result, 5), isIntegratedView ? 'bg-blue-50' : '']">{{ item.original_result?.level5_name || '-' }}</td>
             <td class="px-3 py-2 whitespace-nowrap text-sm text-center" :class="isIntegratedView ? 'bg-blue-50' : ''">
               <span v-if="item.original_result?.final_confidence !== null && item.original_result?.final_confidence !== undefined"
                     :class="getConfidenceClass(item.original_result.final_confidence)">
                 {{ (item.original_result.final_confidence * 100).toFixed(1) }}%
               </span>
               <span v-else class="text-gray-400 text-xs">N/A</span>
             </td>
             <td class="px-3 py-2 whitespace-nowrap text-xs text-center" :class="isIntegratedView ? 'bg-blue-50' : ''">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                     :class="getStatusClass(item.original_result?.final_status)">
                 {{ item.original_result?.final_status }}
               </span>
             </td>
              <td class="px-3 py-2 whitespace-nowrap text-xs text-center" :class="isIntegratedView ? 'bg-blue-50' : ''">
               <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                     :class="getSourceClass(item.original_result?.classification_source)">
                 {{ item.original_result?.classification_source }}
               </span>
             </td>
             <td class="px-3 py-2 text-xs text-gray-500 max-w-xs break-words" :class="isIntegratedView ? 'bg-blue-50' : ''">
                  <!-- Show hint input if flagged, otherwise original notes -->
                  <div v-if="jobStore.isFlagged(item.vendor_name) && !isIntegratedView">
                     <label :for="'hint-' + index" class="sr-only">Hint for {{ item.vendor_name }}</label>
                     <textarea :id="'hint-' + index"
                               rows="2"
                               :value="jobStore.getHint(item.vendor_name)"
                               @input="updateHint(item.vendor_name, ($event.target as HTMLTextAreaElement).value)"
                               placeholder="Enter hint..."
                               class="block w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                     ></textarea>
                     <p v-if="!jobStore.getHint(item.vendor_name)" class="text-red-600 text-xs mt-1">Hint required for submission.</p>
                  </div>
                  <span v-else>{{ item.original_result?.classification_notes_or_reason || '-' }}</span>
             </td>

             <!-- New Classification Columns (Only in Integrated View) -->
             <template v-if="isIntegratedView">
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
                 <td class="px-3 py-2 whitespace-nowrap text-xs text-center bg-green-50">
                   <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                        :class="getSourceClass(item.new_result?.classification_source)">
                    {{ item.new_result?.classification_source }}
                  </span>
                 </td>
                <td class="px-3 py-2 text-xs text-gray-500 max-w-xs break-words bg-green-50">
                  {{ item.new_result?.classification_notes_or_reason || '-' }}
                </td>
             </template>
          </tr>
        </tbody>
      </table>
    </div>

     <!-- Row Count -->
    <div class="mt-3 text-xs text-gray-500">
      Showing {{ filteredAndSortedItems.length }} of {{ originalResults?.length || 0 }} results.
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType, watch } from 'vue';
import { useJobStore, type JobResultItem, type ReviewResultItem } from '@/stores/job';
import { FlagIcon as FlagIconOutline, MagnifyingGlassIcon, PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { FlagIcon as FlagIconSolid, ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon } from '@heroicons/vue/20/solid';

// --- Define Header Interface ---
interface TableHeader {
  key: string; // Use string for complex/nested keys or combined fields
  label: string;
  sortable: boolean;
  sticky?: boolean;
  minWidth?: string;
  isOriginal?: boolean; // Flag for styling/grouping
  isNew?: boolean;      // Flag for styling/grouping
}

// --- Define Combined Item Interface for internal use ---
interface CombinedResultItem {
    vendor_name: string;
    original_result: JobResultItem;
    review_hint: string | null; // Hint from review job
    new_result: JobResultItem | null; // New result from review job (can be null if not reviewed)
}

// --- Props ---
const props = defineProps({
  // Use JobResultItem[] for original results (always expected for CLASSIFICATION job view)
  originalResults: {
    type: Array as PropType<JobResultItem[] | null>,
    required: true,
  },
  // Use ReviewResultItem[] for related review results (optional)
  reviewResults: {
    type: Array as PropType<ReviewResultItem[] | null>,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String as PropType<string | null>,
    default: null,
  },
  targetLevel: {
    type: Number,
    required: true,
  }
});

const emit = defineEmits(['submit-flags']);

// --- Store ---
const jobStore = useJobStore();

// --- Internal State ---
const searchTerm = ref('');
const sortKey = ref<string | null>('vendor_name'); // Default sort key
const sortDirection = ref<'asc' | 'desc' | null>('asc');

// --- Computed Properties ---

const isIntegratedView = computed(() => !!props.reviewResults && props.reviewResults.length > 0);

// Combine original and review results into a single structure for easier iteration/filtering/sorting
const combinedItems = computed((): CombinedResultItem[] => {
    if (!props.originalResults) return [];

    const reviewMap = new Map<string, ReviewResultItem>();
    if (props.reviewResults) {
        props.reviewResults.forEach(reviewItem => {
            reviewMap.set(reviewItem.vendor_name, reviewItem);
        });
    }

    return props.originalResults.map(originalItem => {
        const reviewItem = reviewMap.get(originalItem.vendor_name);
        return {
            vendor_name: originalItem.vendor_name,
            original_result: originalItem,
            review_hint: reviewItem ? reviewItem.hint : null,
            new_result: reviewItem ? reviewItem.new_result : null,
        };
    });
});

// Generate dynamic headers based on whether it's an integrated view
const dynamicHeaders = computed((): TableHeader[] => {
    const baseHeaders: TableHeader[] = [
        { key: 'vendor_name', label: 'Vendor Name', sortable: true, sticky: true, minWidth: '150px' },
    ];

    const originalResultHeaders: TableHeader[] = [
        { key: 'original_result.level1_id', label: 'L1 ID', sortable: true, minWidth: '80px', isOriginal: true },
        { key: 'original_result.level1_name', label: 'L1 Name', sortable: true, minWidth: '120px', isOriginal: true },
        { key: 'original_result.level2_id', label: 'L2 ID', sortable: true, minWidth: '80px', isOriginal: true },
        { key: 'original_result.level2_name', label: 'L2 Name', sortable: true, minWidth: '120px', isOriginal: true },
        { key: 'original_result.level3_id', label: 'L3 ID', sortable: true, minWidth: '80px', isOriginal: true },
        { key: 'original_result.level3_name', label: 'L3 Name', sortable: true, minWidth: '120px', isOriginal: true },
        { key: 'original_result.level4_id', label: 'L4 ID', sortable: true, minWidth: '80px', isOriginal: true },
        { key: 'original_result.level4_name', label: 'L4 Name', sortable: true, minWidth: '120px', isOriginal: true },
        { key: 'original_result.level5_id', label: 'L5 ID', sortable: true, minWidth: '80px', isOriginal: true },
        { key: 'original_result.level5_name', label: 'L5 Name', sortable: true, minWidth: '120px', isOriginal: true },
        { key: 'original_result.final_confidence', label: 'Confidence', sortable: true, minWidth: '100px', isOriginal: true },
        { key: 'original_result.final_status', label: 'Status', sortable: true, minWidth: '100px', isOriginal: true },
        { key: 'original_result.classification_source', label: 'Source', sortable: true, minWidth: '80px', isOriginal: true },
        { key: 'original_result.classification_notes_or_reason', label: 'Notes/Reason', sortable: false, minWidth: '200px', isOriginal: true }, // Combined column for original notes
    ];

    const reviewHintHeader: TableHeader = { key: 'review_hint', label: 'User Hint', sortable: true, minWidth: '180px' };

    const newResultHeaders: TableHeader[] = [
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
        { key: 'new_result.classification_source', label: 'New Source', sortable: true, minWidth: '80px', isNew: true },
        { key: 'new_result.classification_notes_or_reason', label: 'New Notes/Reason', sortable: false, minWidth: '200px', isNew: true },
    ];

    if (isIntegratedView.value) {
        // Modify original notes header label
        const origNotesHeader = originalResultHeaders.find(h => h.key === 'original_result.classification_notes_or_reason');
        if (origNotesHeader) origNotesHeader.label = 'Orig Notes/Reason';

        return [
            ...baseHeaders,
            reviewHintHeader, // Add hint column
            ...originalResultHeaders,
            ...newResultHeaders
        ];
    } else {
        // Modify original notes header label and make it the hint column if flagged
        const origNotesHeader = originalResultHeaders.find(h => h.key === 'original_result.classification_notes_or_reason');
        if (origNotesHeader) origNotesHeader.label = 'Hint / Notes / Reason';
        return [
            ...baseHeaders,
            ...originalResultHeaders
        ];
    }
});

// Helper to get nested values for filtering/sorting
const getNestedValue = (obj: any, path: string): any => {
  if (!obj) return null;
  // Handle direct keys first
  if (path.indexOf('.') === -1) {
      return obj[path] ?? null;
  }
  // Handle nested keys
  return path.split('.').reduce((value, key) => (value && value[key] !== undefined && value[key] !== null ? value[key] : null), obj);
};

const filteredAndSortedItems = computed(() => {
  let filtered = combinedItems.value;

  // Filtering
  if (searchTerm.value) {
    const lowerSearchTerm = searchTerm.value.toLowerCase();
    filtered = filtered.filter(item => {
        // Search direct fields
        if (item.vendor_name?.toLowerCase().includes(lowerSearchTerm)) return true;
        if (isIntegratedView.value && item.review_hint?.toLowerCase().includes(lowerSearchTerm)) return true;

        // Search original result fields (using header keys for consistency)
        const originalHeaders = dynamicHeaders.value.filter(h => h.isOriginal);
        for (const header of originalHeaders) {
             const value = getNestedValue(item, header.key);
             if (value && String(value).toLowerCase().includes(lowerSearchTerm)) return true;
        }

        // Search new result fields if integrated view
        if (isIntegratedView.value) {
            const newHeaders = dynamicHeaders.value.filter(h => h.isNew);
            for (const header of newHeaders) {
                const value = getNestedValue(item, header.key);
                if (value && String(value).toLowerCase().includes(lowerSearchTerm)) return true;
            }
        }
        // Search hint if flagged (even in non-integrated view)
        if (jobStore.isFlagged(item.vendor_name) && jobStore.getHint(item.vendor_name)?.toLowerCase().includes(lowerSearchTerm)) return true;

        return false; // No match
    });
  }

  // Sorting
  if (sortKey.value && sortDirection.value) {
    const key = sortKey.value;
    const direction = sortDirection.value === 'asc' ? 1 : -1;

    // Special handling for the hint column in non-integrated view
    const effectiveSortKey = (!isIntegratedView.value && key === 'original_result.classification_notes_or_reason') ? 'hint_or_notes' : key;

    filtered = filtered.slice().sort((a, b) => {
      let valA: any;
      let valB: any;

      if (effectiveSortKey === 'hint_or_notes') {
          valA = jobStore.isFlagged(a.vendor_name) ? jobStore.getHint(a.vendor_name) : a.original_result?.classification_notes_or_reason;
          valB = jobStore.isFlagged(b.vendor_name) ? jobStore.getHint(b.vendor_name) : b.original_result?.classification_notes_or_reason;
      } else {
          valA = getNestedValue(a, key);
          valB = getNestedValue(b, key);
      }

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

function sortBy(key: string) {
  if (sortKey.value === key) {
    if (sortDirection.value === 'asc') sortDirection.value = 'desc';
    else if (sortDirection.value === 'desc') {
        sortDirection.value = null; // Cycle to no sort
        sortKey.value = null;
    } else { // Was null
        sortDirection.value = 'asc';
        sortKey.value = key; // Re-apply key
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

function getSourceClass(source: string | null | undefined): string {
    switch(source?.toLowerCase()){
        case 'initial': return 'bg-green-100 text-green-800';
        case 'search': return 'bg-blue-100 text-blue-800';
        case 'review': return 'bg-purple-100 text-purple-800'; // Added style for review source
        default: return 'bg-gray-100 text-gray-800';
    }
}

// Highlight cells beyond the target classification depth or if ID is null/empty
function getCellClass(item: JobResultItem | null | undefined, level: number): string {
    const baseClass = 'text-gray-700';
    const beyondDepthClass = 'text-gray-400 italic';
    const nullClass = 'text-gray-400';

    if (!item) return nullClass;

    const levelIdKey = `level${level}_id` as keyof JobResultItem;
    const hasId = item[levelIdKey] !== null && item[levelIdKey] !== undefined && String(item[levelIdKey]).trim() !== '';

    if (!hasId) return nullClass;
    if (level > props.targetLevel) return beyondDepthClass;
    return baseClass;
}

// --- Flagging and Hint Handling ---
function toggleFlag(vendorName: string, reviewHint: string | null) {
    if (jobStore.isFlagged(vendorName)) {
        jobStore.unflagVendor(vendorName);
    } else {
        // Pre-populate hint with the review hint if available in integrated view, otherwise null
        const initialHint = isIntegratedView.value ? reviewHint : null;
        jobStore.flagVendor(vendorName, initialHint);
    }
}

function updateHint(vendorName: string, hint: string) {
    jobStore.setHint(vendorName, hint);
}

async function submitFlags() {
    emit('submit-flags'); // Notify parent
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

// Watch for prop changes to potentially clear sort/filter (optional)
watch(() => [props.originalResults, props.reviewResults], () => {
    console.log("Results props changed, resetting sort/filter");
    searchTerm.value = '';
    sortKey.value = 'vendor_name';
    sortDirection.value = 'asc';
});

</script>

<style scoped>
/* Ensure sticky header cells have appropriate background */
thead th.sticky {
  position: sticky;
  background-color: #f3f4f6; /* bg-gray-100 */
}

/* Ensure sticky body cells have appropriate background */
tbody td.sticky {
    position: sticky;
    background-color: inherit; /* Inherit from parent tr */
}
/* Ensure flagged rows inherit sticky background correctly */
tbody tr.bg-indigo-50 td.sticky {
    background-color: #e0e7ff; /* bg-indigo-50 */
}


/* Add slight borders for visual separation in integrated view */
th.isOriginal, td.isOriginal {
    border-left: 1px solid #e5e7eb; /* gray-200 */
}
th.isNew, td.isNew {
    border-left: 1px solid #e5e7eb; /* gray-200 */
}
th:first-child, td:first-child { /* Flag column */
    border-left: none;
}
th:nth-child(2), td:nth-child(2) { /* Vendor name column */
     border-left: none;
}
/* Adjust border for hint column if it's the first after vendor name */
th:nth-child(3), td:nth-child(3) {
    border-left: v-bind("isIntegratedView ? '1px solid #e5e7eb' : 'none'");
}

/* REMOVED empty ruleset */
/* Style for cells beyond requested depth */
/* .text-gray-400.italic { */
    /* background-color: #f9fafb; */
/* } */
</style>