<template>
  <div class="tiptap-container">
    <h3>WYSIWYG Editor</h3>
    <!-- Use EditorContent to render the Tiptap editor -->
    <EditorContent :editor="editor" class="tiptap-editor" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Markdown from '@tiptap/extension-markdown'

// 1) Define props (from parent)
const props = defineProps({
  currentNoteContent: {
    type: String,
    default: ''
  }
})

// 2) Define events we emit back up
const emit = defineEmits(['updateContent'])

// 3) Create the Tiptap editor
const editor = useEditor({
  extensions: [
    StarterKit,
    Markdown
  ],
  content: props.currentNoteContent, // initial Markdown from parent
  onUpdate({ editor }) {
    // Get updated Markdown from Tiptap
    const updatedMarkdown = editor.storage.markdown.getMarkdown()
    // Send it up to the parent
    emit('updateContent', updatedMarkdown)
  },
})

// 4) If parent prop changes externally, update the editor
watch(
  () => props.currentNoteContent,
  (newVal) => {
    if (!editor.value) return
    const currentMarkdown = editor.value.storage.markdown.getMarkdown()
    // Only reset if the parent differs from Tiptap’s current content
    if (newVal !== currentMarkdown) {
      editor.value.commands.setContent(newVal)
    }
  }
)

// 5) Clean up the editor on unmount
onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy()
  }
})
</script>

<style scoped>
.tiptap-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tiptap-editor {
  flex: 1;
  border: 1px solid #ddd;
  padding: 1rem;
  min-height: 300px;
}
</style>
