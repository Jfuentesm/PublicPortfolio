<template>
  <div class="task-panel">
      <h2>Tasks</h2>
      <!-- Task creation form with extended fields -->
      <div class="task-form">
          <input
              v-model="newTaskTitle"
              placeholder="New task title..."
          />
          <input
              v-model="newTaskDescription"
              placeholder="Description"
          />
          <input
              type="date"
              v-model="newTaskDueDate"
              placeholder="Due Date"
          />
          <select v-model="newTaskPriority">
              <option value="1">High</option>
              <option value="2">Medium</option>
              <option value="3">Low</option>
          </select>
          <input
              v-model="newTaskRecurrence"
              placeholder="Recurrence (daily, weekly, monthly)"
          />
          <button @click="createTask">Add Task</button>
          <button @click="fetchTasks">Reload</button>
      </div>

      <!-- Task list display -->
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
                      @change="handleComplete(task)"
                  />
                  <strong>{{ task.title }}</strong>
              </label>
              <p v-if="task.description">{{ task.description }}</p>
              <small v-if="task.due_date">
                  Due: {{ formatDate(task.due_date) }}
              </small>
              <small>
                  Priority: {{ formatPriority(task.priority) }}
              </small>
              <small v-if="task.recurrence">
                  Recurrence: {{ task.recurrence }}
              </small>
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
* This component displays a panel for managing tasks.
* It allows users to create new tasks with extended fields (description,
* due date, priority, recurrence) and displays the list of tasks.
* It also handles marking tasks complete using the appropriate backend endpoint.
*/
export default {
  name: 'TaskPanel',
  data() {
      return {
          tasks: [],                // Array holding all tasks from the backend
          newTaskTitle: '',         // Title for new task
          newTaskDescription: '',   // Description for new task
          newTaskDueDate: '',       // Due date (as a string) for new task
          newTaskPriority: '2',     // Default priority (2 = Medium)
          newTaskRecurrence: ''     // Recurrence rule (if any)
      }
  },
  mounted() {
      // Fetch tasks once the component is mounted
      this.fetchTasks()
  },
  methods: {
      /**
       * Fetch all tasks from the backend.
       */
      async fetchTasks() {
          try {
              const response = await axios.get('http://localhost:8000/tasks')
              this.tasks = response.data
          } catch (error) {
              console.error('TaskPanel: Failed to fetch tasks:', error)
          }
      },

      /**
       * Create a new task with the given details.
       * Converts the due date to a Date object if provided.
       */
      async createTask() {
          if (!this.newTaskTitle) {
              return
          }
          try {
              const payload = {
                  title: this.newTaskTitle,
                  description: this.newTaskDescription,
                  due_date: this.newTaskDueDate
                      ? new Date(this.newTaskDueDate)
                      : null,
                  priority: parseInt(this.newTaskPriority),
                  recurrence: this.newTaskRecurrence || null
              }
              await axios.post('http://localhost:8000/tasks', payload)
              // Reset form fields
              this.newTaskTitle = ''
              this.newTaskDescription = ''
              this.newTaskDueDate = ''
              this.newTaskPriority = '2'
              this.newTaskRecurrence = ''
              // Refresh the task list
              this.fetchTasks()
          } catch (error) {
              console.error('TaskPanel: Failed to create task:', error)
          }
      },

      /**
       * Handle the task completion toggle.
       * If the task has a recurrence rule and a due date, call the complete endpoint.
       * Otherwise, simply update the status.
       *
       * @param {Object} task - The task object to update.
       */
      async handleComplete(task) {
          try {
              if (task.recurrence && task.due_date) {
                  // For recurring tasks, use the dedicated complete endpoint.
                  await axios.post(`http://localhost:8000/tasks/${task.id}/complete`)
              } else {
                  // Toggle the status between TODO and COMPLETED.
                  if (task.status !== 'COMPLETED') {
                      await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                          status: 'COMPLETED'
                      })
                  } else {
                      await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                          status: 'TODO'
                      })
                  }
              }
              // Refresh tasks after update.
              this.fetchTasks()
          } catch (error) {
              console.error('TaskPanel: Failed to update task status:', error)
          }
      },

      /**
       * Format a date string into a locale-specific date.
       *
       * @param {String} dateStr - The date string.
       * @returns {String} Formatted date.
       */
      formatDate(dateStr) {
          const date = new Date(dateStr)
          return date.toLocaleDateString()
      },

      /**
       * Format the numeric priority into a human-readable string.
       *
       * @param {Number} priority - The priority value.
       * @returns {String} Formatted priority.
       */
      formatPriority(priority) {
          switch (priority) {
              case 1:
                  return 'High'
              case 2:
                  return 'Medium'
              case 3:
                  return 'Low'
              default:
                  return priority
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
  font-family: sans-serif;
  padding: 0.5rem;
  box-sizing: border-box;
}

.task-form {
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.task-form input,
.task-form select {
  padding: 4px;
  font-size: 0.9rem;
}

.task-form button {
  padding: 4px 8px;
  cursor: pointer;
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
