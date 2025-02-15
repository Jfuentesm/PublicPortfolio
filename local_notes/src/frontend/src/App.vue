<template>
    <div class="app-container">
      <div class="header-bar">
        <h1>Local Notes App</h1>
        <div class="view-toggle">
          <button @click="setViewMode('notes')" :class="{ active: viewMode === 'notes' }">
            Notes View
          </button>
          <button @click="setViewMode('kanban')" :class="{ active: viewMode === 'kanban' }">
            Kanban Board
          </button>
          <button @click="setViewMode('canvas')" :class="{ active: viewMode === 'canvas' }">
            Infinite Canvas
          </button>
          <!-- Daily Note Button -->
          <button @click="createDailyNote">
            Daily Note
          </button>
        </div>
      </div>
  
      <!-- Notes view: File explorer, single Tiptap editor, and task panel -->
      <div class="layout" v-if="viewMode === 'notes'">
        <!-- Left Pane: Note Explorer -->
        <section class="pane side">
          <NoteExplorer 
            :notes="notesList" 
            @selectNote="handleNoteSelected"
            @reloadNotes="fetchNotes"
          />
        </section>
  
        <!-- Center Pane: Editor -->
        <section class="pane main">
          <div class="editor-container">
            <EditorPane
              v-if="currentNotePath"
              :currentNoteContent="currentNoteContent"
              @updateContent="updateNoteContent"
            />
          </div>
        </section>
  
        <!-- Right Pane: Task Panel -->
        <section class="pane side tasks-side">
          <TaskPanel />
        </section>
      </div>
  
      <!-- Kanban view -->
      <div v-else-if="viewMode === 'kanban'">
        <KanbanBoard />
      </div>
  
      <!-- Infinite Canvas view -->
      <div v-else-if="viewMode === 'canvas'" class="canvas-view-container">
        <CanvasView />
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  import NoteExplorer from './components/NoteExplorer.vue'
  import EditorPane from './components/EditorPane.vue'
  import TaskPanel from './components/TaskPanel.vue'
  import KanbanBoard from './components/KanbanBoard.vue'
  import CanvasView from './components/CanvasView.vue'
  
  export default {
    name: 'App',
    components: {
      NoteExplorer,
      EditorPane,
      TaskPanel,
      KanbanBoard,
      CanvasView
    },
    data() {
      return {
        notesList: [],
        currentNotePath: null,
        currentNoteContent: '',
        viewMode: 'notes'  // options: 'notes', 'kanban', or 'canvas'
      }
    },
    mounted() {
      this.fetchNotes()
    },
    methods: {
      setViewMode(mode) {
        this.viewMode = mode
      },
      async fetchNotes() {
        try {
          const response = await axios.get('http://localhost:8000/notes')
          this.notesList = response.data.notes || []
        } catch (err) {
          console.error('App.vue: Failed to fetch notes:', err)
        }
      },
      handleNoteSelected(notePath) {
        this.currentNotePath = notePath
        this.fetchNoteContent(notePath)
      },
      async fetchNoteContent(notePath) {
        try {
          const response = await axios.get(`http://localhost:8000/notes/${notePath}`)
          this.currentNoteContent = response.data.content
        } catch (err) {
          console.error('App.vue: Failed to load note content:', err)
        }
      },
      async updateNoteContent(newContent) {
        if (!this.currentNotePath) return
        try {
          await axios.put(`http://localhost:8000/notes/${this.currentNotePath}`, {
            content: newContent
          })
          this.currentNoteContent = newContent
        } catch (err) {
          console.error('App.vue: Failed to update note content:', err)
        }
      },
      async createDailyNote() {
        try {
          const response = await axios.post('http://localhost:8000/notes/daily')
          const { note, content } = response.data
          this.currentNotePath = note
          this.currentNoteContent = content
          this.fetchNotes()
          this.viewMode = 'notes'
        } catch (err) {
          console.error('App.vue: Failed to create or open daily note:', err)
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
  
  .view-toggle {
    display: flex;
    gap: 0.5rem;
  }
  
  .view-toggle button {
    padding: 0.5rem 1rem;
    cursor: pointer;
  }
  
  .view-toggle button.active {
    background-color: #007acc;
    color: #fff;
    border: none;
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
  
  /* Single container for the TipTap Editor */
  .editor-container {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
  }
  
  .canvas-view-container {
    flex: 1;
    padding: 1rem;
  }
  </style>
  