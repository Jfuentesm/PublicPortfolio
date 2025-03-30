<template>
  <div class="space-y-8 md:space-y-12"> <!-- Adds vertical space between children -->
      <!-- Upload Form Section -->
      <section aria-labelledby="upload-heading">
          <div class="max-w-2xl mx-auto">
              <h2 id="upload-heading" class="sr-only">Upload Vendor File</h2> <!-- Screen reader heading -->
              <UploadForm @upload-successful="handleUploadSuccess" />
          </div>
      </section>

       <!-- Job Status Section -->
      <section aria-labelledby="status-heading" v-if="jobStore.currentJobId">
          <div class="max-w-4xl mx-auto">
              <h2 id="status-heading" class="sr-only">Job Status and Results</h2> <!-- Screen reader heading -->
              <JobStatus :key="jobStore.currentJobId" />
              <!-- key forces re-render if job ID changes -->
          </div>
      </section>

      <!-- Placeholder if no job active and logged in -->
      <div v-else class="text-center py-16 text-gray-500 bg-white rounded-lg shadow border border-gray-200">
          <p class="text-lg mb-2">No active job.</p>
          <p>Upload a file above to start the classification process.</p>
      </div>
  </div>
</template>

<script setup lang="ts">
import UploadForm from './UploadForm.vue';
import JobStatus from './JobStatus.vue';
import { useJobStore } from '@/stores/job';

const jobStore = useJobStore();

const handleUploadSuccess = (jobId: string) => {
  console.log(`AppContent: Received upload-successful event for job ${jobId}`);
  // The job store watcher will handle UI updates
  jobStore.setCurrentJobId(jobId);
};
</script>

<style scoped>
/* No scoped styles needed */
</style>