<!-- src/frontend/src/App.vue -->
<template>
  <div class="app-container">
      <div class="header-bar">
          <h1>Local Notes App</h1>
          <!-- Toggle button to switch between Kanban view & normal layout -->
          <button @click="toggleKanbanView">
              {{ showKanbanBoard ? 'Back to Notes View' : 'Show Kanban Board' }}
          </button>
      </div>

      <div class="layout" v-if="!showKanbanBoard">
          <!-- Left Pane: Note Explorer -->
          <section class="pane side">
              <NoteExplorer 
                  :notes="notesList" 
                  @selectNote="handleNoteSelected"
                  @reloadNotes="fetchNotes"
              />
          </section>

          <!-- Center Pane: Editor + Preview -->
          <section class="pane main">
              <div class="editor-preview-container">
                  <EditorPane
                      v-if="currentNotePath"
                      :currentNoteContent="currentNoteContent"
                      @updateContent="updateNoteContent"
                  />
                  <PreviewPane
                      v-if="currentNoteContent"
                      :markdownText="currentNoteContent"
                  />
              </div>
          </section>

          <!-- Right Pane: Task Panel -->
          <section class="pane side tasks-side">
              <TaskPanel />
          </section>
      </div>

      <!-- If Kanban toggle is active, show the Kanban board -->
      <KanbanBoard v-else />
  </div>
</template>

<script>
import axios from 'axios'
import NoteExplorer from './components/NoteExplorer.vue'
import EditorPane from './components/EditorPane.vue'
import PreviewPane from './components/PreviewPane.vue'
import TaskPanel from './components/TaskPanel.vue'
import KanbanBoard from './components/KanbanBoard.vue'

/**
* App.vue
*
* The top-level component that manages the main layout. We add:
* - A header bar with a toggle button to switch views (Kanban or standard).
* - The default layout with NoteExplorer, Editor/Preview, and TaskPanel.
* - The Kanban board in place of the default layout when toggled on.
*/
export default {
  name: 'App',

  components: {
      NoteExplorer,
      EditorPane,
      PreviewPane,
      TaskPanel,
      KanbanBoard
  },

  data() {
      return {
          notesList: [],
          currentNotePath: null,
          currentNoteContent: '',
          showKanbanBoard: false    // Controls whether Kanban is displayed
      }
  },

  mounted() {
      this.fetchNotes()
  },

  methods: {
      /**
       * Toggles the boolean that controls whether to show the Kanban view.
       */
      toggleKanbanView() {
          this.showKanbanBoard = !this.showKanbanBoard
      },

      /**
       * Fetches the list of notes (filenames) from the backend.
       */
      async fetchNotes() {
          try {
              const response = await axios.get('http://localhost:8000/notes')
              this.notesList = response.data.notes || []
          } catch (err) {
              console.error('App.vue: Failed to fetch notes:', err)
          }
      },

      /**
       * Called when a note is selected from the NoteExplorer. Sets the current
       * note path and loads its content.
       * @param {String} notePath - The relative path of the selected note
       */
      handleNoteSelected(notePath) {
          this.currentNotePath = notePath
          this.fetchNoteContent(notePath)
      },

      /**
       * Fetches the content of the specified note from the backend.
       * @param {String} notePath
       */
      async fetchNoteContent(notePath) {
          try {
              const response = await axios.get(`http://localhost:8000/notes/${notePath}`)
              this.currentNoteContent = response.data.content
          } catch (err) {
              console.error('App.vue: Failed to load note content:', err)
          }
      },

      /**
       * Updates the content of the current note (PUT request to the backend).
       * @param {String} newContent - The updated markdown content
       */
      async updateNoteContent(newContent) {
          if (!this.currentNotePath) {
              return
          }
          try {
              await axios.put(`http://localhost:8000/notes/${this.currentNotePath}`, {
                  content: newContent
              })
              this.currentNoteContent = newContent
          } catch (err) {
              console.error('App.vue: Failed to update note content:', err)
          }
      }
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  margin: 0;
  font-family: sans-serif;
  box-sizing: border-box;
}

.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f3f3f3;
  padding: 0.5rem;
  border-bottom: 1px solid #ccc;
}

.layout {
  flex: 1;
  display: flex;
  flex-direction: row;
}

.pane {
  border: 1px solid #ccc;
  box-sizing: border-box;
  padding: 0.5rem;
}

.side {
  width: 20%;
  overflow-y: auto;
}

.tasks-side {
  width: 25%;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-preview-container {
  display: flex;
  flex-direction: row;
  height: 100%;
}

.editor-preview-container > * {
  width: 50%;
  padding: 0.5rem;
  box-sizing: border-box;
  border-right: 1px dashed #ccc;
}

.editor-preview-container > *:last-child {
  border-right: none;
}
</style>