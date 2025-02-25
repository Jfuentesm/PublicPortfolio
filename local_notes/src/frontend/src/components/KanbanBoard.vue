<template>
    <div class="kanban-container">
        <h2>Kanban Board</h2>
        <p class="kanban-instructions">
            Drag and drop tasks between columns to update their status.
        </p>

        <div class="columns">
            <!-- TODO Column -->
            <div class="column" @drop.prevent="onDrop('TODO')" @dragover.prevent>
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

            <!-- In Progress Column -->
            <div class="column" @drop.prevent="onDrop('IN_PROGRESS')" @dragover.prevent>
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

            <!-- Completed Column -->
            <div class="column" @drop.prevent="onDrop('COMPLETED')" @dragover.prevent>
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
    </div>
</template>

<script>
import axios from 'axios'

/**
 * KanbanBoard.vue
 *
 * This component implements a Kanban board for task management.
 * Tasks are grouped by their status (TODO, IN_PROGRESS, COMPLETED) and can be
 * dragged between columns to update their status. Additional task metadata
 * (due date, priority, recurrence) is also displayed.
 */
export default {
    name: 'KanbanBoard',
    data() {
        return {
            tasks: [],        // Array to store all tasks from the backend
            draggedTask: null // Currently dragged task object
        }
    },
    computed: {
        /**
         * Returns tasks with status 'TODO'.
         */
        todoTasks() {
            return this.tasks.filter(task => task.status === 'TODO')
        },
        /**
         * Returns tasks with status 'IN_PROGRESS'.
         */
        inProgressTasks() {
            return this.tasks.filter(task => task.status === 'IN_PROGRESS')
        },
        /**
         * Returns tasks with status 'COMPLETED'.
         */
        completedTasks() {
            return this.tasks.filter(task => task.status === 'COMPLETED')
        }
    },
    mounted() {
        // Fetch tasks when component is mounted.
        this.fetchTasks()
    },
    methods: {
        /**
         * Fetch tasks from the backend and update local tasks array.
         */
        async fetchTasks() {
            try {
                const response = await axios.get('http://localhost:8000/tasks')
                this.tasks = response.data
            } catch (error) {
                console.error('KanbanBoard: Failed to fetch tasks:', error)
            }
        },

        /**
         * Handler for dragstart event.
         * Sets the current dragged task.
         *
         * @param {Object} task - The task object that is being dragged.
         */
        onDragStart(task) {
            this.draggedTask = task
        },

        /**
         * Handler for drop event on a column.
         * Updates the dragged task's status based on the column dropped into.
         *
         * @param {String} newStatus - The status representing the target column.
         */
        async onDrop(newStatus) {
            if (!this.draggedTask) {
                return
            }
            if (this.draggedTask.status === newStatus) {
                this.draggedTask = null
                return
            }
            try {
                // For recurring tasks, use the complete endpoint if moving to COMPLETED.
                if (this.draggedTask.recurrence && this.draggedTask.due_date) {
                    if (newStatus === 'COMPLETED') {
                        await axios.post(
                            `http://localhost:8000/tasks/${this.draggedTask.id}/complete`
                        )
                    } else {
                        await axios.put(
                            `http://localhost:8000/tasks/${this.draggedTask.id}`,
                            { status: newStatus }
                        )
                    }
                } else {
                    await axios.put(
                        `http://localhost:8000/tasks/${this.draggedTask.id}`,
                        { status: newStatus }
                    )
                }
                // Refresh tasks after updating.
                this.fetchTasks()
            } catch (error) {
                console.error('KanbanBoard: Error updating task status:', error)
            }
            this.draggedTask = null
        },

        /**
         * Formats a date string into a locale-specific date.
         *
         * @param {String} dateStr - The date string.
         * @returns {String} Formatted date.
         */
        formatDate(dateStr) {
            const date = new Date(dateStr)
            return date.toLocaleDateString()
        },

        /**
         * Converts numeric priority to a human-readable string.
         *
         * @param {Number} priority - The task priority.
         * @returns {String} The formatted priority string.
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
.kanban-container {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    height: 100%;
    box-sizing: border-box;
    font-family: sans-serif;
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

.column {
    flex: 1;
    border: 1px solid #ccc;
    min-height: 300px;
    padding: 0.5rem;
    box-sizing: border-box;
    background-color: #fafafa;
}

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
