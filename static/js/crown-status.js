/**
 * MINA CROWN+ STATUS INDICATORS
 * Connection status, recording indicator, session warnings, theme toggle
 * - Real-time connection monitoring
 * - Recording status with pulsing indicator
 * - Session warnings and alerts
 * - Dark/light/high-contrast theme toggle
 */

class CrownStatus {
    constructor() {
        this.connectionStatus = 'online';
        this.isRecording = false;
        this.currentTheme = this.detectTheme();
        this.init();
    }

    init() {
        this.createStatusBar();
        this.initConnectionMonitor();
        this.initThemeToggle();
        this.addStyles();
        console.log('✨ Crown+ Status Indicators initialized');
    }

    detectTheme() {
        return localStorage.getItem('crown-theme') || 'dark';
    }

    createStatusBar() {
        if (document.getElementById('crown-status-bar')) return;

        const statusBar = document.createElement('div');
        statusBar.id = 'crown-status-bar';
        statusBar.className = 'crown-status-bar';
        statusBar.innerHTML = `
            <div class="crown-status-indicators">
                <div id="crown-connection-status" class="crown-status-item" style="display: none;">
                    <div class="status-dot"></div>
                    <span class="status-text">Reconnecting...</span>
                </div>
                <div id="crown-recording-status" class="crown-status-item crown-recording-indicator" style="display: none;">
                    <div class="recording-dot"></div>
                    <span class="status-text">Recording</span>
                </div>
            </div>
        `;

        document.body.insertBefore(statusBar, document.body.firstChild);
    }

    initConnectionMonitor() {
        window.addEventListener('online', () => this.setConnectionStatus('online'));
        window.addEventListener('offline', () => this.setConnectionStatus('offline'));

        setInterval(() => {
            if (navigator.onLine) {
                this.setConnectionStatus('online');
            } else {
                this.setConnectionStatus('offline');
            }
        }, 5000);
    }

    setConnectionStatus(status) {
        this.connectionStatus = status;
        const statusElement = document.getElementById('crown-connection-status');
        
        if (status === 'offline' || status === 'reconnecting') {
            statusElement.style.display = 'flex';
            statusElement.className = `crown-status-item crown-status-${status}`;
            statusElement.querySelector('.status-text').textContent = 
                status === 'offline' ? 'Offline' : 'Reconnecting...';
        } else {
            statusElement.style.display = 'none';
        }
    }

    showRecordingStatus(isRecording = true) {
        this.isRecording = isRecording;
        const recordingElement = document.getElementById('crown-recording-status');
        recordingElement.style.display = isRecording ? 'flex' : 'none';
    }

    showWarning(message, duration = 5000) {
        if (window.CrownUI && window.CrownUI.toast) {
            window.CrownUI.toast.warning(message, 'Warning');
        } else {
            console.warn(message);
        }
    }

    showError(message, duration = 8000) {
        if (window.CrownUI && window.CrownUI.toast) {
            window.CrownUI.toast.error(message, 'Error');
        } else {
            console.error(message);
        }
    }

    showSuccess(message, duration = 5000) {
        if (window.CrownUI && window.CrownUI.toast) {
            window.CrownUI.toast.success(message, 'Success');
        } else {
            console.log(message);
        }
    }

    initThemeToggle() {
        this.applyTheme(this.currentTheme);

        const themeToggle = document.createElement('button');
        themeToggle.id = 'crown-theme-toggle';
        themeToggle.className = 'crown-theme-toggle';
        themeToggle.setAttribute('aria-label', 'Toggle theme');
        themeToggle.innerHTML = this.getThemeIcon(this.currentTheme);

        themeToggle.addEventListener('click', () => {
            this.cycleTheme();
        });

        const navbar = document.querySelector('.crown-navbar-container');
        if (navbar) {
            const actions = navbar.querySelector('.navbar-actions') || navbar;
            actions.insertBefore(themeToggle, actions.firstChild);
        }
    }

    cycleTheme() {
        const themes = ['dark', 'light', 'high-contrast'];
        const currentIndex = themes.indexOf(this.currentTheme);
        this.currentTheme = themes[(currentIndex + 1) % themes.length];
        this.applyTheme(this.currentTheme);
        
        const toggle = document.getElementById('crown-theme-toggle');
        if (toggle) {
            toggle.innerHTML = this.getThemeIcon(this.currentTheme);
        }
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-crown-theme', theme);
        localStorage.setItem('crown-theme', theme);
        this.currentTheme = theme;
    }

    getThemeIcon(theme) {
        const icons = {
            'dark': '<i class="fas fa-moon"></i>',
            'light': '<i class="fas fa-sun"></i>',
            'high-contrast': '<i class="fas fa-adjust"></i>'
        };
        return icons[theme] || icons.dark;
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .crown-status-bar {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 9998;
                pointer-events: none;
            }

            .crown-status-indicators {
                display: flex;
                gap: var(--space-2);
                padding: var(--space-2);
                justify-content: center;
            }

            .crown-status-item {
                display: flex;
                align-items: center;
                gap: var(--space-2);
                padding: var(--space-2) var(--space-4);
                background: var(--surface-primary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-full);
                font-size: var(--font-size-sm);
                font-weight: var(--font-weight-medium);
                box-shadow: var(--shadow-lg);
                pointer-events: all;
            }

            .crown-status-offline {
                background: rgba(239, 68, 68, 0.1);
                border-color: var(--color-error-500);
                color: var(--color-error-500);
            }

            .crown-status-reconnecting {
                background: rgba(245, 158, 11, 0.1);
                border-color: var(--color-warning-500);
                color: var(--color-warning-500);
            }

            .crown-recording-indicator {
                background: rgba(239, 68, 68, 0.1);
                border-color: var(--color-error-500);
                color: var(--color-error-500);
            }

            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: currentColor;
            }

            .recording-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: var(--color-error-500);
                box-shadow: 0 0 12px var(--color-error-500);
            }

            @media (prefers-reduced-motion: no-preference) {
                .recording-dot {
                    animation: pulse-recording 1.5s ease-in-out infinite;
                }

                @keyframes pulse-recording {
                    0%, 100% {
                        opacity: 1;
                        transform: scale(1);
                    }
                    50% {
                        opacity: 0.6;
                        transform: scale(0.9);
                    }
                }
            }

            .crown-theme-toggle {
                background: var(--surface-secondary);
                border: 1px solid var(--border-primary);
                color: var(--text-primary);
                width: 40px;
                height: 40px;
                border-radius: var(--radius-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-right: var(--space-2);
            }

            .crown-theme-toggle:hover {
                background: var(--surface-elevated);
                border-color: var(--color-brand-500);
            }

            .crown-theme-toggle:focus {
                outline: 2px solid var(--color-brand-500);
                outline-offset: 2px;
            }

            [data-crown-theme="light"] {
                --bg-primary: #ffffff;
                --bg-secondary: #f8fafc;
                --bg-tertiary: #f1f5f9;
                --surface-primary: #ffffff;
                --surface-secondary: #f8fafc;
                --surface-elevated: #f1f5f9;
                --text-primary: #0f172a;
                --text-secondary: #475569;
                --text-tertiary: #94a3b8;
                --border-primary: #e2e8f0;
                --border-secondary: #cbd5e1;
            }

            [data-crown-theme="high-contrast"] {
                --bg-primary: #000000;
                --text-primary: #ffffff;
                --border-primary: #ffffff;
                --color-brand-500: #00ff00;
            }
        `;
        document.head.appendChild(style);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.CrownStatus = new CrownStatus();
    });
} else {
    window.CrownStatus = new CrownStatus();
}
