<template>
  <div class="card shadow-sm">
    <div class="card-header bg-primary text-white">
      <h4 class="mb-0">Upload Vendor File</h4>
    </div>
    <div class="card-body">
      <!-- Use v-show to hide/show messages without layout shift -->
      <div v-show="successMessage" class="alert alert-success">{{ successMessage }}</div>
      <div v-show="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

      <form @submit.prevent="handleUpload" enctype="multipart/form-data">
        <div class="mb-3">
          <label for="companyName" class="form-label">Company Name <span class="text-danger">*</span></label>
          <input
            type="text"
            class="form-control"
            id="companyName"
            v-model="companyName"
            required
            :disabled="isLoading"
            placeholder="Your Company Inc."
          >
        </div>
        <div class="mb-3">
          <label for="vendorFile" class="form-label">Vendor Excel File <span class="text-danger">*</span></label>
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
          <div class="form-text">
              Requires '.xlsx' or '.xls' format with a column named 'vendor_name'. <br/>
              Optional columns for context: 'vendor_address', 'vendor_website', 'internal_category', 'parent_company', 'spend_category', 'optional_example_good_serviced_purchased'.
          </div>
        </div>
        <button type="submit" class="btn btn-primary w-100" :disabled="isLoading || !selectedFile">
           <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
          {{ isLoading ? ' Uploading & Processing...' : 'Upload and Process' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import apiService from '@/services/api'; // Adjust path as needed
import { useJobStore } from '@/stores/job'; // Import job store

const jobStore = useJobStore(); // Use the job store
const companyName = ref('');
const selectedFile = ref<File | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null); // Ref for the file input element
const isLoading = ref(false);
const successMessage = ref<string | null>(null);
const errorMessage = ref<string | null>(null);

// Emit an event when upload is successful and job is started
const emit = defineEmits(['upload-successful']);

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
    // Clear messages when a new file is selected
    errorMessage.value = null;
    successMessage.value = null;
  } else {
    selectedFile.value = null;
  }
};

const handleUpload = async () => {
  if (!selectedFile.value || !companyName.value) {
    errorMessage.value = 'Please provide a company name and select a file.';
    successMessage.value = null; // Clear success message
    return;
  }

  isLoading.value = true;
  successMessage.value = null; // Clear previous success message
  errorMessage.value = null; // Clear previous error message

  // Clear previous job state before starting a new one
  jobStore.clearJob();

  const formData = new FormData();
  formData.append('company_name', companyName.value);
  formData.append('file', selectedFile.value);

  try {
    const response = await apiService.uploadFile(formData); // Use your API service
    console.log('Upload successful, job started:', response);
    successMessage.value = `Upload successful! Job ${response.job_id} started. Monitoring status below...`;
    emit('upload-successful', response.job_id); // Emit event with the new job ID

    // Reset form after successful upload
    companyName.value = '';
    selectedFile.value = null;
    if (fileInputRef.value) {
        fileInputRef.value.value = ''; // Clear the file input visually
    }

  } catch (error: any) {
    console.error('Upload error:', error);
    // Use the error message prepared by the interceptor
    errorMessage.value = error.message || 'An unexpected error occurred during upload.';
     // Clear success message on error
    successMessage.value = null;

  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.card-header h4 {
    font-weight: 500;
}
.form-text {
    line-height: 1.4;
}
.alert { /* Ensure alerts have some margin */
    margin-bottom: 1rem;
}
</style>