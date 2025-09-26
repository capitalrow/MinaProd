/**
 * Dashboard JavaScript
 * Handles dynamic data loading and real-time updates for the Mina dashboard
 */

class MinaDashboard {
    constructor() {
        this.apiBase = '/api';
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimers = new Map();
        this.init();
    }

    init() {
        console.log('[Dashboard] Initializing Mina Dashboard');
        this.loadDashboardData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    /**
     * Load all dashboard data
     */
    async loadDashboardData() {
        try {
            await Promise.all([
                this.loadStats(),
                this.loadRecentMeetings(),
                this.loadMyTasks(),
                this.loadAnalyticsOverview()
            ]);
        } catch (error) {
            console.error('[Dashboard] Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    /**
     * Load dashboard statistics
     */
    async loadStats() {
        try {
            const [meetingsResponse, tasksResponse] = await Promise.all([
                fetch(`${this.apiBase}/meetings/stats`),
                fetch(`${this.apiBase}/tasks/stats`)
            ]);

            const meetingsStats = await meetingsResponse.json();
            const tasksStats = await tasksResponse.json();

            if (meetingsStats.success) {
                this.updateStatsCards(meetingsStats.stats, tasksStats.stats);
            }
        } catch (error) {
            console.error('[Dashboard] Failed to load stats:', error);
        }
    }

    /**
     * Update statistics cards
     */
    updateStatsCards(meetingStats, taskStats) {
        // Update meeting stats
        this.updateStatCard('total-meetings', meetingStats.total_meetings || 0);
        this.updateStatCard('this-week-meetings', meetingStats.this_week_meetings || 0);
        
        // Update task stats
        this.updateStatCard('total-tasks', taskStats?.total_tasks || 0);
        this.updateStatCard('task-completion-rate', `${taskStats?.completion_rate || 0}%`);
        
        // Update active meetings
        this.updateStatCard('active-meetings', meetingStats.live_meetings || 0);
        
        // Update my active tasks
        this.updateStatCard('my-active-tasks', taskStats?.my_active_tasks || 0);
    }

    /**
     * Update individual stat card
     */
    updateStatCard(cardId, value) {
        const card = document.querySelector(`[data-stat="${cardId}"]`);
        if (card) {
            const valueElement = card.querySelector('.stat-value');
            if (valueElement) {
                valueElement.textContent = value;
            }
        }
    }

    /**
     * Load recent meetings
     */
    async loadRecentMeetings() {
        try {
            const response = await fetch(`${this.apiBase}/meetings/recent?limit=5`);
            const data = await response.json();

            if (data.success) {
                this.renderRecentMeetings(data.meetings);
            }
        } catch (error) {
            console.error('[Dashboard] Failed to load recent meetings:', error);
        }
    }

    /**
     * Render recent meetings list
     */
    renderRecentMeetings(meetings) {
        const container = document.getElementById('recent-meetings-list');
        if (!container) return;

        if (meetings.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p class="text-gray-500">No meetings yet.</p>
                    <a href="/live" class="btn btn-primary btn-sm">Start your first meeting</a>
                </div>
            `;
            return;
        }

        container.innerHTML = meetings.map(meeting => `
            <div class="meeting-item" data-meeting-id="${meeting.id}">
                <div class="meeting-info">
                    <div class="meeting-title">${this.escapeHtml(meeting.title)}</div>
                    <div class="meeting-date">${this.formatDate(meeting.created_at)}</div>
                </div>
                <div class="meeting-actions">
                    <span class="meeting-status status-${meeting.status}">
                        ${this.capitalizeFirst(meeting.status)}
                    </span>
                    <button class="btn-icon" onclick="dashboard.viewMeeting(${meeting.id})" title="View Details">
                        <i data-feather="eye"></i>
                    </button>
                </div>
            </div>
        `).join('');

        // Re-initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Load user's tasks
     */
    async loadMyTasks() {
        try {
            const response = await fetch(`${this.apiBase}/tasks/my-tasks`);
            const data = await response.json();

            if (data.success) {
                this.renderMyTasks(data.tasks);
            }
        } catch (error) {
            console.error('[Dashboard] Failed to load my tasks:', error);
        }
    }

    /**
     * Render user's tasks
     */
    renderMyTasks(taskGroups) {
        const container = document.getElementById('my-tasks-list');
        if (!container) return;

        const allTasks = [
            ...taskGroups.todo,
            ...taskGroups.in_progress,
            ...taskGroups.completed.slice(0, 3) // Show only 3 completed tasks
        ];

        if (allTasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p class="text-gray-500">No tasks assigned.</p>
                    <p class="text-gray-400 text-sm">Tasks will appear here when created from meetings.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = allTasks.map(task => `
            <div class="task-item" data-task-id="${task.id}">
                <div class="task-content">
                    <div class="task-title">${this.escapeHtml(task.title)}</div>
                    <div class="task-meta">
                        <span class="task-status status-${task.status}">
                            ${this.capitalizeFirst(task.status)}
                        </span>
                        <span class="task-priority priority-${task.priority}">
                            ${this.capitalizeFirst(task.priority)} priority
                        </span>
                        ${task.due_date ? `<span class="task-due">Due ${this.formatDate(task.due_date)}</span>` : ''}
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn-icon" onclick="dashboard.updateTaskStatus(${task.id}, '${this.getNextStatus(task.status)}')" title="Update Status">
                        <i data-feather="${this.getStatusIcon(task.status)}"></i>
                    </button>
                </div>
            </div>
        `).join('');

        // Re-initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Load analytics overview
     */
    async loadAnalyticsOverview() {
        try {
            const response = await fetch(`${this.apiBase}/analytics/dashboard?days=7`);
            const data = await response.json();

            if (data.success) {
                this.renderAnalyticsOverview(data.dashboard);
            }
        } catch (error) {
            console.error('[Dashboard] Failed to load analytics:', error);
        }
    }

    /**
     * Render analytics overview
     */
    renderAnalyticsOverview(dashboard) {
        // Update effectiveness score
        this.updateAnalyticsWidget('effectiveness-score', dashboard.averages.effectiveness, '%');
        
        // Update engagement score
        this.updateAnalyticsWidget('engagement-score', dashboard.averages.engagement, '%');
        
        // Update sentiment score
        this.updateAnalyticsWidget('sentiment-score', dashboard.averages.sentiment, '%');
        
        // Update productivity metrics
        this.updateAnalyticsWidget('total-tasks-created', dashboard.productivity.total_tasks_created);
        this.updateAnalyticsWidget('total-decisions-made', dashboard.productivity.total_decisions_made);
    }

    /**
     * Update analytics widget
     */
    updateAnalyticsWidget(widgetId, value, suffix = '') {
        const widget = document.querySelector(`[data-analytics="${widgetId}"]`);
        if (widget) {
            const valueElement = widget.querySelector('.analytics-value');
            if (valueElement) {
                valueElement.textContent = `${value}${suffix}`;
            }
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Refresh button
        const refreshButton = document.getElementById('refresh-dashboard');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.loadDashboardData();
                this.showNotification('Dashboard refreshed', 'success');
            });
        }

        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        this.stopAutoRefresh(); // Clear existing timers
        
        const timer = setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
        
        this.refreshTimers.set('dashboard', timer);
        console.log('[Dashboard] Auto-refresh started');
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        this.refreshTimers.forEach((timer, key) => {
            clearInterval(timer);
        });
        this.refreshTimers.clear();
        console.log('[Dashboard] Auto-refresh stopped');
    }

    /**
     * View meeting details
     */
    async viewMeeting(meetingId) {
        try {
            const response = await fetch(`${this.apiBase}/meetings/${meetingId}`);
            const data = await response.json();

            if (data.success) {
                this.showMeetingModal(data.meeting);
            } else {
                this.showError('Failed to load meeting details');
            }
        } catch (error) {
            console.error('[Dashboard] Failed to load meeting details:', error);
            this.showError('Failed to load meeting details');
        }
    }

    /**
     * Update task status
     */
    async updateTaskStatus(taskId, newStatus) {
        try {
            const response = await fetch(`${this.apiBase}/tasks/${taskId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: newStatus })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('Task status updated', 'success');
                this.loadMyTasks(); // Refresh tasks
                this.loadStats(); // Refresh stats
            } else {
                this.showError(data.message || 'Failed to update task');
            }
        } catch (error) {
            console.error('[Dashboard] Failed to update task:', error);
            this.showError('Failed to update task');
        }
    }

    /**
     * Utility functions
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
        });
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    getNextStatus(currentStatus) {
        const statusFlow = {
            'todo': 'in_progress',
            'in_progress': 'completed',
            'completed': 'todo'
        };
        return statusFlow[currentStatus] || 'todo';
    }

    getStatusIcon(status) {
        const icons = {
            'todo': 'play',
            'in_progress': 'check',
            'completed': 'rotate-ccw',
            'cancelled': 'x'
        };
        return icons[status] || 'circle';
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Add to page
        const container = document.getElementById('notifications') || document.body;
        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Show meeting modal
     */
    showMeetingModal(meeting) {
        // Create modal HTML
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${this.escapeHtml(meeting.title)}</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="meeting-details">
                        <p><strong>Status:</strong> ${this.capitalizeFirst(meeting.status)}</p>
                        <p><strong>Created:</strong> ${this.formatDate(meeting.created_at)}</p>
                        ${meeting.description ? `<p><strong>Description:</strong> ${this.escapeHtml(meeting.description)}</p>` : ''}
                        ${meeting.participants ? `<p><strong>Participants:</strong> ${meeting.participants.length}</p>` : ''}
                        ${meeting.tasks ? `<p><strong>Tasks Created:</strong> ${meeting.tasks.length}</p>` : ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Close</button>
                    <a href="/dashboard/meetings/${meeting.id}" class="btn btn-primary">View Full Details</a>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new MinaDashboard();
});

// CSS for notifications and modals
const dashboardStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 16px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
        max-width: 300px;
    }

    .notification-success {
        background: #10b981;
        color: white;
    }

    .notification-error {
        background: #ef4444;
        color: white;
    }

    .notification-info {
        background: #3b82f6;
        color: white;
    }

    .notification-close {
        background: none;
        border: none;
        color: inherit;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
    }

    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal-content {
        background: white;
        border-radius: 8px;
        width: 90%;
        max-width: 600px;
        max-height: 90vh;
        overflow: auto;
    }

    .modal-header {
        padding: 20px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .modal-body {
        padding: 20px;
    }

    .modal-footer {
        padding: 20px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        gap: 10px;
        justify-content: flex-end;
    }

    .modal-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        width: 30px;
        height: 30px;
    }

    .empty-state {
        text-align: center;
        padding: 40px 20px;
    }

    .btn-icon {
        background: none;
        border: none;
        padding: 4px;
        cursor: pointer;
        color: #6b7280;
        border-radius: 4px;
    }

    .btn-icon:hover {
        background: #f3f4f6;
        color: #374151;
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = dashboardStyles;
document.head.appendChild(styleSheet);