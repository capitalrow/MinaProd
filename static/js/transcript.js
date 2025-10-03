/**
 * Enhanced Transcript Interaction System
 * Handles search, copy, edit, speaker identification, and keyboard shortcuts
 * Part of Phase 2: Transcript Experience Enhancement
 */

class TranscriptManager {
    constructor(meetingId) {
        this.meetingId = meetingId;
        this.segments = [];
        this.searchResults = [];
        this.currentSearchIndex = 0;
        this.editHistory = [];
        this.editHistoryIndex = -1;
        this.speakerColors = {};
        this.comments = {};
        this.audioPlayer = null;
        this.isPlaying = false;
        
        this.init();
    }
    
    init() {
        this.loadSegments();
        this.initializeSearch();
        this.initializeKeyboardShortcuts();
        this.initializeEditMode();
        this.initializeSpeakerIdentification();
        this.initializeHighlighting();
        this.initializePlaybackSync();
    }
    
    // ============================================
    // Segment Loading
    // ============================================
    
    loadSegments() {
        const segmentElements = document.querySelectorAll('.transcript-segment');
        this.segments = Array.from(segmentElements).map((el, index) => ({
            id: el.dataset.segmentId,
            element: el,
            text: el.querySelector('.segment-text').textContent,
            speaker: el.dataset.speaker || 'Unknown',
            timestamp: el.dataset.timestamp,
            confidence: parseFloat(el.dataset.confidence) || 0,
            index
        }));
        
        this.assignSpeakerColors();
    }
    
    // ============================================
    // Search Functionality (T2.2)
    // ============================================
    
    initializeSearch() {
        const searchInput = document.getElementById('transcript-search');
        const searchBtn = document.getElementById('search-btn');
        const prevBtn = document.getElementById('search-prev');
        const nextBtn = document.getElementById('search-next');
        
        if (!searchInput) return;
        
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.performSearch(searchInput.value);
            });
        }
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.navigateSearch(-1));
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.navigateSearch(1));
        }
    }
    
    performSearch(query) {
        // Clear previous highlights
        this.clearSearchHighlights();
        this.searchResults = [];
        this.currentSearchIndex = 0;
        
        if (!query || query.length < 2) {
            this.updateSearchResults();
            return;
        }
        
        // SECURITY: Escape regex special characters to prevent crashes
        const escapeRegex = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const escapedQuery = escapeRegex(query);
        
        let searchRegex;
        try {
            searchRegex = new RegExp(escapedQuery, 'gi');
        } catch (error) {
            console.error('Invalid search pattern:', error);
            this.showToast('error', 'Invalid Search', 'Please try a different search term');
            return;
        }
        
        this.segments.forEach(segment => {
            const text = segment.text;
            const matches = [...text.matchAll(searchRegex)];
            
            if (matches.length > 0) {
                this.searchResults.push(segment);
                
                // Highlight matches in segment
                const textElement = segment.element.querySelector('.segment-text');
                let highlightedText = text;
                
                // Sort matches by position (descending) to avoid index issues
                matches.sort((a, b) => b.index - a.index);
                
                matches.forEach(match => {
                    const matchText = match[0];
                    const startIndex = match.index;
                    const endIndex = startIndex + matchText.length;
                    
                    highlightedText = 
                        highlightedText.substring(0, startIndex) +
                        `<mark>${matchText}</mark>` +
                        highlightedText.substring(endIndex);
                });
                
                textElement.innerHTML = highlightedText;
                segment.element.classList.add('highlight-match');
            }
        });
        
        this.updateSearchResults();
        
        if (this.searchResults.length > 0) {
            this.scrollToSearchResult(0);
        }
    }
    
    clearSearchHighlights() {
        this.segments.forEach(segment => {
            const textElement = segment.element.querySelector('.segment-text');
            textElement.textContent = segment.text;
            segment.element.classList.remove('highlight-match');
        });
    }
    
    navigateSearch(direction) {
        if (this.searchResults.length === 0) return;
        
        this.currentSearchIndex += direction;
        
        if (this.currentSearchIndex < 0) {
            this.currentSearchIndex = this.searchResults.length - 1;
        } else if (this.currentSearchIndex >= this.searchResults.length) {
            this.currentSearchIndex = 0;
        }
        
        this.scrollToSearchResult(this.currentSearchIndex);
        this.updateSearchResults();
    }
    
    scrollToSearchResult(index) {
        const segment = this.searchResults[index];
        if (segment) {
            segment.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    updateSearchResults() {
        const resultsElement = document.getElementById('search-results');
        if (resultsElement) {
            if (this.searchResults.length > 0) {
                resultsElement.textContent = `${this.currentSearchIndex + 1} of ${this.searchResults.length}`;
            } else {
                resultsElement.textContent = '';
            }
        }
    }
    
    // ============================================
    // Copy Functionality (T2.4)
    // ============================================
    
    copyEntireTranscript() {
        const transcriptText = this.segments
            .map(seg => `[${seg.timestamp}] ${seg.speaker}: ${seg.text}`)
            .join('\n\n');
        
        this.copyToClipboard(transcriptText, 'Entire transcript copied to clipboard');
    }
    
    copySegment(segmentId) {
        const segment = this.segments.find(s => s.id === segmentId);
        if (segment) {
            const text = `[${segment.timestamp}] ${segment.speaker}: ${segment.text}`;
            this.copyToClipboard(text, 'Segment copied to clipboard');
        }
    }
    
    async copyToClipboard(text, successMessage) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('success', 'Copied!', successMessage);
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showToast('success', 'Copied!', successMessage);
            } catch (err) {
                this.showToast('error', 'Copy Failed', 'Please try again');
            }
            
            document.body.removeChild(textArea);
        }
    }
    
    // ============================================
    // Edit Functionality (T2.5)
    // ============================================
    
    initializeEditMode() {
        this.segments.forEach(segment => {
            const textElement = segment.element.querySelector('.segment-text');
            if (textElement && textElement.classList.contains('editable')) {
                textElement.addEventListener('dblclick', () => {
                    this.enterEditMode(segment);
                });
            }
        });
    }
    
    enterEditMode(segment) {
        const textElement = segment.element.querySelector('.segment-text');
        const currentText = segment.text;
        
        // Save to history for undo
        this.saveEditHistory({
            segmentId: segment.id,
            oldText: currentText,
            newText: null
        });
        
        // Create textarea
        const textarea = document.createElement('textarea');
        textarea.className = 'segment-edit-textarea';
        textarea.value = currentText;
        
        // Create action buttons
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'segment-edit-actions';
        
        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn btn-primary btn-sm';
        saveBtn.textContent = 'Save';
        saveBtn.onclick = () => this.saveEdit(segment, textarea.value);
        
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-secondary btn-sm';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.onclick = () => this.cancelEdit(segment);
        
        actionsDiv.appendChild(saveBtn);
        actionsDiv.appendChild(cancelBtn);
        
        // Replace text with edit interface
        textElement.style.display = 'none';
        textElement.parentNode.insertBefore(textarea, textElement.nextSibling);
        textElement.parentNode.insertBefore(actionsDiv, textarea.nextSibling);
        
        segment.element.classList.add('editing');
        textarea.focus();
        
        // ESC to cancel, Ctrl+Enter to save
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.cancelEdit(segment);
            } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                this.saveEdit(segment, textarea.value);
            }
        });
    }
    
    async saveEdit(segment, newText) {
        if (newText === segment.text) {
            this.cancelEdit(segment);
            return;
        }
        
        // Update segment text
        segment.text = newText;
        const textElement = segment.element.querySelector('.segment-text');
        textElement.textContent = newText;
        
        // Update history
        this.editHistory[this.editHistory.length - 1].newText = newText;
        
        // Mark as edited
        segment.element.classList.add('edited');
        segment.element.classList.remove('editing');
        
        // Add edited indicator if not present
        if (!segment.element.querySelector('.edited-indicator')) {
            const indicator = document.createElement('span');
            indicator.className = 'edited-indicator';
            indicator.innerHTML = '<svg width="12" height="12" fill="currentColor" viewBox="0 0 20 20"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg> Edited';
            
            const header = segment.element.querySelector('.segment-header');
            if (header) {
                header.appendChild(indicator);
            }
        }
        
        // Clean up edit interface
        this.cleanupEditInterface(segment);
        
        // Auto-save to backend
        await this.autoSaveEdit(segment.id, newText);
        
        this.showToast('success', 'Saved', 'Changes saved successfully');
    }
    
    cancelEdit(segment) {
        segment.element.classList.remove('editing');
        this.cleanupEditInterface(segment);
        
        // Remove last history entry if canceling
        if (this.editHistory.length > 0 && !this.editHistory[this.editHistory.length - 1].newText) {
            this.editHistory.pop();
        }
    }
    
    cleanupEditInterface(segment) {
        const textarea = segment.element.querySelector('.segment-edit-textarea');
        const actions = segment.element.querySelector('.segment-edit-actions');
        const textElement = segment.element.querySelector('.segment-text');
        
        if (textarea) textarea.remove();
        if (actions) actions.remove();
        if (textElement) textElement.style.display = '';
    }
    
    async autoSaveEdit(segmentId, newText) {
        try {
            const response = await fetch(`/api/meetings/${this.meetingId}/segments/${segmentId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: newText })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save edit');
            }
        } catch (error) {
            console.error('Auto-save failed:', error);
            this.showToast('error', 'Save Failed', 'Changes may not be saved');
        }
    }
    
    saveEditHistory(edit) {
        this.editHistory.push(edit);
        this.editHistoryIndex = this.editHistory.length - 1;
    }
    
    // ============================================
    // Speaker Identification (T2.6)
    // ============================================
    
    initializeSpeakerIdentification() {
        // Extract unique speakers
        const speakers = [...new Set(this.segments.map(s => s.speaker))];
        
        // Render speaker legend
        this.renderSpeakerLegend(speakers);
        
        // Make speaker names clickable for editing
        this.segments.forEach(segment => {
            const speakerElement = segment.element.querySelector('.segment-speaker');
            if (speakerElement) {
                speakerElement.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.editSpeakerName(segment);
                });
            }
        });
    }
    
    assignSpeakerColors() {
        const colors = [
            '#8b5cf6', // purple
            '#ec4899', // pink
            '#06b6d4', // cyan
            '#10b981', // green
            '#f59e0b', // amber
            '#3b82f6', // blue
            '#ef4444', // red
            '#8b5cf6'  // purple (repeat)
        ];
        
        const speakers = [...new Set(this.segments.map(s => s.speaker))];
        speakers.forEach((speaker, index) => {
            this.speakerColors[speaker] = colors[index % colors.length];
        });
        
        // Apply colors to speaker avatars
        this.segments.forEach(segment => {
            const avatar = segment.element.querySelector('.speaker-avatar');
            if (avatar) {
                avatar.style.backgroundColor = this.speakerColors[segment.speaker];
            }
        });
    }
    
    renderSpeakerLegend(speakers) {
        const legendContainer = document.getElementById('speaker-legend');
        if (!legendContainer) return;
        
        legendContainer.innerHTML = '<span class="speaker-legend-label">Speakers:</span>';
        
        speakers.forEach(speaker => {
            const segmentCount = this.segments.filter(s => s.speaker === speaker).length;
            const badge = document.createElement('div');
            badge.className = 'speaker-badge';
            badge.innerHTML = `
                <div class="speaker-color" style="background: ${this.speakerColors[speaker]}"></div>
                <span class="speaker-name">${speaker}</span>
                <span class="speaker-segments-count">(${segmentCount})</span>
            `;
            
            badge.addEventListener('click', () => {
                this.filterBySpeaker(speaker);
            });
            
            legendContainer.appendChild(badge);
        });
    }
    
    editSpeakerName(segment) {
        const speakerNameElement = segment.element.querySelector('.speaker-name-editable');
        if (!speakerNameElement) return;
        
        const currentName = speakerNameElement.textContent;
        const newName = prompt('Enter speaker name:', currentName);
        
        if (newName && newName !== currentName) {
            this.updateSpeakerName(segment.speaker, newName);
        }
    }
    
    async updateSpeakerName(oldName, newName) {
        // Update all segments with this speaker
        this.segments.forEach(segment => {
            if (segment.speaker === oldName) {
                segment.speaker = newName;
                segment.element.dataset.speaker = newName;
                
                const nameElement = segment.element.querySelector('.speaker-name-editable');
                if (nameElement) {
                    nameElement.textContent = newName;
                }
            }
        });
        
        // Update speaker colors
        this.speakerColors[newName] = this.speakerColors[oldName];
        delete this.speakerColors[oldName];
        
        // Re-render legend
        const speakers = [...new Set(this.segments.map(s => s.speaker))];
        this.renderSpeakerLegend(speakers);
        
        // Save to backend
        try {
            await fetch(`/api/meetings/${this.meetingId}/speakers`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ oldName, newName })
            });
            
            this.showToast('success', 'Updated', `Speaker renamed to "${newName}"`);
        } catch (error) {
            console.error('Failed to update speaker name:', error);
            this.showToast('error', 'Update Failed', 'Please try again');
        }
    }
    
    filterBySpeaker(speaker) {
        this.segments.forEach(segment => {
            if (segment.speaker === speaker) {
                segment.element.style.display = '';
            } else {
                segment.element.style.display = 'none';
            }
        });
        
        this.showToast('info', 'Filtered', `Showing only segments from ${speaker}`);
    }
    
    clearSpeakerFilter() {
        this.segments.forEach(segment => {
            segment.element.style.display = '';
        });
    }
    
    // ============================================
    // Highlighting (T2.7)
    // ============================================
    
    initializeHighlighting() {
        this.segments.forEach(segment => {
            segment.element.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.showHighlightMenu(segment, e.clientX, e.clientY);
            });
        });
    }
    
    showHighlightMenu(segment, x, y) {
        // Remove existing menu
        const existingMenu = document.querySelector('.highlight-menu');
        if (existingMenu) existingMenu.remove();
        
        const menu = document.createElement('div');
        menu.className = 'highlight-menu';
        menu.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-lg);
            padding: var(--space-2);
            box-shadow: var(--shadow-lg);
            z-index: 1000;
        `;
        
        const colors = [
            { name: 'Yellow', class: 'highlight-yellow' },
            { name: 'Green', class: 'highlight-green' },
            { name: 'Blue', class: 'highlight-blue' },
            { name: 'Clear', class: '' }
        ];
        
        colors.forEach(color => {
            const button = document.createElement('button');
            button.className = 'toolbar-button';
            button.textContent = color.name;
            button.onclick = () => {
                this.applyHighlight(segment, color.class);
                menu.remove();
            };
            menu.appendChild(button);
        });
        
        document.body.appendChild(menu);
        
        // Close menu on click outside
        setTimeout(() => {
            document.addEventListener('click', () => menu.remove(), { once: true });
        }, 100);
    }
    
    async applyHighlight(segment, highlightClass) {
        // Remove existing highlights
        segment.element.classList.remove('highlight-yellow', 'highlight-green', 'highlight-blue');
        
        if (highlightClass) {
            segment.element.classList.add(highlightClass);
        }
        
        // Persist highlight to backend
        try {
            await fetch(`/api/meetings/${this.meetingId}/segments/${segment.id}/highlight`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ highlightColor: highlightClass || null })
            });
        } catch (error) {
            console.error('Failed to save highlight:', error);
        }
    }
    
    filterByHighlight(highlightClass) {
        this.segments.forEach(segment => {
            if (!highlightClass || segment.element.classList.contains(highlightClass)) {
                segment.element.style.display = '';
            } else {
                segment.element.style.display = 'none';
            }
        });
        
        const filterName = highlightClass ? highlightClass.replace('highlight-', '') : 'all';
        this.showToast('info', 'Filtered', `Showing ${filterName} highlights`);
    }
    
    // ============================================
    // Comment Functionality (T2.8)
    // ============================================
    
    showCommentDialog(segment) {
        // Check if comment dialog already exists
        let dialog = document.getElementById('commentDialog');
        if (!dialog) {
            dialog = this.createCommentDialog();
            document.body.appendChild(dialog);
        }
        
        // Set current segment
        dialog.dataset.segmentId = segment.id;
        
        // Load existing comments for this segment
        this.loadComments(segment.id);
        
        // Show dialog
        dialog.style.display = 'flex';
    }
    
    createCommentDialog() {
        const dialog = document.createElement('div');
        dialog.id = 'commentDialog';
        dialog.className = 'comment-dialog-overlay';
        dialog.style.cssText = 'display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); z-index: 9999; align-items: center; justify-content: center;';
        
        dialog.innerHTML = `
            <div class="comment-dialog-content" style="background: var(--glass-bg); backdrop-filter: var(--backdrop-blur); border: 1px solid var(--glass-border); border-radius: var(--radius-2xl); max-width: 600px; width: 90%; max-height: 80vh; display: flex; flex-direction: column;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-6); border-bottom: 1px solid var(--color-border);">
                    <h3 style="font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                        Comments
                    </h3>
                    <button class="btn-icon" onclick="document.getElementById('commentDialog').style.display='none'">
                        <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <div id="commentList" style="flex: 1; overflow-y: auto; padding: var(--space-6);"></div>
                <div style="padding: var(--space-6); border-top: 1px solid var(--color-border);">
                    <textarea id="commentInput" placeholder="Add a comment..." style="width: 100%; min-height: 80px; padding: var(--space-3); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-primary); font-family: inherit; margin-bottom: var(--space-3);"></textarea>
                    <button class="btn btn-primary" onclick="window.transcriptManager.submitComment()">Post Comment</button>
                </div>
            </div>
        `;
        
        // Close dialog when clicking overlay
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                dialog.style.display = 'none';
            }
        });
        
        return dialog;
    }
    
    async loadComments(segmentId) {
        const commentList = document.getElementById('commentList');
        commentList.innerHTML = '<p style="text-align: center; color: var(--color-text-tertiary);">Loading comments...</p>';
        
        try {
            const response = await fetch(`/api/meetings/${this.meetingId}/segments/${segmentId}/comments`);
            const data = await response.json();
            
            if (data.success && data.comments) {
                this.renderComments(data.comments);
            } else {
                commentList.innerHTML = '<p style="text-align: center; color: var(--color-text-tertiary);">No comments yet. Be the first to comment!</p>';
            }
        } catch (error) {
            console.error('Failed to load comments:', error);
            commentList.innerHTML = '<p style="text-align: center; color: var(--color-text-secondary);">Failed to load comments</p>';
        }
    }
    
    renderComments(comments) {
        const commentList = document.getElementById('commentList');
        
        if (comments.length === 0) {
            commentList.innerHTML = '<p style="text-align: center; color: var(--color-text-tertiary);">No comments yet. Be the first to comment!</p>';
            return;
        }
        
        commentList.innerHTML = comments.map(comment => `
            <div class="comment-item" style="padding: var(--space-4); background: var(--color-surface); border-radius: var(--radius-lg); margin-bottom: var(--space-3);">
                <div style="display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-2);">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--gradient-primary); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: var(--font-size-sm);">
                        ${comment.author_name ? comment.author_name[0].toUpperCase() : 'U'}
                    </div>
                    <div>
                        <div style="font-weight: var(--font-weight-semibold); color: var(--color-text-primary);">${comment.author_name || 'User'}</div>
                        <div style="font-size: var(--font-size-xs); color: var(--color-text-tertiary);">${this.formatTimestamp(comment.created_at)}</div>
                    </div>
                </div>
                <p style="color: var(--color-text-primary); line-height: var(--line-height-relaxed);">${comment.text}</p>
            </div>
        `).join('');
    }
    
    async submitComment() {
        const dialog = document.getElementById('commentDialog');
        const input = document.getElementById('commentInput');
        const segmentId = dialog.dataset.segmentId;
        const text = input.value.trim();
        
        if (!text) {
            this.showToast('error', 'Error', 'Comment cannot be empty');
            return;
        }
        
        try {
            const response = await fetch(`/api/meetings/${this.meetingId}/segments/${segmentId}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text })
            });
            
            const data = await response.json();
            
            if (data.success) {
                input.value = '';
                this.loadComments(segmentId);
                this.showToast('success', 'Posted', 'Comment added successfully');
                
                // Update comment count on segment
                const segment = this.segments.find(s => s.id == segmentId);
                if (segment) {
                    this.updateSegmentCommentIndicator(segment);
                }
            } else {
                this.showToast('error', 'Error', data.message || 'Failed to post comment');
            }
        } catch (error) {
            console.error('Failed to post comment:', error);
            this.showToast('error', 'Error', 'Failed to post comment');
        }
    }
    
    updateSegmentCommentIndicator(segment) {
        // Add comment indicator icon to segment if not present
        const existingIndicator = segment.element.querySelector('.comment-indicator');
        if (!existingIndicator) {
            const indicator = document.createElement('button');
            indicator.className = 'segment-action-btn comment-indicator';
            indicator.title = 'View comments';
            indicator.innerHTML = `
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"/>
                </svg>
            `;
            indicator.onclick = () => this.showCommentDialog(segment);
            
            const actions = segment.element.querySelector('.segment-actions');
            if (actions) {
                actions.appendChild(indicator);
            }
        }
    }
    
    formatTimestamp(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMinutes = Math.floor((now - date) / 60000);
        
        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
        return date.toLocaleDateString();
    }
    
    // ============================================
    // Playback Sync (T2.9)
    // ============================================
    
    initializePlaybackSync() {
        // Initialize audio player if present
        this.audioPlayer = document.getElementById('meetingAudioPlayer');
        
        if (this.audioPlayer) {
            // Listen for timeupdate events
            this.audioPlayer.addEventListener('timeupdate', () => {
                this.syncTranscriptToPlayback();
            });
            
            // Click segment to jump to timestamp
            this.segments.forEach(segment => {
                segment.element.addEventListener('click', (e) => {
                    // Don't trigger if clicking action buttons
                    if (!e.target.closest('.segment-actions')) {
                        this.jumpToTimestamp(segment);
                    }
                });
            });
        }
    }
    
    syncTranscriptToPlayback() {
        if (!this.audioPlayer) return;
        
        const currentTime = this.audioPlayer.currentTime * 1000; // Convert to ms
        
        // Find the current segment
        for (const segment of this.segments) {
            const startMs = segment.element.dataset.startMs || 0;
            const endMs = segment.element.dataset.endMs || 0;
            
            if (currentTime >= startMs && currentTime <= endMs) {
                // Highlight current segment
                this.segments.forEach(s => s.element.classList.remove('current-playing'));
                segment.element.classList.add('current-playing');
                
                // Auto-scroll to keep current segment visible
                segment.element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                break;
            }
        }
    }
    
    jumpToTimestamp(segment) {
        if (!this.audioPlayer) return;
        
        const startMs = parseFloat(segment.element.dataset.startMs) || 0;
        this.audioPlayer.currentTime = startMs / 1000; // Convert to seconds
        this.audioPlayer.play();
        this.isPlaying = true;
    }
    
    togglePlayback() {
        if (!this.audioPlayer) return;
        
        if (this.isPlaying) {
            this.audioPlayer.pause();
            this.isPlaying = false;
        } else {
            this.audioPlayer.play();
            this.isPlaying = true;
        }
    }
    
    // ============================================
    // Keyboard Shortcuts (T2.10)
    // ============================================
    
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            const activeElement = document.activeElement;
            const isTyping = activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA';
            
            // Cmd/Ctrl + F: Search
            if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.getElementById('transcript-search');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
            
            // Cmd/Ctrl + C: Copy entire transcript (if nothing selected)
            if ((e.metaKey || e.ctrlKey) && e.key === 'c' && !window.getSelection().toString()) {
                if (!isTyping) {
                    e.preventDefault();
                    this.copyEntireTranscript();
                }
            }
            
            // Space: Play/Pause (if not typing)
            if (e.key === ' ' && !isTyping) {
                e.preventDefault();
                this.togglePlayback();
            }
            
            // Arrow Keys: Navigate segments (if not typing)
            if (!isTyping) {
                if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
                    e.preventDefault();
                    this.navigateSegment(1);
                } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
                    e.preventDefault();
                    this.navigateSegment(-1);
                }
            }
            
            // N: Next search result
            if (e.key === 'n' && !isTyping) {
                e.preventDefault();
                this.navigateSearch(1);
            }
            
            // P: Previous search result
            if (e.key === 'p' && !isTyping) {
                e.preventDefault();
                this.navigateSearch(-1);
            }
            
            // H: Toggle highlight menu
            if (e.key === 'h' && !isTyping) {
                e.preventDefault();
                // Show highlight filter options
                this.showHighlightFilterMenu();
            }
            
            // Cmd/Ctrl + Z: Undo edit
            if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
                // TODO: Implement undo
            }
            
            // Cmd/Ctrl + Shift + Z: Redo edit
            if ((e.metaKey || e.ctrlKey) && e.key === 'z' && e.shiftKey) {
                // TODO: Implement redo
            }
            
            // ? : Show keyboard shortcuts
            if (e.key === '?' && !e.metaKey && !e.ctrlKey) {
                if (!isTyping) {
                    e.preventDefault();
                    this.showKeyboardShortcuts();
                }
            }
            
            // ESC: Close modals
            if (e.key === 'Escape') {
                const panel = document.querySelector('.shortcuts-panel');
                if (panel) panel.remove();
                
                const exportModal = document.getElementById('exportModal');
                if (exportModal) exportModal.style.display = 'none';
                
                const commentDialog = document.getElementById('commentDialog');
                if (commentDialog) commentDialog.style.display = 'none';
            }
        });
    }
    
    navigateSegment(direction) {
        const visibleSegments = this.segments.filter(s => s.element.style.display !== 'none');
        const currentIndex = visibleSegments.findIndex(s => s.element.classList.contains('focused'));
        
        // Remove current focus
        visibleSegments.forEach(s => s.element.classList.remove('focused'));
        
        // Calculate new index
        let newIndex = currentIndex + direction;
        if (newIndex < 0) newIndex = visibleSegments.length - 1;
        if (newIndex >= visibleSegments.length) newIndex = 0;
        
        // Add new focus and scroll into view
        visibleSegments[newIndex].element.classList.add('focused');
        visibleSegments[newIndex].element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    showHighlightFilterMenu() {
        // Show highlight filter quick menu
        this.showToast('info', 'Highlight Filters', 'Right-click on any segment to highlight or use toolbar');
    }
    
    showKeyboardShortcuts() {
        const panel = document.createElement('div');
        panel.className = 'shortcuts-panel';
        panel.innerHTML = `
            <div class="shortcuts-header">
                <h3 class="shortcuts-title">Keyboard Shortcuts</h3>
                <button class="btn-icon" onclick="this.parentElement.parentElement.remove()">
                    <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="shortcuts-list">
                <div class="shortcut-item">
                    <span class="shortcut-description">Search transcript</span>
                    <div class="shortcut-keys">
                        <kbd class="shortcut-key">Ctrl</kbd>
                        <kbd class="shortcut-key">F</kbd>
                    </div>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-description">Copy entire transcript</span>
                    <div class="shortcut-keys">
                        <kbd class="shortcut-key">Ctrl</kbd>
                        <kbd class="shortcut-key">C</kbd>
                    </div>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-description">Show this panel</span>
                    <div class="shortcut-keys">
                        <kbd class="shortcut-key">?</kbd>
                    </div>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-description">Close panels</span>
                    <div class="shortcut-keys">
                        <kbd class="shortcut-key">ESC</kbd>
                    </div>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-description">Save edit</span>
                    <div class="shortcut-keys">
                        <kbd class="shortcut-key">Ctrl</kbd>
                        <kbd class="shortcut-key">Enter</kbd>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
    }
    
    // ============================================
    // Toast Notifications
    // ============================================
    
    showToast(type, title, message) {
        const container = this.getToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
            error: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
            info: '<svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">${icons[type]}</div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    getToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }
}

// Initialize transcript manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const meetingId = document.body.dataset.meetingId;
    if (meetingId && document.querySelector('.transcript-content')) {
        window.transcriptManager = new TranscriptManager(meetingId);
    }
});
