
<!-- <file path='frontend/vue_frontend/src/components/UploadForm.vue'> -->
<template>
    <div class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
      <div class="bg-primary text-white p-4 sm:p-5">
        <h4 class="text-xl font-semibold mb-0">Upload Vendor File</h4>
      </div>
      <div class="p-6 sm:p-8">
        <!-- Job Success Alert -->
        <div v-if="jobSuccessMessage" class="mb-5 p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm flex items-center">
            <CheckCircleIcon class="h-5 w-5 mr-2 text-green-600 flex-shrink-0"/>
            <span>{{ jobSuccessMessage }}</span>
        </div>
         <!-- Job Error Alert -->
        <div v-if="jobErrorMessage" class="mb-5 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm flex items-center">
             <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-red-600 flex-shrink-0"/>
            <span>{{ jobErrorMessage }}</span>
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
              :disabled="isUploading"
              placeholder="e.g., Your Company Inc."
            />
          </div>

          <!-- Target Level Selection -->
          <div class="mb-5">
            <label for="targetLevel" class="block text-sm font-medium text-gray-700 mb-1.5">
                Target Classification Level <span class="text-red-500">*</span>
            </label>
            <select
              id="targetLevel"
              v-model.number="selectedLevel"
              required
              :disabled="isUploading"
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

          <!-- File Input -->
          <div class="mb-5">
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
              :disabled="isUploading"
            />
            <p class="mt-2 text-xs text-gray-500">
                Requires '.xlsx' or '.xls'. Must contain 'vendor_name' column.
                <br/>Optional context columns enhance accuracy (address, website, example, etc.).
            </p>
          </div>

          <!-- Validation Status Area -->
          <div v-if="validationStatus !== 'idle'" class="mb-5 p-3 rounded-md text-sm border" :class="{
            'bg-blue-50 border-blue-200 text-blue-700': validationStatus === 'loading',
            'bg-green-50 border-green-300 text-green-800': validationStatus === 'success',
            'bg-red-50 border-red-300 text-red-800': validationStatus === 'error'
          }">
            <div class="flex items-center">
              <svg v-if="validationStatus === 'loading'" class="animate-spin h-4 w-4 mr-2 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <CheckCircleIcon v-if="validationStatus === 'success'" class="h-5 w-5 mr-2 text-green-600 flex-shrink-0"/>
              <ExclamationTriangleIcon v-if="validationStatus === 'error'" class="h-5 w-5 mr-2 text-red-600 flex-shrink-0"/>
              <span class="font-medium">
                {{ validationStatus === 'loading' ? 'Validating file...' : (validationStatus === 'success' ? 'Validation Passed' : 'Validation Failed') }}
              </span>
            </div>
            <p v-if="validationMessage" class="mt-1 ml-7 text-xs">{{ validationMessage }}</p>
            <div v-if="validationStatus === 'success' && detectedColumns.length > 0" class="mt-2 ml-7">
                <p class="text-xs font-medium mb-1">Detected Columns:</p>
                <ul class="list-disc list-inside text-xs space-y-0.5 max-h-20 overflow-y-auto bg-white p-2 rounded border border-gray-200">
                    <li v-for="col in detectedColumns" :key="col" :class="{'font-semibold text-green-700': col.toLowerCase().includes('vendor_name')}">
                        {{ col }}
                    </li>
                </ul>
            </div>
          </div>
          <!-- End Validation Status Area -->

          <button type="submit" class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isUploading || validationStatus !== 'success' || !selectedFile || !companyName"
            title="Requires Company Name, valid file selection, and successful file validation."
          >
             <svg v-if="isUploading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
             <ArrowUpTrayIcon v-else class="h-5 w-5 mr-2 -ml-1" />
            {{ isUploading ? ' Uploading & Processing...' : 'Upload and Process' }}
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
  const isUploading = ref(false); // Renamed from isLoading for clarity
  const jobSuccessMessage = ref<string | null>(null); // For job submission success
  const jobErrorMessage = ref<string | null>(null); // For job submission errors
  const selectedLevel = ref<number>(5); // Default to Level 5

  // --- ADDED: Validation State ---
  type ValidationStatus = 'idle' | 'loading' | 'success' | 'error';
  const validationStatus = ref<ValidationStatus>('idle');
  const validationMessage = ref<string | null>(null);
  const detectedColumns = ref<string[]>([]);
  // --- END ADDED ---

  const emit = defineEmits(['upload-successful']);

  const resetValidation = () => {
      validationStatus.value = 'idle';
      validationMessage.value = null;
      detectedColumns.value = [];
  };

  const handleFileChange = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    resetValidation(); // Reset previous validation state
    jobSuccessMessage.value = null; // Clear previous job messages
    jobErrorMessage.value = null;

    if (target.files && target.files.length > 0) {
      const file = target.files[0];
      selectedFile.value = file;

      // --- Trigger Validation ---
      validationStatus.value = 'loading';
      validationMessage.value = null;
      detectedColumns.value = [];

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await apiService.validateUpload(formData);
        validationMessage.value = response.message;
        detectedColumns.value = response.detected_columns || [];
        if (response.is_valid) {
          validationStatus.value = 'success';
        } else {
          validationStatus.value = 'error';
          // Optionally clear the file input if validation fails severely
          // selectedFile.value = null;
          // if (fileInputRef.value) fileInputRef.value.value = '';
        }
      } catch (error: any) {
        validationStatus.value = 'error';
        // Use the detailed error message from api.ts interceptor
        validationMessage.value = error.message || 'An unexpected error occurred during file validation.';
        detectedColumns.value = [];
        // Clear file selection on validation API error
        selectedFile.value = null;
        if (fileInputRef.value) fileInputRef.value.value = '';
      }
      // --- End Trigger Validation ---

    } else {
      selectedFile.value = null;
      resetValidation();
    }
  };

  const handleUpload = async () => {
    // Double check conditions, though button should be disabled
    if (!selectedFile.value || !companyName.value || validationStatus.value !== 'success') {
      jobErrorMessage.value = 'Please provide company name, select a valid file, and ensure file validation passes.';
      jobSuccessMessage.value = null;
      return;
    }
    if (selectedLevel.value < 1 || selectedLevel.value > 5) {
      jobErrorMessage.value = 'Please select a valid target level (1-5).';
      jobSuccessMessage.value = null;
      return;
    }

    isUploading.value = true;
    jobSuccessMessage.value = null;
    jobErrorMessage.value = null;
    jobStore.clearJob(); // Clear any previous job being monitored

    const formData = new FormData();
    formData.append('company_name', companyName.value);
    formData.append('file', selectedFile.value);
    formData.append('target_level', selectedLevel.value.toString());

    try {
      const response = await apiService.uploadFile(formData);
      jobSuccessMessage.value = `Upload successful! Job ${response.id} started (Target Level: ${response.target_level}). Monitoring status below...`;
      emit('upload-successful', response.id);
      jobStore.setCurrentJobId(response.id); // Set the current job in the store

      // Reset form fields after successful submission
      companyName.value = '';
      selectedFile.value = null;
      selectedLevel.value = 5; // Reset level to default
      resetValidation(); // Reset validation state as well
      if (fileInputRef.value) {
          fileInputRef.value.value = '';
      }
    } catch (error: any) {
      // Use the detailed error message from api.ts interceptor
      jobErrorMessage.value = error.message || 'An unexpected error occurred during upload.';
      jobSuccessMessage.value = null;
    } finally {
      isUploading.value = false;
    }
  };
  </script>

  <style scoped>
  /* Style the file input button more effectively */
  input[type="file"]::file-selector-button {
      /* Tailwind handles most, but you can add custom tweaks */
      cursor: pointer;
  }

  /* Style for the detected columns list */
  .max-h-20 {
      max-height: 5rem; /* 80px */
  }
  </style>
