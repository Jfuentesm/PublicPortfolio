<template>
  <div>
    <div class="row">
      <!-- Adjust column layout as needed -->
      <div class="col-lg-6 col-md-8 offset-lg-3 offset-md-2">
          <!-- Upload Form -->
          <UploadForm @upload-successful="handleUploadSuccess" />
      </div>
    </div>
     <div class="row mt-4">
       <div class="col-lg-8 col-md-10 offset-lg-2 offset-md-1">
           <!-- Job Status (conditionally rendered based on jobStore) -->
          <JobStatus v-if="jobStore.currentJobId" :key="jobStore.currentJobId" />
          <!-- key forces re-render if job ID changes -->
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

<style scoped>
/* Add spacing or specific layout styles for the logged-in view */
</style>