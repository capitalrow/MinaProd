// Crown+ Theme Toggle System

class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('mina-theme') || 'dark';
        this.init();
    }

    init() {
        // Apply saved theme on load
        this.applyTheme(this.theme);
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('mina-theme')) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.theme = theme;
        
        // Update any theme toggle buttons
        this.updateToggleButtons();
        
        // Dispatch custom event for theme change
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
    }

    setTheme(theme) {
        this.applyTheme(theme);
        localStorage.setItem('mina-theme', theme);
    }

    toggleTheme() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        return newTheme;
    }

    updateToggleButtons() {
        const buttons = document.querySelectorAll('[data-theme-toggle]');
        buttons.forEach(button => {
            const isDark = this.theme === 'dark';
            const icon = button.querySelector('svg, .icon');
            
            if (icon) {
                // Update icon if needed
                if (isDark) {
                    button.setAttribute('aria-label', 'Switch to light mode');
                    button.title = 'Switch to light mode';
                } else {
                    button.setAttribute('aria-label', 'Switch to dark mode');
                    button.title = 'Switch to dark mode';
                }
            }
        });
    }

    getTheme() {
        return this.theme;
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();

// Add global helper functions
window.toggleTheme = () => themeManager.toggleTheme();
window.setTheme = (theme) => themeManager.setTheme(theme);
window.getTheme = () => themeManager.getTheme();

// Auto-attach click handlers to theme toggle buttons
document.addEventListener('DOMContentLoaded', () => {
    const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            themeManager.toggleTheme();
        });
    });
});
