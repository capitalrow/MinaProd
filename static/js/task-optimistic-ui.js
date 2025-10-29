/**
 * CROWN⁴.5 Optimistic UI Update System
 * Applies changes instantly to DOM, queues to IndexedDB, syncs to server.
 * Provides <150ms reconciliation on success, rollback on failure.
 */

class OptimisticUI {
    constructor() {
        this.cache = window.taskCache;
        this.pendingOperations = new Map();
        this.operationCounter = 0;
    }

    /**
     * Create task optimistically
     * @param {Object} taskData
     * @returns {Promise<Object>} Created task
     */
    async createTask(taskData) {
        const opId = this._generateOperationId();
        const tempId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const optimisticTask = {
            id: tempId,
            ...taskData,
            status: taskData.status || 'todo',
            priority: taskData.priority || 'medium',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            _optimistic: true,
            _operation_id: opId
        };

        try {
            // Step 1: Update DOM immediately (<50ms)
            this._addTaskToDOM(optimisticTask);
            
            // Step 2: Save to IndexedDB
            await this.cache.saveTask(optimisticTask);
            
            // Step 3: Queue event and offline operation via OfflineQueueManager
            await this.cache.addEvent({
                event_type: 'task_create',
                task_id: tempId,
                data: taskData,
                timestamp: Date.now()
            });

            // Use OfflineQueueManager for proper session tracking and replay
            if (window.offlineQueue) {
                await window.offlineQueue.queueOperation({
                    type: 'task_create',
                    temp_id: tempId,
                    data: taskData,
                    priority: 10
                });
            }

            // Step 4: Sync to server
            this.pendingOperations.set(opId, { type: 'create', tempId, task: optimisticTask });
            this._syncToServer(opId, 'create', taskData, tempId);

            return optimisticTask;
        } catch (error) {
            console.error('❌ Optimistic create failed:', error);
            this._rollbackCreate(tempId);
            throw error;
        }
    }

    /**
     * Update task optimistically
     * @param {number|string} taskId
     * @param {Object} updates
     * @returns {Promise<Object>} Updated task
     */
    async updateTask(taskId, updates) {
        const opId = this._generateOperationId();
        
        try {
            // Get current task
            const currentTask = await this.cache.getTask(taskId);
            if (!currentTask) {
                throw new Error('Task not found');
            }

            // Create optimistic version
            const optimisticTask = {
                ...currentTask,
                ...updates,
                updated_at: new Date().toISOString(),
                _optimistic: true,
                _operation_id: opId
            };

            // Step 1: Update DOM immediately
            this._updateTaskInDOM(taskId, optimisticTask);
            
            // Step 2: Update IndexedDB
            await this.cache.saveTask(optimisticTask);
            
            // Step 3: Queue event via OfflineQueueManager
            await this.cache.addEvent({
                event_type: 'task_update',
                task_id: taskId,
                data: updates,
                timestamp: Date.now()
            });

            // Use OfflineQueueManager for proper session tracking and replay
            if (window.offlineQueue) {
                await window.offlineQueue.queueOperation({
                    type: 'task_update',
                    task_id: taskId,
                    data: updates,
                    priority: 5
                });
            }

            // Step 4: Sync to server
            this.pendingOperations.set(opId, { type: 'update', taskId, previous: currentTask, updates });
            this._syncToServer(opId, 'update', updates, taskId);

            return optimisticTask;
        } catch (error) {
            console.error('❌ Optimistic update failed:', error);
            throw error;
        }
    }

    /**
     * Delete task optimistically
     * @param {number|string} taskId
     * @returns {Promise<void>}
     */
    async deleteTask(taskId) {
        const opId = this._generateOperationId();
        
        try {
            // Get task for rollback
            const task = await this.cache.getTask(taskId);
            if (!task) {
                throw new Error('Task not found');
            }

            // Step 1: Remove from DOM immediately
            this._removeTaskFromDOM(taskId);
            
            // Step 2: Delete from IndexedDB
            await this.cache.deleteTask(taskId);
            
            // Step 3: Queue event via OfflineQueueManager
            await this.cache.addEvent({
                event_type: 'task_delete',
                task_id: taskId,
                timestamp: Date.now()
            });

            // Use OfflineQueueManager for proper session tracking and replay
            if (window.offlineQueue) {
                await window.offlineQueue.queueOperation({
                    type: 'task_delete',
                    task_id: taskId,
                    priority: 8
                });
            }

            // Step 4: Sync to server
            this.pendingOperations.set(opId, { type: 'delete', taskId, task });
            this._syncToServer(opId, 'delete', null, taskId);

        } catch (error) {
            console.error('❌ Optimistic delete failed:', error);
            throw error;
        }
    }

    /**
     * Toggle task status optimistically
     * @param {number|string} taskId
     * @returns {Promise<Object>}
     */
    async toggleTaskStatus(taskId) {
        const task = await this.cache.getTask(taskId);
        if (!task) return;

        const newStatus = task.status === 'completed' ? 'todo' : 'completed';
        const updates = {
            status: newStatus,
            completed_at: newStatus === 'completed' ? new Date().toISOString() : null
        };

        return this.updateTask(taskId, updates);
    }

    /**
     * Snooze task optimistically
     * @param {number|string} taskId
     * @param {Date} snoozeUntil
     * @returns {Promise<Object>}
     */
    async snoozeTask(taskId, snoozeUntil) {
        return this.updateTask(taskId, {
            snoozed_until: snoozeUntil.toISOString()
        });
    }

    /**
     * Update task priority optimistically
     * @param {number|string} taskId
     * @param {string} priority
     * @returns {Promise<Object>}
     */
    async updatePriority(taskId, priority) {
        return this.updateTask(taskId, { priority });
    }

    /**
     * Add label to task optimistically
     * @param {number|string} taskId
     * @param {string} label
     * @returns {Promise<Object>}
     */
    async addLabel(taskId, label) {
        const task = await this.cache.getTask(taskId);
        if (!task) return;

        const labels = task.labels || [];
        if (!labels.includes(label)) {
            labels.push(label);
        }

        return this.updateTask(taskId, { labels });
    }

    /**
     * Generate unique operation ID
     * @returns {string}
     */
    _generateOperationId() {
        return `op_${Date.now()}_${++this.operationCounter}`;
    }

    /**
     * Add task to DOM
     * @param {Object} task
     */
    _addTaskToDOM(task) {
        const container = document.getElementById('tasks-list-container');
        if (!container) return;

        const taskHTML = window.taskBootstrap.renderTaskCard(task, 0);
        container.insertAdjacentHTML('afterbegin', taskHTML);

        // Add animation
        const card = container.querySelector(`[data-task-id="${task.id}"]`);
        if (card) {
            card.classList.add('optimistic-create');
            card.style.animation = 'slideInFromTop 0.3s ease-out';
        }

        // Hide empty state
        const emptyState = document.getElementById('tasks-empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        // Update counters
        this._updateCounters();
    }

    /**
     * Update task in DOM
     * @param {number|string} taskId
     * @param {Object} task
     */
    _updateTaskInDOM(taskId, task) {
        const card = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!card) return;

        // Update title
        const titleEl = card.querySelector('.task-title');
        if (titleEl && task.title) {
            titleEl.textContent = task.title;
        }

        // Update description
        const descEl = card.querySelector('.task-description');
        if (task.description) {
            if (descEl) {
                descEl.textContent = task.description;
            } else {
                const contentEl = card.querySelector('.task-content');
                if (contentEl) {
                    const descHTML = `<p class="task-description">${this._escapeHtml(task.description)}</p>`;
                    contentEl.insertAdjacentHTML('afterbegin', descHTML);
                }
            }
        }

        // Update status
        if (task.status) {
            card.dataset.status = task.status;
            const checkbox = card.querySelector('.task-checkbox');
            if (checkbox) {
                checkbox.checked = task.status === 'completed';
            }
            if (task.status === 'completed') {
                card.classList.add('completed');
                if (titleEl) titleEl.classList.add('completed');
            } else {
                card.classList.remove('completed');
                if (titleEl) titleEl.classList.remove('completed');
            }
        }

        // Update priority
        if (task.priority) {
            card.dataset.priority = task.priority;
            const priorityBadge = card.querySelector('.priority-badge');
            if (priorityBadge) {
                priorityBadge.className = `priority-badge priority-${task.priority.toLowerCase()}`;
                priorityBadge.textContent = task.priority;
            }
        }

        // Add optimistic indicator
        card.classList.add('optimistic-update');
        setTimeout(() => card.classList.remove('optimistic-update'), 300);

        this._updateCounters();
    }

    /**
     * Remove task from DOM
     * @param {number|string} taskId
     */
    _removeTaskFromDOM(taskId) {
        const card = document.querySelector(`[data-task-id="${taskId}"]`);
        if (!card) return;

        card.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        card.style.opacity = '0';
        card.style.transform = 'translateX(-20px)';

        setTimeout(() => {
            card.remove();
            this._updateCounters();

            // Show empty state if no tasks left
            const remaining = document.querySelectorAll('.task-card').length;
            if (remaining === 0) {
                const emptyState = document.getElementById('tasks-empty-state');
                if (emptyState) {
                    emptyState.style.display = 'block';
                }
            }
        }, 300);
    }

    /**
     * Update task counters
     */
    _updateCounters() {
        const cards = document.querySelectorAll('.task-card');
        const counters = {
            all: cards.length,
            todo: 0,
            in_progress: 0,
            completed: 0,
            overdue: 0
        };

        cards.forEach(card => {
            const status = card.dataset.status || 'todo';
            if (counters[status] !== undefined) {
                counters[status]++;
            }
        });

        Object.entries(counters).forEach(([key, count]) => {
            const badge = document.querySelector(`[data-counter="${key}"]`);
            if (badge) {
                badge.textContent = count;
            }
        });
    }

    /**
     * Sync operation to server
     * @param {string} opId
     * @param {string} type
     * @param {Object} data
     * @param {number|string} taskId
     */
    async _syncToServer(opId, type, data, taskId) {
        const startTime = performance.now();

        try {
            let response;

            if (type === 'create') {
                response = await fetch('/api/tasks/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(data)
                });
            } else if (type === 'update') {
                response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(data)
                });
            } else if (type === 'delete') {
                response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin'
                });
            }

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const result = await response.json();
            const reconcileTime = performance.now() - startTime;

            console.log(`✅ Optimistic ${type} reconciled in ${reconcileTime.toFixed(2)}ms`);

            // Reconcile with server data
            await this._reconcileSuccess(opId, type, result, taskId);

            // Emit telemetry
            if (window.CROWNTelemetry) {
                window.CROWNTelemetry.recordMetric('optimistic_reconcile_ms', reconcileTime);
            }

        } catch (error) {
            console.error(`❌ Server sync failed for ${type}:`, error);
            await this._reconcileFailure(opId, type, taskId);
        }
    }

    /**
     * Reconcile successful server response
     * @param {string} opId
     * @param {string} type
     * @param {Object} serverData
     * @param {number|string} taskId
     */
    async _reconcileSuccess(opId, type, serverData, taskId) {
        const operation = this.pendingOperations.get(opId);
        if (!operation) return;

        if (type === 'create') {
            // Replace temp ID with real ID
            const realTask = serverData.task || serverData;
            const tempId = operation.tempId;

            // Update DOM
            const card = document.querySelector(`[data-task-id="${tempId}"]`);
            if (card) {
                card.dataset.taskId = realTask.id;
                card.classList.remove('optimistic-create');
            }

            // Update cache
            await this.cache.deleteTask(tempId);
            await this.cache.saveTask(realTask);

        } else if (type === 'update') {
            // Update with server truth
            const realTask = serverData.task || serverData;
            await this.cache.saveTask(realTask);
            this._updateTaskInDOM(taskId, realTask);
        }

        // Remove operation
        this.pendingOperations.delete(opId);

        // Mark event as synced
        const events = await this.cache.getPendingEvents();
        const relatedEvent = events.find(e => e.task_id === taskId || e.task_id === operation.tempId);
        if (relatedEvent) {
            await this.cache.markEventSynced(relatedEvent.id);
        }
    }

    /**
     * Reconcile failed server sync (rollback)
     * @param {string} opId
     * @param {string} type
     * @param {number|string} taskId
     */
    async _reconcileFailure(opId, type, taskId) {
        const operation = this.pendingOperations.get(opId);
        if (!operation) return;

        if (type === 'create') {
            // Rollback create
            this._rollbackCreate(operation.tempId);
        } else if (type === 'update') {
            // Rollback to previous state
            await this.cache.saveTask(operation.previous);
            this._updateTaskInDOM(taskId, operation.previous);
        } else if (type === 'delete') {
            // Restore deleted task
            await this.cache.saveTask(operation.task);
            this._addTaskToDOM(operation.task);
        }

        this.pendingOperations.delete(opId);

        // Show error notification
        this._showErrorNotification(`Failed to ${type} task. Changes rolled back.`);
    }

    /**
     * Rollback task creation
     * @param {string} tempId
     */
    async _rollbackCreate(tempId) {
        this._removeTaskFromDOM(tempId);
        await this.cache.deleteTask(tempId);
    }

    /**
     * Show error notification
     * @param {string} message
     */
    _showErrorNotification(message) {
        if (window.showToast) {
            window.showToast(message, 'error');
        } else {
            console.error(message);
        }
    }

    /**
     * Escape HTML
     * @param {string} text
     * @returns {string}
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export singleton
window.optimisticUI = new OptimisticUI();

console.log('⚡ CROWN⁴.5 OptimisticUI loaded');
