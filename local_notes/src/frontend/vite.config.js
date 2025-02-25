import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    // Optional: The proxy ensures requests to "/notes", "/tasks", etc. go to http://127.0.0.1:8000
    proxy: {
      '/notes': 'http://127.0.0.1:8000',
      '/tasks': 'http://127.0.0.1:8000',
      '/backup': 'http://127.0.0.1:8000',
      '/search': 'http://127.0.0.1:8000'
    }
  }
})