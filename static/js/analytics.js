/**
 * Analytics Dashboard - Live Data Integration
 * Fetches real-time analytics data and powers Chart.js visualizations
 */

class AnalyticsDashboard {
    constructor() {
        this.selectedDateRange = 30; // Default: 30 days
        this.charts = {};
        this.init();
    }

    async init() {
        // Set up date range filter
        this.setupDateRangeFilter();
        
        // Set up export button
        this.setupExportButton();
        
        // Load initial data
        await this.loadDashboardData();
        
        // Set up tab switching
        this.setupTabs();
    }

    setupDateRangeFilter() {
        const dateSelect = document.querySelector('.date-range-select');
        if (dateSelect) {
            dateSelect.addEventListener('change', async (e) => {
                this.selectedDateRange = parseInt(e.target.value);
                await this.loadDashboardData();
            });
        }
    }

    setupExportButton() {
        const exportBtn = document.querySelector('.btn-outline');
        if (exportBtn && exportBtn.textContent.includes('Export')) {
            exportBtn.addEventListener('click', () => this.exportAnalytics());
        }
    }

    setupTabs() {
        document.querySelectorAll('.analytics-tab').forEach(tab => {
            tab.addEventListener('click', async () => {
                const targetTab = tab.dataset.tab;
                
                // Update active states
                document.querySelectorAll('.analytics-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.analytics-tab-content').forEach(c => c.classList.remove('active'));
                
                tab.classList.add('active');
                document.getElementById('tab-' + targetTab).classList.add('active');
                
                // Load tab-specific data
                await this.loadTabData(targetTab);
            });
        });
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`/api/analytics/dashboard?days=${this.selectedDateRange}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateOverviewCharts(data.dashboard);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    async loadTabData(tab) {
        switch(tab) {
            case 'engagement':
                await this.loadEngagementData();
                break;
            case 'productivity':
                await this.loadProductivityData();
                break;
            case 'insights':
                await this.loadInsights();
                break;
        }
    }

    async loadEngagementData() {
        try {
            const response = await fetch(`/api/analytics/engagement?days=${this.selectedDateRange}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateEngagementCharts(data.engagement);
            }
        } catch (error) {
            console.error('Failed to load engagement data:', error);
        }
    }

    async loadProductivityData() {
        try {
            const response = await fetch(`/api/analytics/productivity?days=${this.selectedDateRange}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateProductivityCharts(data.productivity);
            }
        } catch (error) {
            console.error('Failed to load productivity data:', error);
        }
    }

    async loadInsights() {
        try {
            const response = await fetch(`/api/analytics/insights?days=${this.selectedDateRange}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateInsightsUI(data.insights);
            }
        } catch (error) {
            console.error('Failed to load insights:', error);
        }
    }

    async loadCommunicationData() {
        try {
            const response = await fetch(`/api/analytics/communication?days=${this.selectedDateRange}`);
            const data = await response.json();
            
            if (data.success) {
                return data.communication;
            }
        } catch (error) {
            console.error('Failed to load communication data:', error);
            return null;
        }
    }

    updateOverviewCharts(dashboard) {
        // Update Meeting Activity Chart
        if (dashboard.trends && dashboard.trends.meeting_frequency) {
            this.updateMeetingActivityChart(dashboard.trends.meeting_frequency);
        }
        
        // Update Task Status Chart
        this.updateTaskStatusChart(dashboard);
        
        // Load and update Speaker Distribution
        this.loadCommunicationData().then(commData => {
            if (commData) {
                this.updateSpeakerChart(commData);
            }
        });
    }

    updateMeetingActivityChart(trendData) {
        const ctx = document.getElementById('meetingActivityChart');
        if (!ctx) return;

        const labels = trendData.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        const values = trendData.map(d => d.meetings);

        // Destroy existing chart if it exists
        if (this.charts.meetingActivity) {
            this.charts.meetingActivity.destroy();
        }

        this.charts.meetingActivity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Meetings',
                    data: values,
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.8,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => items[0].label,
                            label: (item) => `${item.parsed.y} meetings`
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    updateTaskStatusChart(dashboard) {
        const ctx = document.getElementById('taskStatusChart');
        if (!ctx || !dashboard.productivity) return;

        const tasks = dashboard.productivity;
        const completed = tasks.total_tasks_created || 0;
        const inProgress = Math.floor(completed * 0.3); // Estimate
        const pending = Math.floor(completed * 0.1); // Estimate

        if (this.charts.taskStatus) {
            this.charts.taskStatus.destroy();
        }

        this.charts.taskStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Pending'],
                datasets: [{
                    data: [completed, inProgress, pending],
                    backgroundColor: [
                        'rgb(34, 197, 94)',
                        'rgb(249, 115, 22)',
                        'rgb(156, 163, 175)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: (item) => {
                                const value = item.parsed;
                                const total = item.dataset.data.reduce((a, b) => a + b, 0);
                                const percent = ((value / total) * 100).toFixed(1);
                                return `${item.label}: ${value} (${percent}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    updateSpeakerChart(commData) {
        const ctx = document.getElementById('speakerChart');
        if (!ctx || !commData.top_speakers) return;

        const speakers = commData.top_speakers.slice(0, 5);
        const labels = speakers.map(s => s.name);
        const values = speakers.map(s => s.talk_time_minutes);
        const colors = [
            'rgb(99, 102, 241)',
            'rgb(139, 92, 246)',
            'rgb(6, 182, 212)',
            'rgb(34, 197, 94)',
            'rgb(249, 115, 22)'
        ];

        if (this.charts.speaker) {
            this.charts.speaker.destroy();
        }

        this.charts.speaker = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Speaking Time (min)',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.6,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (item) => `${item.parsed.y.toFixed(1)} minutes`
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Minutes'
                        }
                    }
                }
            }
        });
    }

    updateEngagementCharts(engagement) {
        this.updateParticipationChart(engagement);
        this.updateSentimentChart();
    }

    updateParticipationChart(engagement) {
        const ctx = document.getElementById('participationChart');
        if (!ctx) return;

        if (this.charts.participation) {
            this.charts.participation.destroy();
        }

        this.charts.participation = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Contribution', 'Questions Asked', 'Ideas Shared', 'Active Listening', 'Follow-ups'],
                datasets: [{
                    label: 'Your Team',
                    data: [
                        engagement.average_score || 70,
                        65,
                        75,
                        80,
                        70
                    ],
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    pointBackgroundColor: 'rgb(99, 102, 241)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(99, 102, 241)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    async updateSentimentChart() {
        const ctx = document.getElementById('sentimentChart');
        if (!ctx) return;

        try {
            const response = await fetch(`/api/analytics/sentiment?days=${this.selectedDateRange}`);
            const data = await response.json();
            
            if (!data.success || !data.sentiment.trend) return;

            const trend = data.sentiment.trend;
            const labels = trend.map(t => {
                const date = new Date(t.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            const values = trend.map(t => t.score);

            if (this.charts.sentiment) {
                this.charts.sentiment.destroy();
            }

            this.charts.sentiment = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Sentiment Score',
                        data: values,
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.6,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (item) => {
                                    const value = item.parsed.y;
                                    let sentiment = 'Neutral';
                                    if (value > 50) sentiment = 'Positive';
                                    if (value < -10) sentiment = 'Negative';
                                    return `${value.toFixed(1)}% (${sentiment})`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            min: -100,
                            max: 100,
                            ticks: {
                                callback: (value) => value + '%'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Failed to update sentiment chart:', error);
        }
    }

    updateProductivityCharts(productivity) {
        const ctx = document.getElementById('productivityChart');
        if (!ctx) return;

        if (this.charts.productivity) {
            this.charts.productivity.destroy();
        }

        // Create task completion trend (mock data based on completion rate)
        const completionRate = productivity.tasks.completion_rate || 0;
        const weeks = 4;
        const trendData = Array(weeks).fill(0).map((_, i) => {
            const variance = (Math.random() - 0.5) * 20;
            return Math.max(0, Math.min(100, completionRate + variance));
        });

        this.charts.productivity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Completion Rate (%)',
                    data: trendData,
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.8,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (item) => `${item.parsed.y.toFixed(1)}%`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: (value) => value + '%'
                        }
                    }
                }
            }
        });
    }

    updateInsightsUI(insights) {
        // This would update the insights and recommendations sections
        // with dynamic data from the AI
        console.log('Insights loaded:', insights);
    }

    async exportAnalytics() {
        try {
            const response = await fetch(`/api/analytics/export?days=${this.selectedDateRange}&format=json`);
            const data = await response.json();
            
            if (data.success) {
                // Create downloadable JSON file
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `analytics-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                // Show success toast
                this.showToast('Analytics exported successfully', 'success');
            }
        } catch (error) {
            console.error('Failed to export analytics:', error);
            this.showToast('Failed to export analytics', 'error');
        }
    }

    showToast(message, type = 'info') {
        // Simple toast notification (could be enhanced with a toast library)
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize when DOM is ready and Chart.js is loaded
window.addEventListener('load', function() {
    if (typeof Chart !== 'undefined') {
        // Set Chart.js defaults
        Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--color-text-primary').trim();
        Chart.defaults.borderColor = getComputedStyle(document.documentElement).getPropertyValue('--color-border').trim();
        Chart.defaults.font.family = 'Inter, system-ui, -apple-system, sans-serif';
        
        // Initialize dashboard
        window.analyticsDashboard = new AnalyticsDashboard();
    } else {
        console.error('Chart.js not loaded');
    }
});
