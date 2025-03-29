import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import './assets/styles.css'; // Import custom styles AFTER potential framework styles

// Optional: If using Bootstrap JS components via import (instead of CDN in index.html)
// import 'bootstrap/dist/js/bootstrap.bundle.min.js';

const app = createApp(App);

app.use(createPinia());

app.mount('#app');