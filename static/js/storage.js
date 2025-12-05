/**
 * Storage Manager
 * Handles game state persistence using IndexedDB
 */

class StorageManager {
    constructor() {
        this.dbName = 'nature42_db';
        this.storeName = 'gameState';
        this.version = 1;
        this.db = null;
    }

    /**
     * Initialize IndexedDB
     * @returns {Promise<void>}
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => {
                console.error('Failed to open IndexedDB:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('IndexedDB initialized');
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object store if it doesn't exist
                if (!db.objectStoreNames.contains(this.storeName)) {
                    db.createObjectStore(this.storeName);
                    console.log('Created object store:', this.storeName);
                }
            };
        });
    }

    /**
     * Save game state
     * @param {object} state - Game state object
     * @returns {Promise<boolean>}
     */
    async saveState(state) {
        if (!this.db) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([this.storeName], 'readwrite');
                const store = transaction.objectStore(this.storeName);
                
                // Serialize state with timestamp
                const data = {
                    state: state,
                    savedAt: new Date().toISOString()
                };

                const request = store.put(data, 'current');

                request.onsuccess = () => {
                    console.log('Game state saved');
                    resolve(true);
                };

                request.onerror = () => {
                    console.error('Failed to save state:', request.error);
                    
                    // Check if quota exceeded
                    if (request.error.name === 'QuotaExceededError') {
                        this.handleQuotaExceeded().then(() => {
                            reject(new Error('Storage quota exceeded'));
                        });
                    } else {
                        reject(request.error);
                    }
                };

            } catch (error) {
                console.error('Save state error:', error);
                reject(error);
            }
        });
    }

    /**
     * Load game state
     * Implements Requirement 5.5: Detect and handle corrupted state
     * @returns {Promise<object|null>}
     */
    async loadState() {
        if (!this.db) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([this.storeName], 'readonly');
                const store = transaction.objectStore(this.storeName);
                const request = store.get('current');

                request.onsuccess = () => {
                    if (request.result) {
                        console.log('Game state loaded');
                        
                        // Validate state structure
                        const state = request.result.state;
                        if (this.validateState(state)) {
                            resolve(state);
                        } else {
                            console.error('Invalid state structure');
                            resolve(this.handleCorruptedData(new Error('Invalid state structure')));
                        }
                    } else {
                        console.log('No saved game found');
                        resolve(null);
                    }
                };

                request.onerror = () => {
                    console.error('Failed to load state:', request.error);
                    reject(request.error);
                };

            } catch (error) {
                console.error('Load state error:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Validate game state structure
     * @param {object} state - Game state to validate
     * @returns {boolean} - True if valid
     */
    validateState(state) {
        if (!state || typeof state !== 'object') {
            return false;
        }
        
        // Check required fields
        const requiredFields = ['player_location', 'inventory', 'keys_collected', 'visited_locations'];
        for (const field of requiredFields) {
            if (!(field in state)) {
                console.error(`Missing required field: ${field}`);
                return false;
            }
        }
        
        // Validate keys_collected
        if (!Array.isArray(state.keys_collected)) {
            console.error('keys_collected must be an array');
            return false;
        }
        
        if (state.keys_collected.length > 6) {
            console.error('Too many keys collected');
            return false;
        }
        
        for (const key of state.keys_collected) {
            if (typeof key !== 'number' || key < 1 || key > 6) {
                console.error(`Invalid key number: ${key}`);
                return false;
            }
        }
        
        // Validate inventory
        if (!Array.isArray(state.inventory)) {
            console.error('inventory must be an array');
            return false;
        }
        
        return true;
    }

    /**
     * Clear saved game state
     * @returns {Promise<boolean>}
     */
    async clearState() {
        if (!this.db) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            try {
                const transaction = this.db.transaction([this.storeName], 'readwrite');
                const store = transaction.objectStore(this.storeName);
                const request = store.delete('current');

                request.onsuccess = () => {
                    console.log('Game state cleared');
                    resolve(true);
                };

                request.onerror = () => {
                    console.error('Failed to clear state:', request.error);
                    reject(request.error);
                };

            } catch (error) {
                console.error('Clear state error:', error);
                reject(error);
            }
        });
    }

    /**
     * Check if saved game exists
     * @returns {Promise<boolean>}
     */
    async hasSavedGame() {
        try {
            const state = await this.loadState();
            return state !== null;
        } catch (error) {
            console.error('Error checking for saved game:', error);
            return false;
        }
    }

    /**
     * Handle corrupted data gracefully
     * Implements Requirement 5.5: Graceful handling of corrupted storage
     * @param {Error} error - Error object
     * @returns {null}
     */
    handleCorruptedData(error) {
        console.error('Corrupted data detected:', error);
        
        // Show user-friendly error message
        if (window.terminal) {
            window.terminal.showError('Your game save appears to be corrupted.');
            window.terminal.print('\nThis can happen if your browser storage was cleared or modified.', 'system');
            window.terminal.print('\nSuggestions:', 'system');
            window.terminal.print('  • Start a new game to continue playing', 'system');
            window.terminal.print('  • Check if you have another save in a different browser', 'system');
            window.terminal.print('  • Make sure cookies and local storage are enabled', 'system');
            window.terminal.print("\nType 'new game' to start fresh.", 'system');
        }
        
        // Attempt to clear corrupted data
        this.clearState().catch(err => {
            console.error('Failed to clear corrupted data:', err);
        });

        return null;
    }

    /**
     * Check storage quota and available space
     * @returns {Promise<object>}
     */
    async checkStorageQuota() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            try {
                const estimate = await navigator.storage.estimate();
                const percentUsed = (estimate.usage / estimate.quota) * 100;
                
                return {
                    usage: estimate.usage,
                    quota: estimate.quota,
                    percentUsed: percentUsed.toFixed(2),
                    available: estimate.quota - estimate.usage
                };
            } catch (error) {
                console.error('Failed to estimate storage:', error);
                return null;
            }
        }
        return null;
    }

    /**
     * Handle storage quota exceeded error
     * Implements Requirement 5.5: Handle storage errors gracefully
     * @returns {Promise<boolean>}
     */
    async handleQuotaExceeded() {
        console.warn('Storage quota exceeded');
        
        // Check current usage
        const quota = await this.checkStorageQuota();
        if (quota) {
            console.log(`Storage usage: ${quota.percentUsed}% (${quota.usage} / ${quota.quota} bytes)`);
        }

        // Show user-friendly error message
        if (window.terminal) {
            window.terminal.showError("I couldn't save your progress. Your browser storage is full.");
            window.terminal.print('\nSuggestions:', 'system');
            window.terminal.print('  • Check if your browser has enough storage space', 'system');
            window.terminal.print('  • Try clearing old browser data', 'system');
            window.terminal.print('  • Continue playing, but be aware progress may not save', 'system');
            
            if (quota) {
                window.terminal.print(`\nStorage usage: ${quota.percentUsed}% (${Math.round(quota.usage / 1024)} KB used)`, 'system');
            }
        }

        return false;
    }

    /**
     * Serialize game state to JSON
     * @param {object} state - Game state object
     * @returns {string}
     */
    serialize(state) {
        try {
            return JSON.stringify(state);
        } catch (error) {
            console.error('Serialization error:', error);
            throw new Error('Failed to serialize game state');
        }
    }

    /**
     * Deserialize game state from JSON
     * @param {string} data - JSON string
     * @returns {object}
     */
    deserialize(data) {
        try {
            return JSON.parse(data);
        } catch (error) {
            console.error('Deserialization error:', error);
            return this.handleCorruptedData(error);
        }
    }

    /**
     * Get storage statistics
     * @returns {Promise<object>}
     */
    async getStats() {
        const quota = await this.checkStorageQuota();
        const hasSaved = await this.hasSavedGame();
        
        return {
            hasSavedGame: hasSaved,
            quota: quota,
            dbName: this.dbName,
            storeName: this.storeName
        };
    }
}

// Initialize storage manager
window.storageManager = new StorageManager();
