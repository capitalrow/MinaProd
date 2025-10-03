/**
 * Sharing functionality for Phase 2 Group 4 (T2.23-T2.27)
 * Handles link sharing, email sharing, and embed functionality
 */

class ShareManager {
    constructor(meetingId) {
        this.meetingId = meetingId;
        this.activeShares = [];
        this.currentShareToken = null;
    }

    async init() {
        await this.loadActiveShares();
    }

    async loadActiveShares() {
        try {
            const response = await fetch(`/api/sessions/${this.meetingId}/shares`);
            const data = await response.json();
            
            if (data.success && data.links) {
                this.activeShares = data.links;
                this.renderActiveShares();
            }
        } catch (error) {
            console.error('Failed to load active shares:', error);
        }
    }

    renderActiveShares() {
        const container = document.getElementById('sharesList');
        if (!container) return;

        if (this.activeShares.length === 0) {
            container.innerHTML = `
                <p style="color: var(--color-text-tertiary); font-size: var(--font-size-sm); text-align: center;">
                    No active shares yet
                </p>
            `;
            return;
        }

        container.innerHTML = this.activeShares.map(share => `
            <div class="active-share-item" style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-3); background: var(--color-surface); border-radius: var(--radius-lg); margin-bottom: var(--space-2);">
                <div style="flex: 1; min-width: 0;">
                    <div style="font-size: var(--font-size-sm); color: var(--color-text-primary); font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${share.url}
                    </div>
                    <div style="font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: var(--space-1);">
                        <i class="fas fa-clock"></i> Expires: ${this.formatDate(share.expires_at)}
                    </div>
                </div>
                <div style="display: flex; gap: var(--space-2);">
                    <button onclick="shareManager.copyUrl('${share.url}')" class="btn btn-secondary btn-sm" title="Copy URL">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button onclick="shareManager.deactivateShare('${share.token}')" class="btn btn-danger btn-sm" title="Deactivate">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    formatDate(dateStr) {
        if (!dateStr) return 'Never';
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    async createShareLink() {
        const expiresInDays = parseInt(document.getElementById('shareExpiration').value) || 7;
        const privacyLevel = document.getElementById('sharePrivacy').value || 'public';

        try {
            const response = await fetch(`/api/sessions/${this.meetingId}/share`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    expires_in_days: expiresInDays,
                    privacy_level: privacyLevel
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentShareToken = data.token;
                this.displayShareUrl(data.url, data.expires_in_days);
                await this.loadActiveShares();
                this.showToast('Share link created successfully!', 'success');
            } else {
                this.showToast(data.error || 'Failed to create share link', 'error');
            }
        } catch (error) {
            console.error('Error creating share link:', error);
            this.showToast('Network error creating share link', 'error');
        }
    }

    displayShareUrl(url, expiresInDays) {
        const container = document.getElementById('shareUrlContainer');
        const urlInput = document.getElementById('shareUrl');
        const expirySpan = document.getElementById('shareExpiry');

        urlInput.value = url;
        
        const expiryDate = new Date();
        expiryDate.setDate(expiryDate.getDate() + expiresInDays);
        expirySpan.textContent = this.formatDate(expiryDate.toISOString());

        container.style.display = 'block';
    }

    copyUrl(url) {
        navigator.clipboard.writeText(url).then(() => {
            this.showToast('URL copied to clipboard!', 'success');
        }).catch(() => {
            this.showToast('Failed to copy URL', 'error');
        });
    }

    async deactivateShare(token) {
        if (!confirm('Are you sure you want to deactivate this share link?')) {
            return;
        }

        try {
            const response = await fetch(`/api/sessions/${this.meetingId}/share/${token}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Share link deactivated', 'success');
                await this.loadActiveShares();
            } else {
                this.showToast(data.error || 'Failed to deactivate link', 'error');
            }
        } catch (error) {
            console.error('Error deactivating share:', error);
            this.showToast('Network error', 'error');
        }
    }

    async sendEmailShare() {
        const email = document.getElementById('shareEmail').value.trim();
        const includePdf = document.getElementById('includePdf').checked;
        const message = document.getElementById('shareMessage').value.trim();

        if (!email) {
            this.showToast('Please enter an email address', 'error');
            return;
        }

        if (!this.isValidEmail(email)) {
            this.showToast('Please enter a valid email address', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/sessions/${this.meetingId}/share/email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    include_pdf: includePdf,
                    message: message
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast(data.message || 'Email sent successfully!', 'success');
                document.getElementById('shareEmail').value = '';
                document.getElementById('shareMessage').value = '';
            } else {
                this.showToast(data.error || 'Failed to send email', 'error');
            }
        } catch (error) {
            console.error('Error sending email:', error);
            this.showToast('Network error sending email', 'error');
        }
    }

    generateEmbedCode(token) {
        const baseUrl = window.location.origin;
        return `<iframe 
    src="${baseUrl}/share/${token}" 
    width="100%" 
    height="600" 
    frameborder="0" 
    allowfullscreen
    style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
</iframe>`;
    }

    copyEmbedCode() {
        const embedCode = document.getElementById('embedCode').value;
        navigator.clipboard.writeText(embedCode).then(() => {
            this.showToast('Embed code copied to clipboard!', 'success');
        }).catch(() => {
            this.showToast('Failed to copy embed code', 'error');
        });
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    showToast(message, type = 'info') {
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            alert(message);
        }
    }
}

// Global functions for onclick handlers
let shareManager;

function openShareModal() {
    const modal = document.getElementById('shareModal');
    if (modal) {
        modal.style.display = 'flex';
        
        // Initialize share manager if not already done
        const meetingId = document.querySelector('.ai-insights-panel')?.dataset.meetingId;
        if (meetingId && !shareManager) {
            shareManager = new ShareManager(meetingId);
            shareManager.init();
        }
        
        // Switch to link tab by default
        switchShareTab('link');
    }
}

function closeShareModal() {
    const modal = document.getElementById('shareModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function switchShareTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.share-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update content visibility
    document.querySelectorAll('.share-content').forEach(content => {
        content.style.display = 'none';
    });
    
    const activeContent = document.getElementById(`share-${tabName}-content`);
    if (activeContent) {
        activeContent.style.display = 'block';
    }
    
    // Handle embed tab - generate embed code
    if (tabName === 'embed' && shareManager && shareManager.currentShareToken) {
        const embedCode = shareManager.generateEmbedCode(shareManager.currentShareToken);
        document.getElementById('embedCode').value = embedCode;
    } else if (tabName === 'embed') {
        document.getElementById('embedCode').value = '// Create a share link first to generate embed code';
    }
}

function createShareLink() {
    if (shareManager) {
        shareManager.createShareLink();
    }
}

function copyShareUrl() {
    const url = document.getElementById('shareUrl').value;
    if (shareManager) {
        shareManager.copyUrl(url);
    }
}

function sendEmailShare() {
    if (shareManager) {
        shareManager.sendEmailShare();
    }
}

function copyEmbedCode() {
    if (shareManager) {
        shareManager.copyEmbedCode();
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('shareModal');
    if (e.target === modal) {
        closeShareModal();
    }
});
