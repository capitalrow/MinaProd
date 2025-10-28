// Feature Flags Admin - CROWN⁴ Implementation
// Optimistic updates + audit logging + WebSocket sync

class FeatureFlagsAdmin {
    constructor() {
        this.flags = [];
        this.filteredFlags = [];
        this.currentAction = null;
        this.socket = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.initWebSocket();
        await this.loadFlags();
    }

    setupEventListeners() {
        // Search
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filterFlags(e.target.value);
        });

        // New Flag Button
        document.getElementById('btnNewFlag').addEventListener('click', () => {
            this.openCreateModal();
        });

        // Modal Actions
        document.getElementById('btnCancelModal').addEventListener('click', () => {
            this.closeModal('flagModal');
        });

        document.getElementById('btnSaveFlag').addEventListener('click', () => {
            this.saveFlag();
        });

        // Confirmation Modal
        document.getElementById('btnCancelConfirm').addEventListener('click', () => {
            this.closeModal('confirmModal');
        });

        document.getElementById('btnConfirmAction').addEventListener('click', () => {
            this.executeConfirmedAction();
        });

        // Close modals on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closeModal(overlay.id);
                }
            });
        });
    }

    initWebSocket() {
        if (typeof io === 'undefined') return;

        this.socket = io('/flags', {
            transports: ['websocket', 'polling']
        });

        this.socket.on('connect', () => {
            console.log('✅ Connected to flags namespace');
        });

        this.socket.on('flag_updated', (data) => {
            console.log('📡 Flag updated via WebSocket:', data);
            this.handleRemoteUpdate(data);
        });

        this.socket.on('flag_deleted', (data) => {
            console.log('📡 Flag deleted via WebSocket:', data);
            this.handleRemoteDelete(data);
        });

        this.socket.on('disconnect', () => {
            console.log('⚠️ Disconnected from flags namespace');
        });
    }

    async loadFlags() {
        try {
            const response = await fetch('/flags/');
            const data = await response.json();

            if (data.success) {
                this.flags = data.flags || [];
                this.filteredFlags = [...this.flags];
                this.renderFlags();
            } else {
                this.showError(data.error || 'Failed to load flags');
            }
        } catch (error) {
            console.error('Failed to load flags:', error);
            this.showError('Failed to load flags. Please refresh the page.');
            this.renderError();
        }
    }

    filterFlags(query) {
        const lowerQuery = query.toLowerCase().trim();
        if (!lowerQuery) {
            this.filteredFlags = [...this.flags];
        } else {
            this.filteredFlags = this.flags.filter(flag =>
                flag.key.toLowerCase().includes(lowerQuery) ||
                (flag.note && flag.note.toLowerCase().includes(lowerQuery))
            );
        }
        this.renderFlags();
    }

    renderFlags() {
        const container = document.getElementById('flagsContainer');

        if (this.filteredFlags.length === 0) {
            if (this.flags.length === 0) {
                container.innerHTML = this.renderEmptyState();
            } else {
                container.innerHTML = this.renderNoResults();
            }
            return;
        }

        container.innerHTML = this.filteredFlags
            .map((flag, index) => this.renderFlagCard(flag, index))
            .join('');

        // Attach event listeners
        this.attachCardListeners();
    }

    renderFlagCard(flag, index) {
        return `
            <div class="flag-card ${flag.enabled ? 'enabled' : ''}" data-key="${flag.key}" style="animation-delay: ${0.2 + index * 0.05}s">
                <div class="flag-card-header">
                    <div class="flag-key">${this.escapeHtml(flag.key)}</div>
                    <div class="flag-toggle-wrapper">
                        <div class="toggle-switch ${flag.enabled ? 'enabled' : ''}" 
                             data-key="${flag.key}"
                             role="switch"
                             aria-checked="${flag.enabled}"
                             tabindex="0">
                            <div class="toggle-slider"></div>
                        </div>
                    </div>
                </div>
                <div class="flag-note">${flag.note ? this.escapeHtml(flag.note) : '<em>No description</em>'}</div>
                <div class="flag-actions">
                    <button class="flag-action-btn btn-edit" data-key="${flag.key}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        Edit
                    </button>
                    <button class="flag-action-btn btn-history" data-key="${flag.key}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        History
                    </button>
                    <button class="flag-action-btn danger btn-delete" data-key="${flag.key}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Delete
                    </button>
                </div>
            </div>
        `;
    }

    renderEmptyState() {
        return `
            <div class="state-container">
                <div class="state-icon">🏴</div>
                <h2 class="state-title">No Feature Flags Yet</h2>
                <p class="state-message">Create your first feature flag to start controlling feature rollouts.</p>
                <button class="btn-new-flag" onclick="featureFlagsAdmin.openCreateModal()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    Create First Flag
                </button>
            </div>
        `;
    }

    renderNoResults() {
        return `
            <div class="state-container">
                <div class="state-icon">🔍</div>
                <h2 class="state-title">No Matching Flags</h2>
                <p class="state-message">Try adjusting your search query.</p>
            </div>
        `;
    }

    renderError() {
        const container = document.getElementById('flagsContainer');
        container.innerHTML = `
            <div class="state-container">
                <div class="state-icon">⚠️</div>
                <h2 class="state-title">Failed to Load Flags</h2>
                <p class="state-message">Please refresh the page to try again.</p>
                <button class="btn-new-flag" onclick="location.reload()">
                    Refresh Page
                </button>
            </div>
        `;
    }

    attachCardListeners() {
        // Toggle switches
        document.querySelectorAll('.toggle-switch').forEach(toggle => {
            toggle.addEventListener('click', () => {
                this.toggleFlag(toggle.dataset.key);
            });
            toggle.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleFlag(toggle.dataset.key);
                }
            });
        });

        // Edit buttons
        document.querySelectorAll('.btn-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openEditModal(btn.dataset.key);
            });
        });

        // History buttons
        document.querySelectorAll('.btn-history').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showHistory(btn.dataset.key);
            });
        });

        // Delete buttons
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.confirmDelete(btn.dataset.key);
            });
        });
    }

    async toggleFlag(key) {
        const flag = this.flags.find(f => f.key === key);
        if (!flag) return;

        // Optimistic update
        const oldEnabled = flag.enabled;
        flag.enabled = !flag.enabled;
        this.updateFlagCard(key);

        try {
            const response = await fetch(`/flags/${key}/toggle`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (!data.success) {
                // Rollback on failure
                flag.enabled = oldEnabled;
                this.updateFlagCard(key);
                this.showError(data.error || 'Failed to toggle flag');
            } else {
                this.showSuccess(`Flag "${key}" ${flag.enabled ? 'enabled' : 'disabled'}`);
            }
        } catch (error) {
            // Rollback on error
            flag.enabled = oldEnabled;
            this.updateFlagCard(key);
            this.showError('Network error. Changes reverted.');
        }
    }

    updateFlagCard(key) {
        const card = document.querySelector(`.flag-card[data-key="${key}"]`);
        if (!card) return;

        const flag = this.flags.find(f => f.key === key);
        if (!flag) return;

        const toggle = card.querySelector('.toggle-switch');
        if (flag.enabled) {
            card.classList.add('enabled');
            toggle.classList.add('enabled');
            toggle.setAttribute('aria-checked', 'true');
        } else {
            card.classList.remove('enabled');
            toggle.classList.remove('enabled');
            toggle.setAttribute('aria-checked', 'false');
        }
    }

    openCreateModal() {
        document.getElementById('modalTitle').textContent = 'Create Feature Flag';
        document.getElementById('flagKey').value = '';
        document.getElementById('flagKey').disabled = false;
        document.getElementById('flagNote').value = '';
        document.getElementById('flagEnabled').checked = false;
        document.getElementById('keyError').textContent = '';
        document.getElementById('noteError').textContent = '';
        this.currentAction = { mode: 'create' };
        this.openModal('flagModal');
    }

    openEditModal(key) {
        const flag = this.flags.find(f => f.key === key);
        if (!flag) return;

        document.getElementById('modalTitle').textContent = 'Edit Feature Flag';
        document.getElementById('flagKey').value = flag.key;
        document.getElementById('flagKey').disabled = true;
        document.getElementById('flagNote').value = flag.note || '';
        document.getElementById('flagEnabled').checked = flag.enabled;
        document.getElementById('keyError').textContent = '';
        document.getElementById('noteError').textContent = '';
        this.currentAction = { mode: 'edit', key: flag.key };
        this.openModal('flagModal');
    }

    async saveFlag() {
        const key = document.getElementById('flagKey').value.trim();
        const note = document.getElementById('flagNote').value.trim();
        const enabled = document.getElementById('flagEnabled').checked;

        // Validation
        document.getElementById('keyError').textContent = '';
        document.getElementById('noteError').textContent = '';

        if (!key) {
            document.getElementById('keyError').textContent = 'Flag key is required';
            return;
        }

        if (!/^[a-zA-Z0-9_-]+$/.test(key)) {
            document.getElementById('keyError').textContent = 'Only alphanumeric, underscore, and hyphen characters allowed';
            return;
        }

        if (note.length > 255) {
            document.getElementById('noteError').textContent = 'Note must be 255 characters or less';
            return;
        }

        try {
            const response = await fetch('/flags/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, enabled, note: note || null })
            });

            const data = await response.json();

            if (data.success) {
                if (data.action === 'create') {
                    this.flags.push(data.flag);
                    this.showSuccess(`Flag "${key}" created successfully`);
                } else {
                    const index = this.flags.findIndex(f => f.key === key);
                    if (index !== -1) {
                        this.flags[index] = data.flag;
                    }
                    this.showSuccess(`Flag "${key}" updated successfully`);
                }
                this.filterFlags(document.getElementById('searchInput').value);
                this.closeModal('flagModal');
            } else {
                this.showError(data.error || 'Failed to save flag');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
        }
    }

    confirmDelete(key) {
        document.getElementById('confirmTitle').textContent = 'Delete Feature Flag?';
        document.getElementById('confirmMessage').textContent = 
            `Are you sure you want to delete the flag "${key}"? This action cannot be undone.`;
        this.currentAction = { mode: 'delete', key };
        this.openModal('confirmModal');
    }

    async executeConfirmedAction() {
        if (!this.currentAction || this.currentAction.mode !== 'delete') return;

        const key = this.currentAction.key;
        this.closeModal('confirmModal');

        try {
            const response = await fetch(`/flags/${key}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.flags = this.flags.filter(f => f.key !== key);
                this.filterFlags(document.getElementById('searchInput').value);
                this.showSuccess(`Flag "${key}" deleted successfully`);
            } else {
                this.showError(data.error || 'Failed to delete flag');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
        }
    }

    async showHistory(key) {
        try {
            const response = await fetch(`/flags/${key}/history`);
            const data = await response.json();

            if (data.success && data.history) {
                this.renderHistoryModal(key, data.history);
            } else {
                this.showError('Failed to load history');
            }
        } catch (error) {
            this.showError('Failed to load history');
        }
    }

    renderHistoryModal(key, history) {
        // Create a simple history display
        const historyHtml = history.length === 0
            ? '<p class="state-message">No history available for this flag.</p>'
            : history.map(log => `
                <div style="padding: var(--space-3); border-left: 2px solid var(--color-primary); margin-bottom: var(--space-2);">
                    <div style="font-weight: var(--font-weight-semibold);">${log.action.toUpperCase()}</div>
                    <div style="color: var(--color-text-secondary); font-size: var(--font-size-sm);">
                        By: ${log.user_id} | ${new Date(log.created_at).toLocaleString()}
                    </div>
                    ${log.old_value && log.new_value ? `
                        <div style="margin-top: var(--space-2); font-size: var(--font-size-sm);">
                            ${JSON.stringify(log.old_value)} → ${JSON.stringify(log.new_value)}
                        </div>
                    ` : ''}
                </div>
            `).join('');

        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h2 class="modal-title">Audit History: ${key}</h2>
                </div>
                <div class="modal-body" style="max-height: 400px; overflow-y: auto;">
                    ${historyHtml}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">Close</button>
                </div>
            </div>
        `;

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

        document.body.appendChild(modal);
    }

    handleRemoteUpdate(data) {
        const index = this.flags.findIndex(f => f.key === data.flag.key);
        if (index !== -1) {
            this.flags[index] = data.flag;
        } else {
            this.flags.push(data.flag);
        }
        this.filterFlags(document.getElementById('searchInput').value);
    }

    handleRemoteDelete(data) {
        this.flags = this.flags.filter(f => f.key !== data.key);
        this.filterFlags(document.getElementById('searchInput').value);
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
        this.currentAction = null;
    }

    showSuccess(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'success');
        } else {
            console.log('✅', message);
        }
    }

    showError(message) {
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'error');
        } else {
            console.error('❌', message);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize
const featureFlagsAdmin = new FeatureFlagsAdmin();
