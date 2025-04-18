// frontend/vue_frontend/src/stores/admin.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiService from '@/services/api'; // Adjust path as needed
import type { SystemStatsResponse, RecentJobItem } from '@/services/api'; // Import specific types

export const useAdminStore = defineStore('admin', () => {
    // --- State ---
    const systemStats = ref<SystemStatsResponse | null>(null);
    const recentJobs = ref<RecentJobItem[] | null>(null);
    const loadingStats = ref(false);
    const loadingJobs = ref(false);
    const errorStats = ref<string | null>(null);
    const errorJobs = ref<string | null>(null);

    // --- Actions ---
    async function fetchSystemStats(): Promise<void> {
        loadingStats.value = true;
        errorStats.value = null;
        console.log('AdminStore: Fetching system stats...');
        try {
            const stats = await apiService.getSystemStats();
            systemStats.value = stats;
            console.log('AdminStore: System stats fetched successfully.');
        } catch (err: any) {
            console.error('AdminStore: Failed to fetch system stats:', err);
            errorStats.value = err.message || 'An unknown error occurred while fetching system stats.';
            systemStats.value = null; // Clear potentially stale data on error
        } finally {
            loadingStats.value = false;
        }
    }

    async function fetchRecentJobs(limit: number = 15): Promise<void> {
        loadingJobs.value = true;
        errorJobs.value = null;
        console.log(`AdminStore: Fetching recent jobs (limit=${limit})...`);
        try {
            // Pass limit to apiService if the function supports it
            const response = await apiService.getRecentJobs(limit);
            recentJobs.value = response.jobs;
            console.log(`AdminStore: Fetched ${recentJobs.value?.length ?? 0} recent jobs.`);
        } catch (err: any) {
            console.error('AdminStore: Failed to fetch recent jobs:', err);
            errorJobs.value = err.message || 'An unknown error occurred while fetching recent jobs.';
            recentJobs.value = null; // Clear potentially stale data on error
        } finally {
            loadingJobs.value = false;
        }
    }

    // --- Getters (Implicit via refs, or add computed if needed) ---
    // Example computed getter (though direct refs are often fine in setup scripts)
    // const activeJobCount = computed(() => {
    //   if (!systemStats.value) return 0;
    //   return systemStats.value.pending_jobs + systemStats.value.processing_jobs;
    // });

    return {
        // State
        systemStats,
        recentJobs,
        loadingStats,
        loadingJobs,
        errorStats,
        errorJobs,

        // Actions
        fetchSystemStats,
        fetchRecentJobs,

        // Getters (if defined)
        // activeJobCount,
    };
});