/**
 * CROWN⁴.5 Task Bootstrap - Cache-First Architecture
 * Achieves <200ms first paint by loading from IndexedDB first,
 * then syncing with server in background.
 */

class TaskBootstrap {
    constructor() {
        this.cache = window.taskCache;
        this.initialized = false;
        this.syncInProgress = false;
        this.lastSyncTimestamp = null;
        this.perf = {
            cache_load_start: 0,
            cache_load_end: 0,
            first_paint: 0,
            sync_start: 0,
            sync_end: 0
        };
    }

    /**
     * Hydrate IndexedDB cache from server-rendered tasks
     * CRITICAL: This prevents bootstrap from clearing SSR tasks on first load
     * @returns {Promise<Array>} Hydrated tasks
     */
    async hydrateFromServerRender() {
        if (!window.__INITIAL_TASKS__ || !Array.isArray(window.__INITIAL_TASKS__)) {
            console.log('📭 No server-rendered tasks to hydrate');
            return [];
        }

        const tasks = window.__INITIAL_TASKS__;
        console.log(`💧 Hydrating cache with ${tasks.length} server-rendered tasks`);

        // Write each task to IndexedDB
        for (const task of tasks) {
            await this.cache.upsertTask(task);
        }

        console.log(`✅ Cache hydrated with ${tasks.length} tasks`);
        return tasks;
    }

    /**
     * Bootstrap tasks page with cache-first loading
     * Target: <200ms first paint
     * @returns {Promise<Object>} Bootstrap results
     */
    async bootstrap() {
        console.log('🚀 Starting CROWN⁴.5 cache-first bootstrap...');
        this.perf.cache_load_start = performance.now();

        try {
            // Step 1: Load from cache immediately (target: <50ms)
            let cachedTasks = await this.loadFromCache();
            
            // CRITICAL: On first load, hydrate from server-rendered tasks
            if (cachedTasks.length === 0 && !this.initialized) {
                console.log('🔄 First load detected, hydrating from SSR...');
                cachedTasks = await this.hydrateFromServerRender();
            }
            
            this.perf.cache_load_end = performance.now();
            
            const cacheLoadTime = this.perf.cache_load_end - this.perf.cache_load_start;
            console.log(`📦 Cache loaded in ${cacheLoadTime.toFixed(2)}ms (${cachedTasks.length} tasks)`);

            // Step 2: Render UI immediately (target: <200ms total)
            await this.renderTasks(cachedTasks, { fromCache: true });
            this.perf.first_paint = performance.now();
            
            const firstPaintTime = this.perf.first_paint - this.perf.cache_load_start;
            console.log(`🎨 First paint in ${firstPaintTime.toFixed(2)}ms`);

            // Emit performance metric
            if (window.CROWNTelemetry) {
                window.CROWNTelemetry.recordMetric('first_paint_ms', firstPaintTime);
                window.CROWNTelemetry.recordMetric('cache_load_ms', cacheLoadTime);
            }

            // Step 3: Start background sync
            this.syncInBackground();

            this.initialized = true;

            return {
                success: true,
                cached_tasks: cachedTasks.length,
                cache_load_ms: cacheLoadTime,
                first_paint_ms: firstPaintTime,
                meets_target: firstPaintTime < 200
            };
        } catch (error) {
            console.error('❌ Bootstrap failed:', error);
            
            // Fallback: Load from server directly
            return this.fallbackToServer();
        }
    }

    /**
     * Load tasks from IndexedDB cache
     * @returns {Promise<Array>} Cached tasks
     */
    async loadFromCache() {
        await this.cache.init();

        // Load view state (filters, sort, scroll position)
        const viewState = await this.cache.getViewState('tasks_page') || {
            filter: 'all',
            sort: { field: 'created_at', direction: 'desc' },
            scroll_position: 0
        };

        // Load tasks with filters
        const filters = this.buildFiltersFromViewState(viewState);
        const tasks = await this.cache.getFilteredTasks(filters);

        // Apply sort
        const sortedTasks = this.sortTasks(tasks, viewState.sort);

        return sortedTasks;
    }

    /**
     * Build filter object from view state
     * @param {Object} viewState
     * @returns {Object} Filters
     */
    buildFiltersFromViewState(viewState) {
        const filters = {};

        if (viewState.status && viewState.status !== 'all') {
            filters.status = viewState.status;
        }

        if (viewState.priority && viewState.priority !== 'all') {
            filters.priority = viewState.priority;
        }

        if (viewState.search) {
            filters.search = viewState.search;
        }

        if (viewState.labels && viewState.labels.length > 0) {
            filters.labels = viewState.labels;
        }

        if (viewState.due_date) {
            filters.due_date = viewState.due_date;
        }

        // Hide snoozed by default
        filters.show_snoozed = viewState.show_snoozed !== false;

        return filters;
    }

    /**
     * Sort tasks by field and direction
     * @param {Array} tasks
     * @param {Object} sort - { field, direction }
     * @returns {Array} Sorted tasks
     */
    sortTasks(tasks, sort = { field: 'created_at', direction: 'desc' }) {
        const { field, direction } = sort;
        const multiplier = direction === 'asc' ? 1 : -1;

        return tasks.sort((a, b) => {
            let aVal = a[field];
            let bVal = b[field];

            // Handle dates
            if (field === 'created_at' || field === 'updated_at' || field === 'due_date') {
                aVal = aVal ? new Date(aVal).getTime() : 0;
                bVal = bVal ? new Date(bVal).getTime() : 0;
            }

            // Handle nulls
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;

            if (aVal < bVal) return -1 * multiplier;
            if (aVal > bVal) return 1 * multiplier;
            return 0;
        });
    }

    /**
     * Render tasks to DOM
     * @param {Array} tasks
     * @param {Object} options - { fromCache: boolean }
     * @returns {Promise<void>}
     */
    async renderTasks(tasks, options = {}) {
        const container = document.getElementById('tasks-list-container');
        const emptyState = document.getElementById('tasks-empty-state');
        
        if (!container) {
            console.warn('⚠️ Tasks container not found, skipping render');
            return;
        }

        // Show empty state or task list
        if (tasks.length === 0) {
            if (emptyState) {
                emptyState.style.display = 'block';
                emptyState.classList.add('fade-in');
            }
            if (container) {
                container.innerHTML = '';
            }
            return;
        }

        // Hide empty state
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        // Render tasks
        const tasksHTML = tasks.map((task, index) => this.renderTaskCard(task, index)).join('');
        container.innerHTML = tasksHTML;

        // Add stagger animation
        const cards = container.querySelectorAll('.task-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.05}s`;
        });

        // Update counters
        this.updateCounters(tasks);

        // Show cache indicator if from cache
        if (options.fromCache) {
            this.showCacheIndicator();
        }

        // Restore scroll position
        const viewState = await this.cache.getViewState('tasks_page');
        if (viewState && viewState.scroll_position) {
            window.scrollTo(0, viewState.scroll_position);
        }
    }

    /**
     * Render single task card HTML
     * @param {Object} task
     * @param {number} index
     * @returns {string} HTML
     */
    renderTaskCard(task, index) {
        const priority = task.priority || 'medium';
        const status = task.status || 'todo';
        const isCompleted = status === 'completed';
        const isSnoozed = task.snoozed_until && new Date(task.snoozed_until) > new Date();

        return `
            <div class="task-card" 
                 data-task-id="${task.id}"
                 data-status="${status}"
                 data-priority="${priority}"
                 style="animation-delay: ${index * 0.05}s;">
                <div class="task-card-header">
                    <div class="task-checkbox-wrapper">
                        <input type="checkbox" 
                               class="task-checkbox" 
                               ${isCompleted ? 'checked' : ''}
                               data-task-id="${task.id}">
                    </div>
                    <div class="task-content">
                        <h3 class="task-title ${isCompleted ? 'completed' : ''}">
                            ${this.escapeHtml(task.title || 'Untitled Task')}
                        </h3>
                        ${task.description ? `
                            <p class="task-description">${this.escapeHtml(task.description)}</p>
                        ` : ''}
                        <div class="task-meta">
                            <span class="priority-badge priority-${priority.toLowerCase()}">
                                ${priority}
                            </span>
                            ${task.due_date ? `
                                <span class="due-date-badge ${this.isDueDateOverdue(task.due_date) ? 'overdue' : ''}">
                                    <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                    </svg>
                                    ${this.formatDueDate(task.due_date)}
                                </span>
                            ` : ''}
                            ${isSnoozed ? `
                                <span class="snoozed-badge">
                                    <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                    </svg>
                                    Snoozed
                                </span>
                            ` : ''}
                            ${task.labels && task.labels.length > 0 ? `
                                <div class="task-labels">
                                    ${task.labels.slice(0, 3).map(label => `
                                        <span class="label-badge">${this.escapeHtml(label)}</span>
                                    `).join('')}
                                    ${task.labels.length > 3 ? `
                                        <span class="label-badge">+${task.labels.length - 3}</span>
                                    ` : ''}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Update task counters in UI
     * CRITICAL: This must ALWAYS calculate counts from ALL tasks, not filtered subset
     * @param {Array} tasks - Currently displayed tasks (may be filtered)
     */
    async updateCounters(tasks) {
        // Fetch ALL tasks from cache to get correct totals
        // The 'tasks' parameter might be filtered, which would give wrong counts
        const allTasks = await this.cache.getAllTasks();
        
        const counters = {
            all: allTasks.length,
            pending: allTasks.filter(t => t.status === 'todo' || t.status === 'in_progress').length,
            todo: allTasks.filter(t => t.status === 'todo').length,
            in_progress: allTasks.filter(t => t.status === 'in_progress').length,
            completed: allTasks.filter(t => t.status === 'completed').length,
            overdue: allTasks.filter(t => this.isDueDateOverdue(t.due_date) && t.status !== 'completed').length
        };

        // Update counter badges
        Object.entries(counters).forEach(([key, count]) => {
            const badge = document.querySelector(`[data-counter="${key}"]`);
            if (badge) {
                badge.textContent = count;
                
                // Add pulse animation on counter change
                badge.classList.remove('counter-pulse');
                void badge.offsetWidth; // Trigger reflow
                badge.classList.add('counter-pulse');
            }
        });
    }

    /**
     * Show cache indicator (subtle notification)
     */
    showCacheIndicator() {
        const indicator = document.getElementById('cache-indicator');
        if (indicator) {
            indicator.style.display = 'block';
            indicator.classList.add('fade-in');
            
            setTimeout(() => {
                indicator.classList.remove('fade-in');
                indicator.classList.add('fade-out');
                setTimeout(() => {
                    indicator.style.display = 'none';
                }, 300);
            }, 2000);
        }
    }

    /**
     * Sync with server in background
     * @returns {Promise<void>}
     */
    async syncInBackground() {
        if (this.syncInProgress) {
            console.log('⏳ Sync already in progress, skipping');
            return;
        }

        this.syncInProgress = true;
        this.perf.sync_start = performance.now();
        console.log('🔄 Starting background sync...');

        try {
            // Fetch tasks from server
            const response = await fetch('/api/tasks/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const data = await response.json();
            const serverTasks = data.tasks || [];

            this.perf.sync_end = performance.now();
            const syncTime = this.perf.sync_end - this.perf.sync_start;
            console.log(`✅ Background sync completed in ${syncTime.toFixed(2)}ms (${serverTasks.length} tasks)`);

            // Update cache with server data
            await this.cache.saveTasks(serverTasks);
            
            // Update last sync timestamp
            this.lastSyncTimestamp = Date.now();
            await this.cache.setMetadata('last_sync_timestamp', this.lastSyncTimestamp);

            // Re-render with fresh data
            await this.renderTasks(serverTasks, { fromCache: false });

            // Emit sync success event
            window.dispatchEvent(new CustomEvent('tasks:sync:success', {
                detail: { tasks: serverTasks, sync_time_ms: syncTime }
            }));

            // Schedule compaction if needed
            await this.maybeCompact();

        } catch (error) {
            console.error('❌ Background sync failed:', error);
            this.syncInProgress = false;

            // Emit sync error event
            window.dispatchEvent(new CustomEvent('tasks:sync:error', {
                detail: { error: error.message }
            }));
        } finally {
            this.syncInProgress = false;
        }
    }

    /**
     * Maybe run compaction if enough time has passed
     * @returns {Promise<void>}
     */
    async maybeCompact() {
        const lastCompaction = await this.cache.getMetadata('last_compaction_timestamp');
        const now = Date.now();
        const oneDayMs = 24 * 60 * 60 * 1000;

        // Compact once per day
        if (!lastCompaction || (now - lastCompaction) > oneDayMs) {
            console.log('🗜️ Running event compaction...');
            const result = await this.cache.compactEvents(30); // 30 day retention
            await this.cache.setMetadata('last_compaction_timestamp', now);
            console.log(`✅ Compacted ${result.compacted} events`);
        }
    }

    /**
     * Fallback to server-only loading
     * @returns {Promise<Object>}
     */
    async fallbackToServer() {
        console.log('⚠️ Falling back to server-only loading...');
        
        try {
            const response = await fetch('/api/tasks/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            const data = await response.json();
            const tasks = data.tasks || [];

            await this.renderTasks(tasks, { fromCache: false });

            return {
                success: true,
                cached_tasks: 0,
                fallback: true,
                tasks: tasks.length
            };
        } catch (error) {
            console.error('❌ Fallback failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Check if due date is overdue
     * @param {string} dueDate
     * @returns {boolean}
     */
    isDueDateOverdue(dueDate) {
        if (!dueDate) return false;
        const due = new Date(dueDate);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return due < today;
    }

    /**
     * Format due date for display
     * @param {string} dueDate
     * @returns {string}
     */
    formatDueDate(dueDate) {
        if (!dueDate) return 'No due date';
        
        const due = new Date(dueDate);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const diffDays = Math.floor((due - today) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Tomorrow';
        if (diffDays === -1) return 'Yesterday';
        if (diffDays < 0) return `${Math.abs(diffDays)}d overdue`;
        if (diffDays <= 7) return `In ${diffDays}d`;
        
        return due.toLocaleDateString();
    }

    /**
     * Escape HTML for XSS prevention
     * @param {string} text
     * @returns {string}
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export singleton
window.taskBootstrap = new TaskBootstrap();

console.log('🚀 CROWN⁴.5 TaskBootstrap loaded');
