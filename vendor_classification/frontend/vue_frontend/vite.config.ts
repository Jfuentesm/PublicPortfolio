// frontend/vue_frontend/vite.config.ts
// No changes needed based on errors, assuming tsconfig.node.json is set up correctly
import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173, // Default Vite port
    proxy: {
      // Proxy API requests starting with /api or /token to the backend server
      // Change target based on where your FastAPI backend runs locally
      '/api': {
        target: 'http://localhost:8001', // Your FastAPI backend port from run_local.sh
        changeOrigin: true,
        // secure: false, // Uncomment if backend uses self-signed certs
        // rewrite: (path) => path.replace(/^\/api/, '/api') // Keep prefix if backend expects it
      },
       '/token': { // Proxy the /token endpoint separately if it's not under /api
        target: 'http://localhost:8001',
        changeOrigin: true,
        // secure: false,
      }
    }
  }
})