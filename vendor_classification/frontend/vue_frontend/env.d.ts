/// <reference types="vite/client" />

// Add this declaration for *.vue files
declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
  }