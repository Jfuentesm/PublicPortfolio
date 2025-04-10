// frontend/vue_frontend/src/main.ts
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import './assets/styles.css';

// --- REMOVED Unused Import ---
// import { useViewStore } from './stores/view';
// --- END REMOVED ---

console.log("[main.ts] Initializing Vue application...");

const app = createApp(App);
const pinia = createPinia(); // Create Pinia instance

console.log("[main.ts] Installing Pinia state management...");
app.use(pinia); // Use Pinia

// Stores are typically initialized within components or App.vue setup

console.log("[main.ts] Mounting the application to the '#app' element...");
app.mount('#app');

console.log("[main.ts] Vue application mounted successfully.");