
<template>
  <div class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
    <div class="bg-primary text-white p-4 sm:p-5">
      <h4 class="text-xl font-semibold mb-0">Upload Vendor File</h4>
    </div>
    <div class="p-6 sm:p-8">
      <!-- Success Alert -->
      <div v-if="successMessage" class="mb-5 p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm flex items-center">
          <CheckCircleIcon class="h-5 w-5 mr-2 text-green-600 flex-shrink-0"/>
          <span>{{ successMessage }}</span>
      </div>
       <!-- Error Alert -->
      <div v-if="errorMessage" class="mb-5 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm flex items-center">
           <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-red-600 flex-shrink-0"/>
          <span>{{ errorMessage }}</span>
      </div>

      <form @submit.prevent="handleUpload" enctype="multipart/form-data">
        <div class="mb-5">
          <label for="companyName" class="block text-sm font-medium text-gray-700 mb-1.5">
              Company Name <span class="text-red-500">*</span>
          </label>
          <input
            type="text"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-60 disabled:bg-gray-100 disabled:cursor-not-allowed"
            id="companyName"
            v-model="companyName"
            required
            :disabled="isLoading"
            placeholder="e.g., Your Company Inc."
          />
        </div>

        <!-- ADDED: Target Level Selection -->
        <div class="mb-5">
          <label for="targetLevel" class="block text-sm font-medium text-gray-700 mb-1.5">
              Target Classification Level <span class="text-red-500">*</span>
          </label>
          <select
            id="targetLevel"
            v-model.number="selectedLevel"
            required
            :disabled="isLoading"
            class="block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-60 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="1">Level 1 (Sector)</option>
            <option value="2">Level 2 (Subsector)</option>
            <option value="3">Level 3 (Industry Group)</option>
            <option value="4">Level 4 (NAICS Industry)</option>
            <option value="5">Level 5 (National Industry)</option>
          </select>
          <p class="mt-1 text-xs text-gray-500">Select the maximum NAICS level you want the classification to reach.</p>
        </div>
        <!-- END ADDED -->

        <div class="mb-6">
          <label for="vendorFile" class="block text-sm font-medium text-gray-700 mb-1.5">
              Vendor Excel File <span class="text-red-500">*</span>
          </label>
          <input
            type="file"
            class="block w-full text-sm text-gray-500 border border-gray-300 rounded-md cursor-pointer bg-gray-50 focus:outline-none focus:ring-primary focus:border-primary file:mr-4 file:py-2 file:px-4 file:rounded-l-md file:border-0 file:text-sm file:font-semibold file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200 disabled:opacity-60 disabled:cursor-not-allowed"
            id="vendorFile"
            ref="fileInputRef"
            @change="handleFileChange"
            accept=".xlsx,.xls"
            required
            :disabled="isLoading"
          />
          <p class="mt-2 text-xs text-gray-500">
              Requires '.xlsx' or '.xls'. Must contain 'vendor_name' column.
              <br/>Optional context columns enhance accuracy (address, website, example, etc.).
          </p>
        </div>
        <button type="submit" class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed" :disabled="isLoading || !selectedFile">
           <svg v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
           </svg>
           <ArrowUpTrayIcon v-else class="h-5 w-5 mr-2 -ml-1" />
          {{ isLoading ? ' Uploading & Processing...' : 'Upload and Process' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import apiService from '@/services/api';
import { useJobStore } from '@/stores/job';
import { ArrowUpTrayIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/20/solid'; // Using solid icons

const jobStore = useJobStore();
const companyName = ref('');
const selectedFile = ref<File | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const isLoading = ref(false);
const successMessage = ref<string | null>(null);
const errorMessage = ref<string | null>(null);
// --- ADDED: State for selected level ---
const selectedLevel = ref<number>(5); // Default to Level 5
// --- END ADDED ---

const emit = defineEmits(['upload-successful']);

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
    errorMessage.value = null;
    successMessage.value = null;
  } else {
    selectedFile.value = null;
  }
};

const handleUpload = async () => {
  if (!selectedFile.value || !companyName.value) {
    errorMessage.value = 'Please provide a company name and select a file.';
    successMessage.value = null;
    return;
  }
  // --- ADDED: Validate selected level ---
  if (selectedLevel.value < 1 || selectedLevel.value > 5) {
    errorMessage.value = 'Please select a valid target level (1-5).';
    successMessage.value = null;
    return;
  }
  // --- END ADDED ---

  isLoading.value = true;
  successMessage.value = null;
  errorMessage.value = null;
  jobStore.clearJob();
  const formData = new FormData();
  formData.append('company_name', companyName.value);
  formData.append('file', selectedFile.value);
  // --- ADDED: Append selected level to form data ---
  formData.append('target_level', selectedLevel.value.toString());
  // --- END ADDED ---

  try {
    const response = await apiService.uploadFile(formData); // apiService.uploadFile now handles FormData directly
    successMessage.value = `Upload successful! Job ${response.job_id} started (Target Level: ${selectedLevel.value}). Monitoring status below...`;
    emit('upload-successful', response.job_id);
    // Reset form fields
    companyName.value = '';
    selectedFile.value = null;
    selectedLevel.value = 5; // Reset level to default
    if (fileInputRef.value) {
        fileInputRef.value.value = '';
    }
  } catch (error: any) {
    errorMessage.value = error.message || 'An unexpected error occurred during upload.';
    successMessage.value = null;
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Style the file input button more effectively */
input[type="file"]::file-selector-button {
    /* Tailwind handles most, but you can add custom tweaks */
    cursor: pointer;
}
</style>