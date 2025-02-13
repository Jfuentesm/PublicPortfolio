<template>
  <div class="note-explorer">
    <h2>Notes</h2>

    <div class="notes-list">
      <ul>
        <li
          v-for="(note, idx) in notes"
          :key="idx"
          @click="select(note)"
          class="note-item"
        >
          {{ note }}
        </li>
      </ul>
    </div>
    <div class="actions">
      <input
        v-model="newNoteName"
        placeholder="New note name..."
        @keydown.enter="createNote"
      />
      <button @click="createNote">Create Note</button>
      <button @click="reloadNotes">Reload</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'NoteExplorer',
  props: {
    notes: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      newNoteName: ''
    }
  },
  methods: {
    select(notePath) {
      // Notify parent that a note was selected
      this.$emit('selectNote', notePath)
    },
    createNote() {
      if (!this.newNoteName) return
      axios.post('http://localhost:8000/notes', {
        note_name: this.newNoteName
      })
      .then(() => {
        this.newNoteName = ''
        // Refresh the parent’s note list
        this.$emit('reloadNotes')
      })
      .catch(err => {
        console.error('Failed to create note:', err)
      })
    },
    reloadNotes() {
      this.$emit('reloadNotes')
    }
  }
}
</script>

<style scoped>
.note-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notes-list {
  flex: 1;
  overflow-y: auto;
}

.note-item {
  cursor: pointer;
  padding: 4px;
  border-bottom: 1px solid #eee;
}

.note-item:hover {
  background: #fafafa;
}

.actions {
  margin-top: 0.5rem;
}

.actions input {
  width: 60%;
  padding: 4px;
  margin-right: 0.5rem;
}
</style>
