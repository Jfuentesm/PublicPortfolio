<template>
    <div class="editor-pane">
      <h3>Editor</h3>
      <textarea
        v-model="editorContent"
        class="editor-textarea"
        @input="onContentChange"
      />
    </div>
  </template>
  
  <script>
  export default {
    name: 'EditorPane',
    props: {
      currentNoteContent: {
        type: String,
        default: ''
      }
    },
    data() {
      return {
        editorContent: this.currentNoteContent
      }
    },
    watch: {
      // If the prop changes externally (e.g. when selecting a different note),
      // sync it back to the local data
      currentNoteContent(newVal) {
        this.editorContent = newVal
      }
    },
    methods: {
      onContentChange() {
        // Emit event to update note content in the parent
        this.$emit('updateContent', this.editorContent)
      }
    }
  }
  </script>
  
  <style scoped>
  .editor-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .editor-textarea {
    flex: 1;
    resize: none;
    width: 100%;
    height: calc(100% - 2rem);
    font-family: monospace;
    font-size: 14px;
    padding: 8px;
    box-sizing: border-box;
  }
  </style>
  