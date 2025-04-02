<template>
  <div class="space-y-8 md:space-y-12"> <!-- Adds vertical space between children -->
      <!-- Upload Form Section -->
      <section aria-labelledby="upload-heading">
          <div class="max-w-2xl mx-auto">
              <h2 id="upload-heading" class="sr-only">Upload Vendor File</h2> <!-- Screen reader heading -->
              <UploadForm @upload-successful="handleUploadSuccess" />
          </div>
      </section>

       <!-- Job Status Section (for currently selected job) -->
      <section aria-labelledby="status-heading" v-if="jobStore.currentJobId">
          <div class="max-w-4xl mx-auto">
              <h2 id="status-heading" class="sr-only">Current Job Status and Results</h2> <!-- Screen reader heading -->
              <JobStatus :key="jobStore.currentJobId" />
              <!-- key forces re-render if job ID changes -->
          </div>
      </section>

      <!-- Placeholder if no job active and logged in -->
      <div v-else class="text-center py-16 text-gray-500 bg-white rounded-lg shadow border border-gray-200 max-w-4xl mx-auto">
          <p class="text-lg mb-2">No active job selected.</p>
          <p>Upload a file above to start a new classification, or select a job from the history below.</p>
      </div>

      <!-- Job History Section -->
      <section aria-labelledby="history-heading">
          <div class="max-w-6xl mx-auto"> <!-- Wider container for table -->
               <h2 id="history-heading" class="sr-only">Job History</h2> <!-- Screen reader heading -->
               <JobHistory />
          </div>
      </section>

  </div>
</template>

<script setup lang="ts">
import UploadForm from './UploadForm.vue';
import JobStatus from './JobStatus.vue';
import JobHistory from './JobHistory.vue'; // <-- Import JobHistory
import { useJobStore } from '@/stores/job';

const jobStore = useJobStore();

const handleUploadSuccess = (jobId: string) => {
  console.log(`AppContent: Received upload-successful event for job ${jobId}`);
  jobStore.setCurrentJobId(jobId);
  // Optionally trigger a refresh of the history list after a short delay
  setTimeout(() => {
      jobStore.fetchJobHistory({ limit: 100 });
  }, 1500);
};
</script>

<style scoped>
/* No scoped styles needed */
</style>