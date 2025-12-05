/**
 * Terminal UI Controller
 * Handles terminal display, input, and animations
 */

class Terminal {
    constructor() {
        this.outputElement = document.getElementById('terminal-output');
        this.inputElement = document.getElementById('terminal-input');
        this.inputContainer = document.getElementById('terminal-input-container');
        this.imageDisplay = document.getElementById('image-display');
        this.locationImage = document.getElementById('location-image');
        
        this.inputHistory = [];
        this.historyIndex = -1;
        this.isTyping = false;
        this.typingSpeed = 30; // ms per character
        
        this.init();
    }

    init() {
        // Focus input on load
        this.inputElement.focus();

        // Handle input submission
        this.inputElement.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !this.isTyping) {
                this.handleCommand();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateHistory(-1);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.navigateHistory(1);
            }
        });

        // Keep focus on input
        document.addEventListener('click', () => {
            if (!window.getSelection().toString()) {
                this.inputElement.focus();
            }
        });

        // Display welcome message
        this.displayWelcome();
    }

    displayWelcome() {
        const welcome = `
╔═══════════════════════════════════════════════════════════════╗
║                      NATURE42 SYSTEM v1.0                     ║
║                   A Text Adventure Experience                 ║
╚═══════════════════════════════════════════════════════════════╝

Initializing game world...
Loading AI systems...
Ready.

Type your commands below to begin your adventure.
Try: "look around" or "help"

`;
        this.print(welcome, 'system');
    }

    handleCommand() {
        const command = this.inputElement.value.trim();
        
        if (!command) {
            return;
        }

        // Add to history
        this.inputHistory.push(command);
        this.historyIndex = this.inputHistory.length;

        // Echo command
        this.print(`> ${command}`, 'normal');

        // Clear input
        this.inputElement.value = '';

        // Emit command event for game client to handle
        const event = new CustomEvent('terminalCommand', { detail: { command } });
        document.dispatchEvent(event);
    }

    navigateHistory(direction) {
        if (this.inputHistory.length === 0) {
            return;
        }

        this.historyIndex += direction;

        if (this.historyIndex < 0) {
            this.historyIndex = 0;
        } else if (this.historyIndex >= this.inputHistory.length) {
            this.historyIndex = this.inputHistory.length;
            this.inputElement.value = '';
            return;
        }

        this.inputElement.value = this.inputHistory[this.historyIndex];
    }

    /**
     * Print text to terminal output
     * @param {string} text - Text to display
     * @param {string} style - Style class: 'normal', 'system', 'error', 'success'
     * @param {boolean} animate - Whether to animate typing
     */
    print(text, style = 'normal', animate = false) {
        if (animate && !this.isAccessibilityMode()) {
            this.printWithTyping(text, style);
        } else {
            this.printInstant(text, style);
        }
    }

    printInstant(text, style) {
        const line = document.createElement('div');
        line.className = `output-line ${style}`;
        line.textContent = text;
        this.outputElement.appendChild(line);
        this.scrollToBottom();
    }

    async printWithTyping(text, style) {
        this.isTyping = true;
        this.disableInput();

        const line = document.createElement('div');
        line.className = `output-line ${style} typing`;
        this.outputElement.appendChild(line);

        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        line.appendChild(cursor);

        for (let i = 0; i < text.length; i++) {
            const textNode = document.createTextNode(text[i]);
            line.insertBefore(textNode, cursor);
            this.scrollToBottom();
            await this.sleep(this.typingSpeed);
        }

        cursor.remove();
        line.classList.remove('typing');
        this.isTyping = false;
        this.enableInput();
    }

    /**
     * Print text incrementally (for streaming responses)
     * @param {string} text - Text chunk to append
     * @param {string} style - Style class
     * @param {boolean} newLine - Whether to start a new line
     */
    printStreaming(text, style = 'normal', newLine = false) {
        let line;
        
        if (newLine || !this.currentStreamLine) {
            line = document.createElement('div');
            line.className = `output-line ${style}`;
            this.outputElement.appendChild(line);
            this.currentStreamLine = line;
        } else {
            line = this.currentStreamLine;
        }

        line.textContent += text;
        this.scrollToBottom();
    }

    /**
     * End streaming and prepare for next output
     */
    endStreaming() {
        this.currentStreamLine = null;
    }

    /**
     * Clear the terminal output
     */
    clear() {
        this.outputElement.innerHTML = '';
        this.currentStreamLine = null;
    }

    /**
     * Display an image with loading and error handling
     * TODO: Implement for Task 10.2
     * @param {string} url - Image URL
     * @param {string} alt - Alt text
     */
    showImage(url, alt = 'Location visualization') {
        // TODO: Implement image display (Task 10.2)
        console.log('Image display not yet implemented');
    }

    /**
     * Hide the image display
     * TODO: Implement for Task 10.2
     */
    hideImage() {
        // TODO: Implement image hiding (Task 10.2)
    }

    /**
     * Show loading indicator
     */
    showLoading(message = 'Processing') {
        const line = document.createElement('div');
        line.className = 'output-line system';
        line.innerHTML = `${message}<span class="loading-indicator"></span>`;
        line.id = 'loading-indicator';
        this.outputElement.appendChild(line);
        this.scrollToBottom();
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loader = document.getElementById('loading-indicator');
        if (loader) {
            loader.remove();
        }
    }

    /**
     * Display error message
     * @param {string} message - Error message
     */
    showError(message) {
        this.print(`ERROR: ${message}`, 'error');
    }

    /**
     * Display success message
     * @param {string} message - Success message
     */
    showSuccess(message) {
        this.print(message, 'success');
    }

    /**
     * Disable input
     */
    disableInput() {
        this.inputElement.disabled = true;
        this.inputElement.style.opacity = '0.5';
    }

    /**
     * Enable input
     */
    enableInput() {
        this.inputElement.disabled = false;
        this.inputElement.style.opacity = '1';
        this.inputElement.focus();
    }

    /**
     * Scroll to bottom of output
     */
    scrollToBottom() {
        this.outputElement.scrollTop = this.outputElement.scrollHeight;
    }

    /**
     * Check if accessibility mode is enabled
     */
    isAccessibilityMode() {
        return document.body.classList.contains('accessibility-mode');
    }

    /**
     * Sleep utility for animations
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Get input history
     */
    getHistory() {
        return [...this.inputHistory];
    }

    /**
     * Set typing speed
     * @param {number} speed - Speed in ms per character
     */
    setTypingSpeed(speed) {
        this.typingSpeed = speed;
    }
}

// Initialize terminal when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.terminal = new Terminal();
    });
} else {
    window.terminal = new Terminal();
}
