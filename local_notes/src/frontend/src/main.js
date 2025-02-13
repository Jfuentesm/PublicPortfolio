/**
 * main.js
 *
 * The main entry point for the Vue app. Creates the Vue application,
 * mounts it to #app in index.html, and configures global dependencies.
 */

import { createApp } from 'vue'
import App from './App.vue'

// Create the app instance
const app = createApp(App)

// Mount it to <div id="app"> in index.html
app.mount('#app')