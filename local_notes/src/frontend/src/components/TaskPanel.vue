<!-- src/frontend/src/components/TaskPanel.vue -->
<template>
  <div class="task-panel">
      <h2>Tasks</h2>
      
      <div class="task-form">
          <input
              v-model="newTaskTitle"
              placeholder="New task title..."
              @keydown.enter="createTask"
          />
          <button @click="createTask">Add Task</button>
      </div>

      <div class="task-list">
          <div 
              v-for="task in tasks"
              :key="task.id"
              class="task-item"
          >
              <label>
                  <input
                      type="checkbox"
                      :checked="task.status === 'COMPLETED'"
                      @change="toggleComplete(task)"
                  />
                  <strong>{{ task.title }}</strong>
              </label>
              <p v-if="task.description">{{ task.description }}</p>
              <small>Status: {{ task.status }}</small>
          </div>
      </div>
  </div>
</template>

<script>
import axios from 'axios'

/**
* TaskPanel.vue
*
* A right-hand panel that displays tasks in a simple list.
* Users can create new tasks and toggle their completion status.
*/
export default {
  name: 'TaskPanel',

  data() {
      return {
          tasks: [],
          newTaskTitle: ''
      }
  },

  mounted() {
      this.fetchTasks()
  },

  methods: {
      /**
       * Fetches all tasks from the backend.
       */
      async fetchTasks() {
          try {
              let response = await axios.get('http://localhost:8000/tasks')
              this.tasks = response.data
          } catch (err) {
              console.error('TaskPanel: Failed to fetch tasks:', err)
          }
      },

      /**
       * Creates a new task with minimal data (title only).
       */
      async createTask() {
          if (!this.newTaskTitle) {
              return
          }
          try {
              await axios.post('http://localhost:8000/tasks', {
                  title: this.newTaskTitle
              })
              this.newTaskTitle = ''
              this.fetchTasks()
          } catch (err) {
              console.error('TaskPanel: Failed to create task:', err)
          }
      },

      /**
       * Toggles the task's status. If currently COMPLETED, revert to TODO.
       * Otherwise, set it to COMPLETED. 
       * Note: For recurring tasks, you might call /tasks/{id}/complete
       * instead of a plain PUT update.
       * @param {Object} task - The task object being toggled
       */
      async toggleComplete(task) {
          try {
              if (task.status === 'COMPLETED') {
                  await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                      status: 'TODO'
                  })
              } else {
                  await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                      status: 'COMPLETED'
                  })
              }
              this.fetchTasks()
          } catch (err) {
              console.error('TaskPanel: Failed to toggle task:', err)
          }
      }
  }
}
</script>

<style scoped>
.task-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.task-form {
  margin-bottom: 1rem;
}

.task-list {
  flex: 1;
  overflow-y: auto;
}

.task-item {
  border-bottom: 1px solid #eee;
  padding: 0.5rem 0;
}
</style>