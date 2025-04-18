<template>
  <div class="space-y-8">
    <h1 class="text-3xl font-bold text-gray-800">Admin Dashboard</h1>

    <!-- System Stats Section -->
    <section>
      <h2 class="text-xl font-semibold text-gray-700 mb-4">System Overview</h2>
      <div v-if="adminStore.loadingStats" class="text-center py-4">
        <p class="text-gray-500">Loading system statistics...</p>
        <!-- Optional: Add a spinner -->
      </div>
      <div v-else-if="adminStore.errorStats" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">Error!</strong>
        <span class="block sm:inline"> Could not load system statistics: {{ adminStore.errorStats }}</span>
      </div>
      <div v-else-if="adminStore.systemStats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Stat Cards -->
        <StatCard title="Total Users" :value="adminStore.systemStats.total_users" icon="users" />
        <StatCard title="Total Jobs" :value="adminStore.systemStats.total_jobs" icon="briefcase" />
        <StatCard title="Active Jobs" :value="adminStore.systemStats.pending_jobs + adminStore.systemStats.processing_jobs" icon="cog" />
        <StatCard title="Failed Jobs (24h)" :value="adminStore.systemStats.failed_jobs_last_24h" icon="exclamation-triangle" :error="adminStore.systemStats.failed_jobs_last_24h > 0" />
        <StatCard title="Completed Jobs" :value="adminStore.systemStats.completed_jobs" icon="check-circle" />
        <!-- Add more cards as needed, e.g., for cost -->
      </div>
    </section>

    <!-- Recent Jobs Section -->
    <section>
      <h2 class="text-xl font-semibold text-gray-700 mb-4">Recent Jobs</h2>
       <div v-if="adminStore.loadingJobs" class="text-center py-4">
        <p class="text-gray-500">Loading recent jobs...</p>
      </div>
      <div v-else-if="adminStore.errorJobs" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">Error!</strong>
        <span class="block sm:inline"> Could not load recent jobs: {{ adminStore.errorJobs }}</span>
      </div>
      <div v-else-if="adminStore.recentJobs && adminStore.recentJobs.length > 0" class="overflow-x-auto bg-white shadow rounded-lg">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job ID</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="job in adminStore.recentJobs" :key="job.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 truncate" :title="job.id">
                {{ job.id.substring(0, 8) }}...
              </td>
               <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 truncate" :title="job.company_name">
                {{ job.company_name }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ job.created_by }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', jobTypeClass(job.job_type)]">
                  {{ job.job_type }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', statusClass(job.status)]">
                  {{ job.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDateTime(job.created_at) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
       <div v-else class="text-center py-4">
        <p class="text-gray-500">No recent jobs found.</p>
      </div>
    </section>

    <!-- Health Check Section -->
     <section>
      <h2 class="text-xl font-semibold text-gray-700 mb-4">System Health</h2>
        <div v-if="adminStore.loadingStats" class="text-center py-4">
            <p class="text-gray-500">Loading health status...</p>
        </div>
        <div v-else-if="adminStore.errorStats" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">Error!</strong>
            <span class="block sm:inline"> Could not load health status: {{ adminStore.errorStats }}</span>
        </div>
        <div v-else-if="adminStore.systemStats?.health_status" class="bg-white shadow rounded-lg p-4 space-y-2">
            <div v-for="(value, key) in adminStore.systemStats.health_status" :key="key" class="flex justify-between items-center text-sm">
                <span class="text-gray-600 capitalize">{{ key.replace(/_/g, ' ') }}:</span>
                <span :class="['font-medium', healthStatusClass(key, value)]">
                    {{ formatHealthValue(value) }}
                </span>
            </div>
        </div>
     </section>

     <!-- Consider adding User Management here as a sub-section -->
     <!-- <section>
        <h2 class="text-xl font-semibold text-gray-700 mb-4">User Management</h2>
        <UserManagement />
     </section> -->

  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useAdminStore } from '@/stores/admin'; // Ensure this path is correct
import StatCard from './StatCard.vue'; // Assuming you create this component
// import UserManagement from './UserManagement.vue'; // Import if embedding UserManagement

const adminStore = useAdminStore();

onMounted(() => {
  adminStore.fetchSystemStats();
  adminStore.fetchRecentJobs();
});

// --- Helper Functions for Display ---

const formatDateTime = (isoString: string | Date): string => {
  if (!isoString) return 'N/A';
  try {
    const date = typeof isoString === 'string' ? new Date(isoString) : isoString;
    return date.toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch (e) {
    console.error("Error formatting date:", isoString, e);
    return 'Invalid Date';
  }
};

const statusClass = (status: string): string => {
  switch (status?.toLowerCase()) {
    case 'completed': return 'bg-green-100 text-green-800';
    case 'processing': return 'bg-blue-100 text-blue-800';
    case 'pending': return 'bg-yellow-100 text-yellow-800';
    case 'failed': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const jobTypeClass = (type: string): string => {
  switch (type?.toUpperCase()) {
    case 'CLASSIFICATION': return 'bg-purple-100 text-purple-800';
    case 'REVIEW': return 'bg-pink-100 text-pink-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const formatHealthValue = (value: any): string => {
    if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
    }
    if (value === null || value === undefined) {
        return 'N/A';
    }
    if (typeof value === 'string' && value.startsWith('error:')) {
        return value.substring(6); // Remove 'error: ' prefix for display
    }
    // Truncate long strings (like detailed error messages)
    if (typeof value === 'string' && value.length > 50) {
        return value.substring(0, 47) + '...';
    }
    return String(value);
};

// --- UPDATED: Prefixed unused 'key' parameter with underscore ---
const healthStatusClass = (_key: string, value: any): string => {
    const stringValue = String(value).toLowerCase();

    if (stringValue.includes('error') || stringValue.includes('failed') || stringValue === 'missing' || value === false) {
        return 'text-red-600';
    }
    if (stringValue.includes('unknown') || stringValue.includes('placeholder')) {
        return 'text-yellow-600';
    }
    if (stringValue.includes('connected') || stringValue.includes('healthy') || stringValue === 'found' || stringValue === 'configured' || stringValue === 'api functional' || value === true) {
        return 'text-green-600';
    }
    return 'text-gray-700'; // Default
};
// --- END UPDATED ---

</script>

<style scoped>
/* Add any specific styles if needed */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>