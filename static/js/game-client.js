/**
 * Game Client
 * Main game logic coordinator - handles state management, command processing, and UI coordination
 */

class GameClient {
    constructor() {
        this.terminal = null;
        this.streamingHandler = null;
        this.storageManager = null;
        this.gameState = null;
        this.isInitialized = false;
    }

    /**
     * Initialize the game client
     */
    async init() {
        // Wait for dependencies to be ready
        await this.waitForDependencies();

        this.terminal = window.terminal;
        this.storageManager = window.storageManager;
        this.streamingHandler = new StreamingHandler(this.terminal);

        // Initialize storage
        try {
            await this.storageManager.init();
        } catch (error) {
            console.error('Failed to initialize storage:', error);
            this.terminal.showError('Failed to initialize game storage. Some features may not work.');
        }

        // Set up modal
        await this.setupModal();

        // Listen for terminal commands
        document.addEventListener('terminalCommand', (e) => {
            this.handleCommand(e.detail.command);
        });

        // Set up auto-save on page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.gameState) {
                this.saveGame();
            }
        });

        // Set up auto-save before page unload
        window.addEventListener('beforeunload', () => {
            if (this.gameState) {
                // Synchronous save attempt
                this.saveGame();
            }
        });

        this.isInitialized = true;
        console.log('Game client initialized');
    }

    /**
     * Set up the welcome modal
     */
    async setupModal() {
        const modal = document.getElementById('welcome-modal');
        const newGameBtn = document.getElementById('new-game-btn');
        const continueGameBtn = document.getElementById('continue-game-btn');

        // Check if there's a saved game
        const hasSaved = await this.storageManager.hasSavedGame();
        
        if (hasSaved) {
            continueGameBtn.style.display = 'block';
        }

        // Handle new game button
        newGameBtn.addEventListener('click', async () => {
            modal.classList.add('hidden');
            await this.initializeNewGame();
        });

        // Handle continue game button
        continueGameBtn.addEventListener('click', async () => {
            modal.classList.add('hidden');
            await this.continueGame();
        });
    }

    /**
     * Wait for dependencies to load
     */
    async waitForDependencies() {
        const maxWait = 5000; // 5 seconds
        const startTime = Date.now();

        while (!window.terminal || !window.storageManager || !window.StreamingHandler) {
            if (Date.now() - startTime > maxWait) {
                throw new Error('Timeout waiting for dependencies');
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }

    /**
     * Update inventory display
     */
    updateInventoryDisplay() {
        if (!this.gameState) return;

        const inventoryItems = document.getElementById('inventory-items');
        const inventoryEmpty = document.querySelector('.inventory-empty');
        const keysCount = document.getElementById('keys-count');

        // Update keys count
        keysCount.textContent = `${this.gameState.keys_collected.length}/6`;

        // Update inventory items
        if (this.gameState.inventory && this.gameState.inventory.length > 0) {
            inventoryEmpty.style.display = 'none';
            inventoryItems.innerHTML = '';

            this.gameState.inventory.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'inventory-item';
                if (item.is_key) {
                    itemDiv.classList.add('is-key');
                }

                const itemName = document.createElement('span');
                itemName.className = 'item-name';
                itemName.textContent = item.name;

                const itemDesc = document.createElement('div');
                itemDesc.className = 'item-description';
                itemDesc.textContent = item.description;

                itemDiv.appendChild(itemName);
                itemDiv.appendChild(itemDesc);
                inventoryItems.appendChild(itemDiv);
            });
        } else {
            inventoryEmpty.style.display = 'block';
            inventoryItems.innerHTML = '';
        }
    }

    /**
     * Initialize a new game
     */
    async initializeNewGame() {
        try {
            // Get properly initialized game state from backend
            const response = await fetch('/api/state', {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to create new game state');
            }
            
            const data = await response.json();
            
            if (data.success && data.state) {
                this.gameState = data.state;
                this.terminal.print('\nStarting new game...', 'system');
                this.sendInitialCommand();
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error('Error initializing new game:', error);
            this.terminal.showError('Failed to start new game. Please refresh the page and try again.');
        }
    }

    /**
     * Continue saved game
     */
    async continueGame() {
        try {
            const savedState = await this.storageManager.loadState();
            
            if (savedState) {
                // Validate saved state structure
                if (this.validateGameState(savedState)) {
                    this.gameState = savedState;
                    this.updateInventoryDisplay();
                    this.terminal.print('\nGame loaded successfully!', 'success');
                    this.terminal.print('Type "look" to see your surroundings.\n', 'system');
                } else {
                    // Corrupted data detected
                    this.handleCorruptedSave();
                }
            } else {
                this.terminal.showError('Failed to load saved game. Starting new game.');
                await this.initializeNewGame();
            }
        } catch (error) {
            console.error('Error loading game:', error);
            
            // Check if it's a corrupted data error
            if (error.name === 'SyntaxError' || error.message.includes('parse')) {
                this.handleCorruptedSave();
            } else {
                this.terminal.showError('Failed to load saved game. Starting new game.');
                await this.initializeNewGame();
            }
        }
    }

    /**
     * Validate game state structure
     * @param {object} state - Game state to validate
     * @returns {boolean}
     */
    validateGameState(state) {
        const requiredFields = [
            'player_location',
            'inventory',
            'keys_collected',
            'visited_locations',
            'npc_interactions',
            'puzzle_states',
            'decision_history'
        ];

        for (const field of requiredFields) {
            if (!(field in state)) {
                console.error(`Missing required field: ${field}`);
                return false;
            }
        }

        return true;
    }

    /**
     * Handle corrupted save data
     */
    async handleCorruptedSave() {
        this.terminal.showError('Saved game data is corrupted or invalid.');
        this.terminal.print('The corrupted save will be cleared.', 'system');
        this.terminal.print('Type "new" to start a fresh game.\n', 'system');
        
        // Clear corrupted data
        try {
            await this.storageManager.clearState();
            console.log('Corrupted save data cleared');
        } catch (error) {
            console.error('Failed to clear corrupted data:', error);
        }
    }

    /**
     * Send initial command to start the game
     */
    async sendInitialCommand() {
        // Update inventory display
        this.updateInventoryDisplay();
        // Send a "look around" command to get the initial scene
        await this.processCommand('look around');
    }

    /**
     * Handle command from terminal
     * @param {string} command - User command
     */
    async handleCommand(command) {
        const lowerCommand = command.toLowerCase().trim();

        // Handle special client-side commands
        if (lowerCommand === 'continue' && !this.gameState) {
            await this.continueGame();
            return;
        }

        if (lowerCommand === 'new' && !this.gameState) {
            await this.clearSavedGame();
            await this.initializeNewGame();
            return;
        }

        if (lowerCommand === 'clear') {
            this.terminal.clear();
            return;
        }

        // Ensure game is initialized
        if (!this.gameState) {
            // Allow help command even before game starts
            if (lowerCommand === 'help' || lowerCommand === '?') {
                this.showHelp();
                return;
            }
            this.terminal.showError('Please type "continue" or "new" to begin.');
            return;
        }

        // Process command through backend
        await this.processCommand(command);
    }

    /**
     * Process command through backend
     * @param {string} command - User command
     */
    async processCommand(command) {
        try {
            // Send command to backend with streaming
            const result = await this.streamingHandler.sendCommand(command, this.gameState);

            // Handle result
            if (result.error) {
                this.terminal.showError(`Error: ${result.error}`);
                return;
            }

            // Update game state if provided
            if (result.game_state) {
                await this.updateGameState(result.game_state);
            }

            // TODO: Display image if provided (Task 10.2)
            // if (result.image_url) {
            //     this.terminal.showImage(result.image_url, result.image_alt || 'Location');
            // }

            // Handle special game events
            if (result.game_complete) {
                this.handleGameComplete();
            }

        } catch (error) {
            console.error('Command processing error:', error);
            this.terminal.showError('Failed to process command. Please try again.');
        }
    }

    /**
     * Save game state
     * @param {boolean} showFeedback - Whether to show save feedback to user
     */
    async saveGame(showFeedback = false) {
        try {
            await this.storageManager.saveState(this.gameState);
            if (showFeedback) {
                this.terminal.print('[Game saved]', 'system');
            }
        } catch (error) {
            console.error('Failed to save game:', error);
            
            // Show error for quota exceeded
            if (error.message.includes('quota')) {
                this.terminal.showError('Storage quota exceeded. Unable to save game.');
            }
            // Don't show error to user for other auto-save failures
        }
    }

    /**
     * Update game state and trigger auto-save
     * @param {object} newState - New game state
     */
    async updateGameState(newState) {
        this.gameState = newState;
        this.gameState.last_updated = new Date().toISOString();
        this.updateInventoryDisplay();
        await this.saveGame();
    }

    /**
     * Clear saved game
     */
    async clearSavedGame() {
        try {
            await this.storageManager.clearState();
            this.terminal.print('Saved game cleared.', 'system');
        } catch (error) {
            console.error('Failed to clear saved game:', error);
            this.terminal.showError('Failed to clear saved game.');
        }
    }

    /**
     * Show help information
     */
    showHelp() {
        const help = `
╔═══════════════════════════════════════════════════════════════╗
║                          HELP                                 ║
╚═══════════════════════════════════════════════════════════════╝

BASIC COMMANDS:
  look / look around     - Examine your surroundings
  examine [object]       - Look at something closely
  go [direction]         - Move in a direction
  take [item]            - Pick up an item
  use [item]             - Use an item from your inventory
  inventory / i          - View your inventory
  help                   - Show this help message
  clear                  - Clear the terminal screen

GAME COMMANDS:
  open door [number]     - Open one of the six doors (1-6)
  examine vault          - Look at the central vault
  talk to [npc]          - Speak with an NPC
  hint                   - Request a hint for the current puzzle

SPECIAL COMMANDS:
  new                    - Start a new game (clears saved progress)
  continue               - Continue from saved game

TIPS:
  - Use natural language! The AI understands various phrasings
  - Be creative with puzzle solutions
  - Talk to NPCs and remember past interactions
  - Explore thoroughly to find all items and clues
  - Your progress is automatically saved

Type any command to begin your adventure!
`;
        this.terminal.print(help, 'system');
    }

    /**
     * Handle game completion
     */
    handleGameComplete() {
        this.terminal.print('\n' + '═'.repeat(63), 'success');
        this.terminal.print('CONGRATULATIONS! You have completed Nature42!', 'success');
        this.terminal.print('═'.repeat(63) + '\n', 'success');
        
        // Optionally clear saved game
        setTimeout(() => {
            this.terminal.print('Type "new" to start a new adventure.', 'system');
        }, 2000);
    }

    /**
     * Get current game state
     * @returns {object}
     */
    getGameState() {
        return this.gameState;
    }

    /**
     * Check if game is initialized
     * @returns {boolean}
     */
    isReady() {
        return this.isInitialized && this.gameState !== null;
    }
}

// Initialize game client when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        window.gameClient = new GameClient();
        await window.gameClient.init();
    });
} else {
    (async () => {
        window.gameClient = new GameClient();
        await window.gameClient.init();
    })();
}
