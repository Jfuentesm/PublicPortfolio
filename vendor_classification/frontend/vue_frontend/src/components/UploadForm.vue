<template>
    <div class="card mb-4">
      <div class="card-header bg-primary text-white">
        <h4 class="mb-0">Upload Vendor File</h4>
      </div>
      <div class="card-body">
        <div v-if="successMessage" class="success-message mb-3">{{ successMessage }}</div>
        <div v-if="errorMessage" class="error-message mb-3">{{ errorMessage }}</div>
        <form @submit.prevent="handleUpload" enctype="multipart/form-data">
          <div class="mb-3">
            <label for="companyName" class="form-label">Company Name</label>
            <input type="text" class="form-control" id="companyName" v-model="companyName" required :disabled="isLoading">
          </div>
          <div class="mb-3">
            <label for="vendorFile" class="form-label">Vendor Excel File</label>
            <input
              type="file"
              class="form-control"
              id="vendorFile"
              ref="fileInputRef"
              @change="handleFileChange"
              accept=".xlsx,.xls"
              required
              :disabled="isLoading"
            >
            <div class="form-text">Upload an Excel file with a 'vendor_name' column. Optional columns like 'vendor_address', 'vendor_website', 'optional_example_good_serviced_purchased', etc., can provide helpful context.</div>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="isLoading || !selectedFile">
            {{ isLoading ? 'Uploading...' : 'Upload and Process' }}
          </button>
        </form>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import apiService from '@/services/api'; // Adjust path as needed
  
  const companyName = ref('');
  const selectedFile = ref<File | null>(null);
  const fileInputRef = ref<HTMLInputElement | null>(null); // Ref for the file input element
  const isLoading = ref(false);
  const successMessage = ref<string | null>(null);
  const errorMessage = ref<string | null>(null);
  
  const emit = defineEmits(['upload-successful']);
  
  const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      selectedFile.value = target.files[0];
      errorMessage.value = null; // Clear error when file is selected
    } else {
      selectedFile.value = null;
    }
  };
  
  const handleUpload = async () => {
    if (!selectedFile.value || !companyName.value) {
      errorMessage.value = 'Please provide a company name and select a file.';
      return;
    }
  
    isLoading.value = true;
    successMessage.value = null;
    errorMessage.value = null;
  
    const formData = new FormData();
    formData.append('company_name', companyName.value);
    formData.append('file', selectedFile.value);
  
    try {
      const response = await apiService.uploadFile(formData); // Use your API service
      console.log('Upload successful, job started:', response);
      successMessage.value = `Upload successful! Job ${response.job_id} started. Monitoring status...`;
      emit('upload-successful', response.job_id);
  
      // Reset form after successful upload
      companyName.value = '';
      selectedFile.value = null;
      if (fileInputRef.value) {
          fileInputRef.value.value = ''; // Clear the file input visually
      }
  
    } catch (error: any) {
      console.error('Upload error:', error);
      errorMessage.value = error.message || 'An unexpected error occurred during upload.';
      // Consider more specific error handling based on error type/status code
       if (error.response?.data?.detail) {
           // Handle FastAPI validation errors specifically
           if (Array.isArray(error.response.data.detail)) {
                errorMessage.value = `Validation Error: ${error.response.data.detail.map((err: any) => `${err.loc.join('.')} - ${err.msg}`).join('; ')}`;
           } else {
                errorMessage.value = `Upload Error: ${error.response.data.detail}`;
           }
       }
    } finally {
      isLoading.value = false;
    }
  };
  </script>
  
  <style scoped>
  .error-message { color: #dc3545; font-size: 0.875em; }
  .success-message { color: #198754; font-size: 0.875em; }
  </style>