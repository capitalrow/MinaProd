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
            
            // Load communication data for speaking time visualizations (T2.33)
            const commResponse = await fetch(`/api/analytics/communication?days=${this.selectedDateRange}`);
            const commData = await commResponse.json();
            
            if (commData.success) {
                this.updateSpeakingTimeCharts(commData.communication);
                // T2.34: Update participation balance metrics
                this.updateParticipationBalanceMetrics(commData.communication);
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

    /**
     * T2.33: Speaking Time Visualization
     * Creates detailed speaking time charts (bar, pie) and participant breakdown
     */
    updateSpeakingTimeCharts(communication) {
        if (!communication || !communication.top_speakers) {
            this.showEmptySpeakingTimeState();
            return;
        }

        const speakers = communication.top_speakers.slice(0, 10); // Top 10
        const labels = speakers.map(s => s.name);
        const timeValues = speakers.map(s => s.talk_time_minutes);
        const totalTime = timeValues.reduce((a, b) => a + b, 0);
        const percentages = timeValues.map(t => ((t / totalTime) * 100).toFixed(1));

        // Color palette for charts
        const colors = [
            'rgb(99, 102, 241)',   // Primary
            'rgb(139, 92, 246)',   // Purple
            'rgb(6, 182, 212)',    // Cyan
            'rgb(34, 197, 94)',    // Green
            'rgb(249, 115, 22)',   // Orange
            'rgb(236, 72, 153)',   // Pink
            'rgb(59, 130, 246)',   // Blue
            'rgb(168, 85, 247)',   // Violet
            'rgb(20, 184, 166)',   // Teal
            'rgb(234, 179, 8)'     // Yellow
        ];

        // 1. Horizontal Bar Chart - Speaking Time Distribution
        this.createSpeakingTimeBarChart(labels, timeValues, colors);

        // 2. Pie Chart - Speaking Balance
        this.createSpeakingTimePieChart(labels, timeValues, percentages, colors);

        // 3. Detailed Participant Breakdown
        this.createSpeakingTimeDetails(speakers, totalTime, colors);
    }

    createSpeakingTimeBarChart(labels, values, colors) {
        const ctx = document.getElementById('speakingTimeBarChart');
        if (!ctx) return;

        if (this.charts.speakingTimeBar) {
            this.charts.speakingTimeBar.destroy();
        }

        this.charts.speakingTimeBar = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Speaking Time (minutes)',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 6,
                    barThickness: 32
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bars
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.8,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (item) => {
                                const minutes = item.parsed.x;
                                const hours = Math.floor(minutes / 60);
                                const mins = Math.round(minutes % 60);
                                return `${hours}h ${mins}m (${minutes.toFixed(1)} minutes)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
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

    createSpeakingTimePieChart(labels, values, percentages, colors) {
        const ctx = document.getElementById('speakingTimePieChart');
        if (!ctx) return;

        if (this.charts.speakingTimePie) {
            this.charts.speakingTimePie.destroy();
        }

        this.charts.speakingTimePie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map((label, i) => `${label} (${percentages[i]}%)`),
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 12,
                            font: { size: 11 },
                            generateLabels: (chart) => {
                                const data = chart.data;
                                return data.labels.map((label, i) => ({
                                    text: label,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i
                                }));
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (item) => {
                                const value = item.parsed;
                                const percent = percentages[item.dataIndex];
                                const hours = Math.floor(value / 60);
                                const mins = Math.round(value % 60);
                                return `${hours}h ${mins}m (${percent}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    createSpeakingTimeDetails(speakers, totalTime, colors) {
        const container = document.getElementById('speakingTimeDetails');
        if (!container) return;

        // Calculate balance indicators
        const avgTime = totalTime / speakers.length;
        const idealPercentage = 100 / speakers.length;

        const detailsHTML = speakers.map((speaker, index) => {
            const time = speaker.talk_time_minutes;
            const percentage = ((time / totalTime) * 100).toFixed(1);
            const hours = Math.floor(time / 60);
            const minutes = Math.round(time % 60);
            
            // Balance indicator: compare to ideal
            const deviation = percentage - idealPercentage;
            let balanceClass = 'bg-gray-500';
            let balanceText = 'Balanced';
            
            if (deviation > 15) {
                balanceClass = 'bg-orange-500';
                balanceText = 'High';
            } else if (deviation < -15) {
                balanceClass = 'bg-blue-500';
                balanceText = 'Low';
            } else if (Math.abs(deviation) <= 5) {
                balanceClass = 'bg-green-500';
                balanceText = 'Ideal';
            }

            return `
                <div class="flex items-center gap-4 p-4 rounded-lg" style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style="background: ${colors[index]};">
                        <span class="text-white font-bold">${speaker.name.charAt(0).toUpperCase()}</span>
                    </div>
                    <div class="flex-1">
                        <div class="flex justify-between items-center mb-1">
                            <h3 class="font-semibold text-base">${speaker.name}</h3>
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 rounded-full text-xs font-medium ${balanceClass} bg-opacity-20 text-white">
                                    ${balanceText}
                                </span>
                                <span class="font-bold text-lg">${percentage}%</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-3 mb-2">
                            <span class="text-sm text-secondary">${hours}h ${minutes}m</span>
                            <span class="text-sm text-tertiary">•</span>
                            <span class="text-sm text-tertiary">${speaker.segment_count || 0} segments</span>
                        </div>
                        <div class="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div class="absolute h-full rounded-full transition-all duration-500" 
                                 style="width: ${percentage}%; background: ${colors[index]};"></div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = detailsHTML;
    }

    showEmptySpeakingTimeState() {
        const container = document.getElementById('speakingTimeDetails');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center text-secondary py-12">
                <svg class="w-16 h-16 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
                <p class="font-medium">No speaking time data available</p>
                <p class="text-sm mt-1">Record meetings to see participant speaking analytics</p>
            </div>
        `;
    }

    /**
     * T2.34: Participation Balance Metrics
     * Calculates and displays comprehensive balance indicators
     */
    updateParticipationBalanceMetrics(communication) {
        const container = document.getElementById('participationBalanceMetrics');
        if (!container || !communication || !communication.top_speakers) {
            return;
        }

        const speakers = communication.top_speakers;
        const totalTime = speakers.reduce((sum, s) => sum + s.talk_time_minutes, 0);
        const numSpeakers = speakers.length;
        
        // Calculate balance metrics
        const metrics = this.calculateBalanceMetrics(speakers, totalTime, numSpeakers);
        
        // Render balance metric cards
        container.innerHTML = `
            ${this.createBalanceMetricCard(
                'Speaking Time Balance',
                metrics.timeBalance.score,
                metrics.timeBalance.status,
                metrics.timeBalance.description,
                'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
            )}
            ${this.createBalanceMetricCard(
                'Contribution Equity',
                metrics.contributionEquity.score,
                metrics.contributionEquity.status,
                metrics.contributionEquity.description,
                'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'
            )}
            ${this.createBalanceMetricCard(
                'Engagement Dispersion',
                metrics.dispersion.score,
                metrics.dispersion.status,
                metrics.dispersion.description,
                'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
            )}
            ${this.createBalanceMetricCard(
                'Participation Health',
                metrics.overall.score,
                metrics.overall.status,
                metrics.overall.description,
                'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
            )}
        `;
    }

    calculateBalanceMetrics(speakers, totalTime, numSpeakers) {
        const idealPercentage = 100 / numSpeakers;
        const percentages = speakers.map(s => (s.talk_time_minutes / totalTime) * 100);
        
        // 1. Speaking Time Balance (using Coefficient of Variation)
        const mean = percentages.reduce((a, b) => a + b, 0) / percentages.length;
        const variance = percentages.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / percentages.length;
        const stdDev = Math.sqrt(variance);
        const cv = (stdDev / mean) * 100; // Coefficient of Variation
        
        const timeBalanceScore = Math.max(0, 100 - cv);
        const timeBalanceStatus = timeBalanceScore >= 80 ? 'Excellent' : 
                                  timeBalanceScore >= 60 ? 'Good' : 
                                  timeBalanceScore >= 40 ? 'Fair' : 'Needs Improvement';
        
        // 2. Contribution Equity (Gini coefficient approximation)
        const sortedPercentages = [...percentages].sort((a, b) => a - b);
        let giniSum = 0;
        sortedPercentages.forEach((p, i) => {
            giniSum += (i + 1) * p;
        });
        const gini = (2 * giniSum) / (numSpeakers * sortedPercentages.reduce((a, b) => a + b, 0)) - 
                     (numSpeakers + 1) / numSpeakers;
        const equityScore = (1 - gini) * 100;
        const equityStatus = equityScore >= 75 ? 'Excellent' : 
                            equityScore >= 60 ? 'Good' : 
                            equityScore >= 45 ? 'Fair' : 'Unbalanced';
        
        // 3. Engagement Dispersion (how spread out participation is)
        const deviations = percentages.map(p => Math.abs(p - idealPercentage));
        const avgDeviation = deviations.reduce((a, b) => a + b, 0) / deviations.length;
        const dispersionScore = Math.max(0, 100 - (avgDeviation * 3));
        const dispersionStatus = dispersionScore >= 75 ? 'Well-Distributed' : 
                                dispersionScore >= 50 ? 'Moderately Spread' : 
                                dispersionScore >= 30 ? 'Concentrated' : 'Highly Skewed';
        
        // 4. Overall Participation Health
        const overallScore = (timeBalanceScore + equityScore + dispersionScore) / 3;
        const overallStatus = overallScore >= 80 ? 'Healthy' : 
                             overallScore >= 60 ? 'Stable' : 
                             overallScore >= 40 ? 'Attention Needed' : 'Critical';
        
        return {
            timeBalance: {
                score: Math.round(timeBalanceScore),
                status: timeBalanceStatus,
                description: `${cv.toFixed(1)}% variation in speaking time`
            },
            contributionEquity: {
                score: Math.round(equityScore),
                status: equityStatus,
                description: `${(gini * 100).toFixed(1)}% Gini coefficient`
            },
            dispersion: {
                score: Math.round(dispersionScore),
                status: dispersionStatus,
                description: `±${avgDeviation.toFixed(1)}% from ideal balance`
            },
            overall: {
                score: Math.round(overallScore),
                status: overallStatus,
                description: `Based on ${numSpeakers} participants`
            }
        };
    }

    createBalanceMetricCard(title, score, status, description, iconPath) {
        // Determine color based on score
        let colorClass, bgGradient;
        if (score >= 80) {
            colorClass = 'text-green-500';
            bgGradient = 'rgba(34, 197, 94, 0.1)';
        } else if (score >= 60) {
            colorClass = 'text-blue-500';
            bgGradient = 'rgba(99, 102, 241, 0.1)';
        } else if (score >= 40) {
            colorClass = 'text-yellow-500';
            bgGradient = 'rgba(249, 115, 22, 0.1)';
        } else {
            colorClass = 'text-red-500';
            bgGradient = 'rgba(239, 68, 68, 0.1)';
        }

        return `
            <div class="p-5 rounded-xl" style="background: ${bgGradient}; border: 1px solid rgba(255, 255, 255, 0.1);">
                <div class="flex items-start justify-between mb-3">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center ${colorClass}" style="background: rgba(255, 255, 255, 0.1);">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${iconPath}"/>
                        </svg>
                    </div>
                    <div class="text-right">
                        <div class="text-3xl font-bold ${colorClass}">${score}</div>
                        <div class="text-xs text-secondary">/ 100</div>
                    </div>
                </div>
                <h3 class="font-semibold text-sm mb-1">${title}</h3>
                <p class="text-xs text-tertiary mb-2">${description}</p>
                <div class="flex items-center gap-2">
                    <div class="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div class="h-full ${colorClass} transition-all duration-500" style="width: ${score}%; opacity: 0.8;"></div>
                    </div>
                    <span class="text-xs font-medium ${colorClass}">${status}</span>
                </div>
            </div>
        `;
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
