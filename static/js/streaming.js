/**
 * Streaming Response Handler
 * Handles server-sent events and streaming responses from the backend
 */

class StreamingHandler {
    constructor(terminal) {
        this.terminal = terminal;
        this.currentStream = null;
        this.abortController = null;
    }

    /**
     * Send command and handle streaming response
     * @param {string} command - User command
     * @param {object} gameState - Current game state
     * @returns {Promise<object>} - Response result
     */
    async sendCommand(command, gameState) {
        // Cancel any existing stream
        this.cancelStream();

        // Create new abort controller for this request
        this.abortController = new AbortController();

        try {
            this.terminal.showLoading('Generating response');

            const response = await fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    game_state: gameState
                }),
                signal: this.abortController.signal
            });

            this.terminal.hideLoading();

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Check if response is streaming
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/event-stream')) {
                return await this.handleStreamingResponse(response);
            } else {
                // Fallback to regular JSON response
                return await response.json();
            }

        } catch (error) {
            this.terminal.hideLoading();
            
            if (error.name === 'AbortError') {
                this.handleStreamError(error);
                return { error: 'cancelled' };
            }
            
            // Try to parse error response from server
            let errorData = null;
            if (error.response) {
                try {
                    errorData = await error.response.json();
                } catch (e) {
                    // Couldn't parse error response
                }
            }
            
            this.handleStreamError(error, errorData);
            console.error('Command error:', error);
            return { error: error.message };
        }
    }

    /**
     * Handle streaming response using Fetch Streaming API
     * @param {Response} response - Fetch response object
     * @returns {Promise<object>} - Final result
     */
    async handleStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let result = null;

        try {
            // Show visual feedback that streaming is in progress
            this.terminal.printStreaming('', 'normal', true);

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    break;
                }

                // Decode chunk
                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = this.parseSSEData(line.slice(6));
                        
                        if (data) {
                            if (data.type === 'text' && data.content) {
                                // Display text chunk incrementally
                                this.terminal.printStreaming(data.content);
                            } else if (data.type === 'tool' && data.tool_name) {
                                // Show tool usage
                                this.terminal.printStreaming(`\n[Using tool: ${data.tool_name}]\n`, 'system', true);
                            } else if (data.type === 'state_changes' && data.changes) {
                                // Store state changes
                                if (!result) result = {};
                                result.game_state = data.changes;
                            } else if (data.type === 'done') {
                                // Stream complete
                                if (!result) result = {};
                                result.success = data.success;
                            } else if (data.type === 'error' && data.message) {
                                // Error occurred
                                throw new Error(data.message);
                            }
                            // Legacy format support
                            else if (data.text) {
                                this.terminal.printStreaming(data.text);
                            } else if (data.tool) {
                                this.terminal.printStreaming(`\n[Using tool: ${data.tool}]\n`, 'system', true);
                            } else if (data.done) {
                                if (!result) result = {};
                                result = { ...result, ...(data.result || {}) };
                            } else if (data.error) {
                                throw new Error(data.error);
                            }
                        }
                    }
                }
            }

            this.terminal.endStreaming();
            return result || {};

        } catch (error) {
            this.terminal.endStreaming();
            
            // Try to extract error data if it's a structured error
            let errorData = null;
            if (error.message) {
                try {
                    errorData = JSON.parse(error.message);
                } catch (e) {
                    // Not JSON, use as-is
                }
            }
            
            this.handleStreamError(error, errorData);
            throw error;
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * Parse SSE data field
     * @param {string} data - Data string
     * @returns {object|null} - Parsed data or null
     */
    parseSSEData(data) {
        try {
            return JSON.parse(data);
        } catch (error) {
            console.warn('Failed to parse SSE data:', data);
            return null;
        }
    }

    /**
     * Cancel current stream
     */
    cancelStream() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        this.terminal.hideLoading();
        this.terminal.endStreaming();
    }

    /**
     * Handle stream errors gracefully with user-friendly messages
     * Implements Requirement 18.4: Graceful error handling for streams
     * @param {Error} error - Error object
     * @param {object} errorData - Optional error data from server
     */
    handleStreamError(error, errorData = null) {
        console.error('Stream error:', error);
        
        let message = '';
        let suggestions = [];
        
        // Check if we have structured error data from server
        if (errorData && errorData.message) {
            message = errorData.message;
            suggestions = errorData.suggestions || [];
        }
        // Handle specific error types
        else if (error.name === 'AbortError') {
            message = 'The connection was interrupted.';
            suggestions = [
                'Try your command again',
                'Check your internet connection'
            ];
        } else if (error.message.includes('network') || error.message.includes('Failed to fetch')) {
            message = "There's a problem connecting to the game server.";
            suggestions = [
                'Check your internet connection',
                'Try refreshing the page',
                'Wait a moment and try again'
            ];
        } else if (error.message.includes('timeout')) {
            message = 'The AI is taking longer than expected to respond.';
            suggestions = [
                'Try your command again',
                'Try a simpler command',
                'The service may be slow right now'
            ];
        } else if (error.message.includes('AI service') || error.message.includes('unavailable')) {
            message = 'The AI service is temporarily unavailable.';
            suggestions = [
                'Check your internet connection',
                'Wait a moment and try again',
                'Refresh the page if the problem persists'
            ];
        } else {
            message = error.message || 'An unexpected error occurred.';
            suggestions = [
                'Try your action again',
                'Refresh the page if problems continue'
            ];
        }
        
        // Display error message
        this.terminal.showError(message);
        
        // Display suggestions if available
        if (suggestions.length > 0) {
            this.terminal.print('\nSuggestions:', 'system');
            suggestions.forEach(suggestion => {
                this.terminal.print(`  • ${suggestion}`, 'system');
            });
        }
        
        // Add recovery action if available
        if (errorData && errorData.recovery_action) {
            this.terminal.print('', 'normal'); // Blank line
            this.terminal.print(this.getRecoveryInstructions(errorData.recovery_action), 'system');
        }
    }
    
    /**
     * Get recovery instructions for a specific action
     * @param {string} recoveryAction - Recovery action identifier
     * @returns {string} - Instructions
     */
    getRecoveryInstructions(recoveryAction) {
        const instructions = {
            'start_new_game': "Type 'new game' to start fresh.",
            'refresh_or_new_game': "Try refreshing the page first. If that doesn't work, start a new game.",
            'refresh_page': 'Refresh your browser page to reload the game.',
            'check_connection': 'Check your internet connection and try again.',
            'wait_and_retry': 'Wait a moment for the service to recover, then try again.'
        };
        
        return instructions[recoveryAction] || 'Try again or refresh the page if the problem persists.';
    }

    /**
     * Check if currently streaming
     * @returns {boolean}
     */
    isStreaming() {
        return this.abortController !== null;
    }
}

// Export for use in game client
window.StreamingHandler = StreamingHandler;
