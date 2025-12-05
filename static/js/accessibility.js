/**
 * Accessibility Mode Manager
 * Handles toggling of visual effects for accessibility
 */

class AccessibilityManager {
    constructor() {
        this.checkbox = document.getElementById('accessibility-mode');
        this.storageKey = 'nature42_accessibility_mode';
        this.init();
    }

    init() {
        // Load saved preference
        const savedMode = localStorage.getItem(this.storageKey);
        if (savedMode === 'true') {
            this.enableAccessibilityMode();
            this.checkbox.checked = true;
        }

        // Listen for changes
        this.checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.enableAccessibilityMode();
            } else {
                this.disableAccessibilityMode();
            }
        });
    }

    enableAccessibilityMode() {
        document.body.classList.add('accessibility-mode');
        localStorage.setItem(this.storageKey, 'true');
        console.log('Accessibility mode enabled');
    }

    disableAccessibilityMode() {
        document.body.classList.remove('accessibility-mode');
        localStorage.setItem(this.storageKey, 'false');
        console.log('Accessibility mode disabled');
    }

    isEnabled() {
        return document.body.classList.contains('accessibility-mode');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.accessibilityManager = new AccessibilityManager();
    });
} else {
    window.accessibilityManager = new AccessibilityManager();
}
