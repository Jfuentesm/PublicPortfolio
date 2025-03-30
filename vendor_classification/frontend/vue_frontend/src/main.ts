import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import './assets/styles.css'; // Import custom styles AFTER potential framework styles


const app = createApp(App);

app.use(createPinia());

app.mount('#app');