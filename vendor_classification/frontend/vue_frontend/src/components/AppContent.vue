<template>
    <div>
      <div class="row">
        <div class="col-md-8 offset-md-2">
          <UploadForm @upload-successful="handleUploadSuccess" />
          <JobStatus v-if="jobStore.currentJobId" :key="jobStore.currentJobId" />
          <!-- JobStats could be conditionally shown within JobStatus when completed -->
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import UploadForm from './UploadForm.vue';
  import JobStatus from './JobStatus.vue';
  import { useJobStore } from '@/stores/job'; // Adjust path
  
  const jobStore = useJobStore();
  
  const handleUploadSuccess = (jobId: string) => {
    console.log(`AppContent: Received upload-successful event for job ${jobId}`);
    jobStore.setCurrentJobId(jobId); // Update the store, JobStatus will react
  };
  </script>