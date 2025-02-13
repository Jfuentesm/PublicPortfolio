<template>
    <div class="preview-pane">
      <h3>Preview</h3>
      <div
        class="preview-content"
        v-html="renderedMarkdown"
      />
    </div>
  </template>
  
  <script>
  import { marked } from 'marked'
  
  export default {
    name: 'PreviewPane',
    props: {
      markdownText: {
        type: String,
        default: ''
      }
    },
    computed: {
      renderedMarkdown() {
        // Use 'marked' to convert the raw markdown text into HTML
        return marked(this.markdownText || '')
      }
    }
  }
  </script>
  
  <style scoped>
  .preview-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .preview-content {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
    background: #f9f9f9;
    border: 1px solid #ddd;
  }
  </style>
  