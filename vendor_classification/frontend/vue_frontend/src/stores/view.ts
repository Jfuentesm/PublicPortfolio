// frontend/vue_frontend/src/stores/view.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useViewStore = defineStore('view', () => {
    // --- State ---
    // 'landing', 'app', 'admin'
    const currentView = ref<'landing' | 'app' | 'admin'>('landing');

    // --- Actions ---
    function setView(view: 'landing' | 'app' | 'admin'): void {
        console.log(`ViewStore: Setting view to '${view}'`);
        currentView.value = view;
    }

    return {
        currentView,
        setView,
    };
});