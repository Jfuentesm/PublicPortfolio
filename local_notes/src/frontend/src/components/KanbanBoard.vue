<!-- src/frontend/src/components/KanbanBoard.vue -->
<template>
    <div class="kanban-container">
        <!-- Title / heading -->
        <h2>Kanban Board</h2>
        <p class="kanban-instructions">
            Drag and drop tasks between columns to update their status.
        </p>

        <div class="columns">
            <!-- TODO Column -->
            <div 
                class="column" 
                @drop.prevent="onDrop('TODO')" 
                @dragover.prevent
            >
                <h3>TODO</h3>
                <div 
                    v-for="task in todoTasks" 
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>

            <!-- IN_PROGRESS Column -->
            <div 
                class="column" 
                @drop.prevent="onDrop('IN_PROGRESS')" 
                @dragover.prevent
            >
                <h3>In Progress</h3>
                <div
                    v-for="task in inProgressTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>

            <!-- COMPLETED Column -->
            <div 
                class="column" 
                @drop.prevent="onDrop('COMPLETED')" 
                @dragover.prevent
            >
                <h3>Completed</h3>
                <div
                    v-for="task in completedTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios'

/**
 * KanbanBoard.vue
 *
 * A component that displays tasks in columns by status. Users can drag a
 * task card from one status column to another to update the status automatically.
 */
export default {
    name: 'KanbanBoard',

    data() {
        return {
            tasks: [],           // Array of all tasks from the backend
            draggedTask: null    // Task user is currently dragging
        }
    },

    computed: {
        /**
         * Filter tasks by TODO status.
         * @returns {Array} The tasks with status='TODO'
         */
        todoTasks() {
            return this.tasks.filter(task => task.status === 'TODO')
        },
        /**
         * Filter tasks by IN_PROGRESS status.
         * @returns {Array} The tasks with status='IN_PROGRESS'
         */
        inProgressTasks() {
            return this.tasks.filter(task => task.status === 'IN_PROGRESS')
        },
        /**
         * Filter tasks by COMPLETED status.
         * @returns {Array} The tasks with status='COMPLETED'
         */
        completedTasks() {
            return this.tasks.filter(task => task.status === 'COMPLETED')
        }
    },

    mounted() {
        this.fetchTasks()
    },

    methods: {
        /**
         * Fetches all tasks from the backend and populates this.tasks array.
         */
        async fetchTasks() {
            try {
                let response = await axios.get('http://localhost:8000/tasks')
                this.tasks = response.data
            } catch (error) {
                console.error('KanbanBoard: Failed to fetch tasks:', error)
            }
        },

        /**
         * Handler for dragstart event: sets the draggedTask data.
         * @param {Object} task - The task being dragged.
         */
        onDragStart(task) {
            this.draggedTask = task
        },

        /**
         * Handler for drop event on a column: updates the dragged task's status
         * to match the drop column.
         * @param {String} newStatus - The status representing the column
         */
        async onDrop(newStatus) {
            if (!this.draggedTask) {
                return
            }
            // Only update if the status is actually changing.
            if (this.draggedTask.status === newStatus) {
                this.draggedTask = null
                return
            }
            try {
                await axios.put(`http://localhost:8000/tasks/${this.draggedTask.id}`, {
                    status: newStatus
                })
                // Reload tasks from the server to reflect the update
                this.fetchTasks()
            } catch (error) {
                console.error('KanbanBoard: Error updating task status:', error)
            }
            this.draggedTask = null
        }
    }
}
</script>

<style scoped>
.kanban-container {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    height: 100%;
    box-sizing: border-box;
}

.kanban-instructions {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 1rem;
}

.columns {
    display: flex;
    gap: 1rem;
    flex: 1;
}

/* A single column */
.column {
    flex: 1;
    border: 1px solid #ccc;
    min-height: 300px;
    padding: 0.5rem;
    box-sizing: border-box;
    background-color: #fafafa;
}

/* Each task card in a column */
.task-card {
    background: #fff;
    margin-bottom: 0.5rem;
    padding: 0.5rem;
    border: 1px solid #ddd;
    cursor: grab;
}
.task-card:active {
    cursor: grabbing;
}
</style>