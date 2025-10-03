/**
 * AI Insights Manager
 * Handles all AI-powered insights for meeting transcripts
 * Implements T2.11-T2.22
 */

class AIInsightsManager {
    constructor(meetingId) {
        this.meetingId = meetingId;
        this.currentTab = 'summary';
        this.insights = null;
        this.loading = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInsights();
    }

    bindEvents() {
        // Tab switching - Use currentTarget to handle clicks on nested elements
        document.querySelectorAll('.ai-insights-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                if (tabName) {
                    this.switchTab(tabName);
                }
            });
        });

        // Refresh button
        const refreshBtn = document.querySelector('[data-action="refresh-insights"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadInsights(true));
        }

        // Quality feedback buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.ai-quality-btn');
            if (btn) {
                this.handleQualityFeedback(btn);
            }
        });

        // Custom prompt submit
        const customPromptForm = document.querySelector('.ai-custom-prompt-form');
        if (customPromptForm) {
            customPromptForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.executeCustomPrompt();
            });
        }

        // Template buttons - Use currentTarget to handle clicks on nested elements
        document.querySelectorAll('.ai-prompt-template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const template = e.currentTarget.dataset.template;
                if (template) {
                    this.loadPromptTemplate(template);
                }
            });
        });

        // Action item buttons - Use data-action-index to safely retrieve data
        document.addEventListener('click', (e) => {
            const actionBtn = e.target.closest('[data-action="create-task"]');
            if (actionBtn && actionBtn.dataset.actionIndex !== undefined) {
                const index = parseInt(actionBtn.dataset.actionIndex, 10);
                if (this.actionItems && this.actionItems[index]) {
                    this.createTaskFromAction(this.actionItems[index]);
                } else {
                    console.error('Action item not found at index:', index);
                }
            }
            
            const calendarBtn = e.target.closest('[data-action="add-to-calendar"]');
            if (calendarBtn && calendarBtn.dataset.actionIndex !== undefined) {
                const index = parseInt(calendarBtn.dataset.actionIndex, 10);
                if (this.actionItems && this.actionItems[index]) {
                    this.addToCalendar(this.actionItems[index]);
                }
            }
        });

        // Topic tag filtering
        document.addEventListener('click', (e) => {
            const topicTag = e.target.closest('.ai-topic-tag');
            if (topicTag && topicTag.dataset.topic) {
                const topic = topicTag.dataset.topic;
                this.filterByTopic(topic);
            }
        });
    }

    async loadInsights(forceRefresh = false) {
        if (this.loading) return;
        
        this.loading = true;
        this.showLoading();

        try {
            const response = await fetch(`/api/meetings/${this.meetingId}/ai/insights`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.insights = data.insights;
                this.renderInsights();
                
                // Re-enable tabs after successful load
                document.querySelectorAll('.ai-insights-tab').forEach(tab => {
                    tab.style.pointerEvents = '';
                    tab.style.opacity = '';
                });
                
                this.showToast('AI insights loaded successfully', 'success');
            } else {
                this.showError(data.message || 'Failed to load AI insights');
            }
        } catch (error) {
            console.error('Failed to load AI insights:', error);
            this.showError('Network error loading AI insights');
        } finally {
            this.loading = false;
        }
    }

    switchTab(tabName) {
        // Defensive guard: do nothing if tabName is falsy
        if (!tabName) {
            console.warn('switchTab called with invalid tabName:', tabName);
            return;
        }
        
        this.currentTab = tabName;
        
        // Update active tab
        document.querySelectorAll('.ai-insights-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // Show corresponding content
        document.querySelectorAll('.ai-insights-content').forEach(content => {
            content.style.display = content.dataset.tab === tabName ? 'block' : 'none';
        });
    }

    renderInsights() {
        if (!this.insights) return;

        // Render each section
        this.renderSummary();
        this.renderKeyPoints();
        this.renderActionItems();
        this.renderQuestions();
        this.renderDecisions();
        this.renderSentiment();
        this.renderTopics();
        this.updateTabBadges();
    }

    renderSummary() {
        const container = document.querySelector('.ai-insights-content[data-tab="summary"]');
        if (!container) return;

        const summary = this.insights.summary || 'No summary available';
        const paragraphs = this.insights.paragraphs || [summary];
        
        container.innerHTML = `
            <div class="ai-summary-card">
                <div class="ai-summary-text">
                    ${paragraphs.map(p => `<p>${this.escapeHtml(p)}</p>`).join('')}
                </div>
                <div class="ai-summary-meta">
                    <span><i class="fas fa-brain"></i> Generated by GPT-4</span>
                    <span><i class="fas fa-clock"></i> ${this.formatTime(this.insights.generated_at)}</span>
                    ${this.insights.confidence_score ? `
                        <span><i class="fas fa-chart-line"></i> ${Math.round(this.insights.confidence_score * 100)}% confidence</span>
                    ` : ''}
                </div>
            </div>
            ${this.renderQualityFeedback('summary')}
        `;
    }

    renderKeyPoints() {
        const container = document.querySelector('.ai-insights-content[data-tab="key-points"]');
        if (!container) return;

        const keyPoints = this.insights.key_points || [];
        
        if (keyPoints.length === 0) {
            container.innerHTML = this.renderEmpty('No key points extracted');
            return;
        }

        container.innerHTML = `
            <div class="ai-key-points-list">
                ${keyPoints.map((point, index) => `
                    <div class="ai-key-point" data-point-index="${index}">
                        <div class="ai-key-point-header">
                            <div class="ai-key-point-icon">${index + 1}</div>
                            ${point.importance ? `
                                <span class="ai-key-point-importance ${point.importance.toLowerCase()}">
                                    ${point.importance}
                                </span>
                            ` : ''}
                            ${this.renderConfidenceIndicator(point.confidence)}
                        </div>
                        <div class="ai-key-point-text">${this.escapeHtml(point.point || point)}</div>
                    </div>
                `).join('')}
            </div>
            ${this.renderQualityFeedback('key-points')}
        `;
    }

    renderActionItems() {
        const container = document.querySelector('.ai-insights-content[data-tab="action-items"]');
        if (!container) return;

        const actionItems = this.insights.action_items || [];
        
        if (actionItems.length === 0) {
            container.innerHTML = this.renderEmpty('No action items found');
            return;
        }

        // Store action items in instance for safe access
        this.actionItems = actionItems;
        
        container.innerHTML = `
            <div class="ai-action-items-list">
                ${actionItems.map((item, index) => `
                    <div class="ai-action-item ${item.priority ? item.priority.toLowerCase() : 'medium'}">
                        <div class="ai-action-item-header">
                            <div class="ai-action-item-task">${this.escapeHtml(item.task)}</div>
                            ${item.priority ? `
                                <span class="ai-action-item-priority ${item.priority.toLowerCase()}">
                                    ${item.priority}
                                </span>
                            ` : ''}
                        </div>
                        <div class="ai-action-item-meta">
                            ${item.assignee ? `
                                <span><i class="fas fa-user"></i> ${this.escapeHtml(item.assignee)}</span>
                            ` : ''}
                            ${item.due_date ? `
                                <span><i class="fas fa-calendar"></i> ${this.escapeHtml(item.due_date)}</span>
                            ` : ''}
                            ${this.renderConfidenceIndicator(item.confidence)}
                        </div>
                        <div class="ai-action-item-actions">
                            <button class="ai-action-item-btn" data-action="create-task" data-action-index="${index}">
                                <i class="fas fa-plus"></i> Create Task
                            </button>
                            <button class="ai-action-item-btn" data-action="add-to-calendar" data-action-index="${index}">
                                <i class="fas fa-calendar-plus"></i> Add to Calendar
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
            ${this.renderQualityFeedback('action-items')}
        `;
    }

    renderQuestions() {
        const container = document.querySelector('.ai-insights-content[data-tab="questions"]');
        if (!container) return;

        const questions = this.insights.questions || [];
        
        if (questions.length === 0) {
            container.innerHTML = this.renderEmpty('No questions identified');
            return;
        }

        container.innerHTML = `
            <div class="ai-questions-list">
                ${questions.map(q => `
                    <div class="ai-question">
                        <div class="ai-question-status">
                            <span class="ai-question-badge ${q.answered ? 'answered' : 'unanswered'}">
                                ${q.answered ? '✓ Answered' : '⚠ Unanswered'}
                            </span>
                            ${q.asker ? `<span class="ai-question-asker">Asked by ${this.escapeHtml(q.asker)}</span>` : ''}
                        </div>
                        <div class="ai-question-text">${this.escapeHtml(q.question)}</div>
                        ${q.answer ? `
                            <div class="ai-question-answer">
                                <strong>Answer:</strong> ${this.escapeHtml(q.answer)}
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
            ${this.renderQualityFeedback('questions')}
        `;
    }

    renderDecisions() {
        const container = document.querySelector('.ai-insights-content[data-tab="decisions"]');
        if (!container) return;

        const decisions = this.insights.decisions || [];
        
        if (decisions.length === 0) {
            container.innerHTML = this.renderEmpty('No decisions recorded');
            return;
        }

        container.innerHTML = `
            <div class="ai-decisions-list">
                ${decisions.map(d => `
                    <div class="ai-decision">
                        <div class="ai-decision-text">${this.escapeHtml(d.decision)}</div>
                        ${d.rationale ? `
                            <div class="ai-decision-rationale">
                                <strong>Rationale:</strong> ${this.escapeHtml(d.rationale)}
                            </div>
                        ` : ''}
                        <div class="ai-decision-meta">
                            ${d.impact ? `
                                <span><i class="fas fa-bolt"></i> ${d.impact} impact</span>
                            ` : ''}
                            ${d.decided_by ? `
                                <span><i class="fas fa-user-tie"></i> ${this.escapeHtml(d.decided_by)}</span>
                            ` : ''}
                            ${this.renderConfidenceIndicator(d.confidence)}
                        </div>
                    </div>
                `).join('')}
            </div>
            ${this.renderQualityFeedback('decisions')}
        `;
    }

    renderSentiment() {
        const container = document.querySelector('.ai-insights-content[data-tab="sentiment"]');
        if (!container) return;

        const sentiment = this.insights.sentiment || { overall: 'neutral', score: 0.5 };
        const iconMap = {
            positive: 'fa-smile',
            neutral: 'fa-meh',
            negative: 'fa-frown'
        };

        container.innerHTML = `
            <div class="ai-sentiment-card">
                <div class="ai-sentiment-header">
                    <div class="ai-sentiment-score">
                        <div class="ai-sentiment-icon ${sentiment.overall}">
                            <i class="fas ${iconMap[sentiment.overall] || 'fa-meh'}"></i>
                        </div>
                        <div>
                            <div class="ai-sentiment-label">${sentiment.overall}</div>
                            <div class="ai-sentiment-score-value">Confidence: ${Math.round(sentiment.score * 100)}%</div>
                        </div>
                    </div>
                </div>
                <div class="ai-sentiment-meter">
                    <div class="ai-sentiment-meter-fill ${sentiment.overall}" style="width: ${sentiment.score * 100}%"></div>
                </div>
                ${sentiment.explanation ? `
                    <div class="ai-sentiment-explanation">
                        ${this.escapeHtml(sentiment.explanation)}
                    </div>
                ` : ''}
            </div>
            ${this.renderQualityFeedback('sentiment')}
        `;
    }

    renderTopics() {
        const container = document.querySelector('.ai-insights-content[data-tab="topics"]');
        if (!container) return;

        const topics = this.insights.topics || [];
        
        if (topics.length === 0) {
            container.innerHTML = this.renderEmpty('No topics detected');
            return;
        }

        container.innerHTML = `
            <div class="ai-topics-grid">
                ${topics.map((topic, index) => `
                    <button class="ai-topic-tag" data-topic="${this.escapeHtml(topic)}" style="animation-delay: ${index * 0.05}s">
                        ${this.escapeHtml(topic)}
                    </button>
                `).join('')}
            </div>
            ${this.renderQualityFeedback('topics')}
        `;
    }

    renderConfidenceIndicator(confidence) {
        if (!confidence) return '';
        
        const level = confidence > 0.8 ? 'high' : confidence > 0.5 ? 'medium' : 'low';
        const dots = 3;
        
        return `
            <span class="ai-confidence-indicator ${level}" title="AI Confidence: ${Math.round(confidence * 100)}%">
                <span class="ai-confidence-dots">
                    ${Array(dots).fill('<span class="ai-confidence-dot"></span>').join('')}
                </span>
            </span>
        `;
    }

    renderQualityFeedback(section) {
        return `
            <div class="ai-quality-feedback">
                <span class="ai-quality-label">Was this helpful?</span>
                <div class="ai-quality-buttons">
                    <button class="ai-quality-btn thumbs-up" data-section="${section}" data-feedback="positive">
                        <i class="fas fa-thumbs-up"></i>
                    </button>
                    <button class="ai-quality-btn thumbs-down" data-section="${section}" data-feedback="negative">
                        <i class="fas fa-thumbs-down"></i>
                    </button>
                </div>
            </div>
        `;
    }

    renderEmpty(message) {
        return `
            <div class="ai-insights-empty">
                <i class="fas fa-inbox"></i>
                <h3>${message}</h3>
                <p>AI analysis did not find relevant items in this category</p>
            </div>
        `;
    }

    handleQualityFeedback(button) {
        const section = button.dataset.section;
        const feedback = button.dataset.feedback;
        
        // Toggle active state
        const parent = button.parentElement;
        parent.querySelectorAll('.ai-quality-btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // Send feedback to server
        this.submitFeedback(section, feedback);
        
        this.showToast('Thank you for your feedback!', 'success');
    }

    async submitFeedback(section, feedback) {
        try {
            await fetch(`/api/meetings/${this.meetingId}/ai/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ section, feedback })
            });
        } catch (error) {
            console.error('Failed to submit feedback:', error);
        }
    }

    async executeCustomPrompt() {
        const textarea = document.querySelector('.ai-custom-prompt-textarea');
        const prompt = textarea.value.trim();
        
        if (!prompt) {
            this.showToast('Please enter a prompt', 'error');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/api/meetings/${this.meetingId}/ai/custom-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            if (data.success) {
                this.displayCustomPromptResult(data.result);
                this.showToast('Custom analysis completed', 'success');
            } else {
                this.showError(data.message || 'Failed to execute custom prompt');
            }
        } catch (error) {
            console.error('Failed to execute custom prompt:', error);
            this.showError('Network error');
        }
    }

    displayCustomPromptResult(result) {
        const resultContainer = document.querySelector('.ai-custom-prompt-result') || 
                              this.createCustomPromptResultContainer();
        
        resultContainer.innerHTML = `
            <h4>Analysis Result</h4>
            <pre>${JSON.stringify(result, null, 2)}</pre>
        `;
        resultContainer.style.display = 'block';
    }

    createCustomPromptResultContainer() {
        const container = document.createElement('div');
        container.className = 'ai-custom-prompt-result';
        document.querySelector('.ai-custom-prompt-form').appendChild(container);
        return container;
    }

    loadPromptTemplate(template) {
        // Defensive guard: do nothing if template is falsy
        if (!template) {
            console.warn('loadPromptTemplate called with invalid template:', template);
            return;
        }
        
        const templates = {
            risks: 'Identify potential risks and concerns mentioned in this meeting.',
            followup: 'What follow-up meetings or actions are needed based on this discussion?',
            stakeholders: 'Who are the key stakeholders mentioned and what are their concerns?',
            timeline: 'Extract any timelines, deadlines, or milestones mentioned.',
            budget: 'Identify any budget-related discussions or financial commitments.'
        };
        
        const textarea = document.querySelector('.ai-custom-prompt-textarea');
        if (textarea && templates[template]) {
            textarea.value = templates[template];
            this.showToast(`Template loaded: ${template}`, 'success');
        } else if (textarea) {
            console.warn('Template not found:', template);
        }
    }

    async createTaskFromAction(actionData) {
        // This would integrate with the tasks system
        console.log('Creating task:', actionData);
        this.showToast('Task creation feature coming soon', 'info');
    }
    
    async addToCalendar(actionData) {
        // This would integrate with the calendar system
        console.log('Adding to calendar:', actionData);
        this.showToast('Calendar integration coming soon', 'info');
    }

    filterByTopic(topic) {
        // Toggle topic filter
        const tag = document.querySelector(`[data-topic="${topic}"]`);
        tag.classList.toggle('active');
        
        // This would filter the transcript view by topic
        console.log('Filtering by topic:', topic);
        this.showToast(`Filtering by: ${topic}`, 'info');
    }

    updateTabBadges() {
        if (!this.insights) return;

        const badges = {
            'key-points': this.insights.key_points?.length || 0,
            'action-items': this.insights.action_items?.length || 0,
            'questions': this.insights.questions?.length || 0,
            'decisions': this.insights.decisions?.length || 0,
            'topics': this.insights.topics?.length || 0
        };

        Object.entries(badges).forEach(([tab, count]) => {
            const tabEl = document.querySelector(`[data-tab="${tab}"]`);
            if (tabEl && count > 0) {
                const existingBadge = tabEl.querySelector('.badge');
                if (existingBadge) {
                    existingBadge.textContent = count;
                } else {
                    const badge = document.createElement('span');
                    badge.className = 'badge';
                    badge.textContent = count;
                    tabEl.appendChild(badge);
                }
            }
        });
    }

    showLoading() {
        // Show loading in the current tab's content area only - don't destroy DOM structure
        const currentContent = document.querySelector(`.ai-insights-content[data-tab="${this.currentTab}"]`);
        if (!currentContent) return;

        currentContent.innerHTML = `
            <div class="ai-insights-loading">
                <div class="ai-spinner"></div>
                <p>Analyzing transcript with AI...</p>
            </div>
        `;
        
        // Disable tabs during loading
        document.querySelectorAll('.ai-insights-tab').forEach(tab => {
            tab.style.pointerEvents = 'none';
            tab.style.opacity = '0.6';
        });
    }

    showError(message) {
        // Show error in the current tab's content area only - don't destroy DOM structure
        const currentContent = document.querySelector(`.ai-insights-content[data-tab="${this.currentTab}"]`);
        if (!currentContent) return;

        currentContent.innerHTML = `
            <div class="ai-insights-error">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Failed to Load AI Insights</h3>
                <p>${this.escapeHtml(message)}</p>
                <button class="btn btn-primary" onclick="location.reload()">Retry</button>
            </div>
        `;
        
        // Re-enable tabs after error
        document.querySelectorAll('.ai-insights-tab').forEach(tab => {
            tab.style.pointerEvents = '';
            tab.style.opacity = '';
        });
    }

    showToast(message, type = 'info') {
        // Reuse existing toast system
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(isoString) {
        if (!isoString) return 'just now';
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAIInsights);
} else {
    initAIInsights();
}

function initAIInsights() {
    const insightsPanel = document.querySelector('[data-meeting-id]');
    if (insightsPanel) {
        const meetingId = insightsPanel.dataset.meetingId;
        window.aiInsightsManager = new AIInsightsManager(meetingId);
    }
}
