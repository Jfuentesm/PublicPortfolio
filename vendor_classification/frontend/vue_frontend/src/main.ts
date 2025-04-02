// frontend/vue_frontend/src/main.ts

// Import necessary functions from installed libraries
// These imports should now resolve correctly after `npm install` and `tsconfig.json` fixes.
import { createApp } from 'vue';
import { createPinia } from 'pinia';

// Import the root Vue component
import App from './App.vue';

// Import global styles (Tailwind base/components/utilities + custom styles)
// Ensure this path is correct relative to main.ts
import './assets/styles.css';

// --- Optional: Add console log for confirmation during runtime ---
console.log("[main.ts] Initializing Vue application...");
// --- End Optional Logging ---

// Create the Vue application instance
const app = createApp(App);

// --- Optional: Add console log ---
console.log("[main.ts] Installing Pinia state management...");
// --- End Optional Logging ---

// Use the Pinia plugin for state management
// This provides the state stores (like authStore, jobStore) to your components.
app.use(createPinia());

// --- Optional: Add console log ---
console.log("[main.ts] Mounting the application to the '#app' element...");
// --- End Optional Logging ---

// Mount the application to the DOM element with the ID 'app' in index.html
// This renders your Vue application onto the page.
app.mount('#app');

// --- Optional: Add console log ---
console.log("[main.ts] Vue application mounted successfully.");
// --- End Optional Logging ---