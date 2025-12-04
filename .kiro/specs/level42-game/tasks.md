# Implementation Plan: Nature42

- [x] 1. Set up project structure and dependencies





- [x] 1.1 Create project directory structure


  - Create backend Python package structure
  - Create static frontend directory structure (HTML, CSS, JS)
  - Set up requirements.txt with FastAPI, Strands SDK, and dependencies
  - _Requirements: 11.1_

- [x] 1.2 Configure AWS App Runner deployment files


  - Create apprunner.yaml with Python 3.11 configuration
  - Configure port 8080 and health check endpoint
  - Document environment variable requirements
  - _Requirements: 11.1_

- [x] 1.3 Install and verify Strands Agent SDK


  - Install strands-agents and strands-agents-tools
  - Create test agent to verify Bedrock connectivity
  - Document API key setup for development
  - _Requirements: 11.1, 11.2_

- [x] 2. Implement core data models



- [x] 2.1 Create game state data models


  - Implement GameState, LocationData, Item, Interaction, PuzzleState, Decision dataclasses
  - Add JSON serialization/deserialization methods
  - _Requirements: 5.3, 10.5_

- [ ]* 2.2 Write property test for game state serialization
  - **Property 12: Game state serialization round-trip**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 2.3 Create difficulty progression configuration


  - Implement DIFFICULTY_CURVE dictionary with door 1-6 parameters
  - Create helper functions to query difficulty settings
  - _Requirements: 13.7, 13.8, 13.9_

- [ ]* 2.4 Write property test for difficulty monotonicity
  - **Property 21: Difficulty increases with door number**
  - **Validates: Requirements 13.7**

- [x] 2.5 Create pop culture reference database


  - Implement POP_CULTURE_REFS dictionary organized by decade
  - Add helper functions to select random references by era
  - _Requirements: 9.1, 9.3_

- [x] 3. Build FastAPI backend server




- [x] 3.1 Create FastAPI application with basic routes


  - Initialize FastAPI app with CORS middleware
  - Implement health check endpoint for App Runner
  - Configure static file serving
  - _Requirements: 11.1_

- [x] 3.2 Implement streaming command endpoint


  - Create POST /api/command endpoint with SSE streaming
  - Integrate Strands Agent SDK stream_async
  - Handle command requests with game state context
  - _Requirements: 1.1, 18.1, 18.2_

- [ ]* 3.3 Write property test for command parsing
  - **Property 1: Command parsing produces intent**
  - **Validates: Requirements 1.1**

- [x] 3.4 Implement state management endpoints


  - Create GET /api/state endpoint
  - Create POST /api/state endpoint
  - Create DELETE /api/state endpoint (new game)
  - _Requirements: 5.1, 5.2_

- [x] 4. Implement Strands Agent integration

- [x] 4.1 Create content generation module



  - Implement ContentGenerator class with Strands Agent
  - Configure Bedrock model with appropriate temperature settings
  - Add age-appropriate content filtering
  - _Requirements: 11.2, 16.1, 16.2_

- [ ]* 4.2 Write property test for age-appropriate content
  - **Property 26: Generated content is age-appropriate**
  - **Validates: Requirements 16.1, 16.2, 16.3, 16.4**

- [x] 4.3 Implement location generation tool
  - Create generate_location method with door number and difficulty
  - Ensure pop culture references are included
  - Generate at least 2 exits per location
  - _Requirements: 2.1, 2.3, 2.5_

- [ ]* 4.4 Write property test for pop culture references
  - **Property 4: Pop culture references in generated content**
  - **Validates: Requirements 2.3, 9.1**

- [ ]* 4.5 Write property test for location exits
  - **Property 6: Generated locations have multiple exits**
  - **Validates: Requirements 2.5**

- [x] 4.6 Implement location caching for consistency
  - Store generated locations in game state
  - Retrieve cached descriptions on revisit
  - _Requirements: 2.4_

- [ ]* 4.7 Write property test for location consistency
  - **Property 5: Location description consistency**
  - **Validates: Requirements 2.4**

- [x] 4.8 Implement NPC dialogue generation
  - Create generate_npc_dialogue method with interaction history
  - Track NPC sentiment and personality
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 4.9 Write property test for NPC interaction recording
  - **Property 15: NPC interactions recorded in state**
  - **Validates: Requirements 8.1, 8.5**

- [x] 4.10 Implement puzzle generation and evaluation
  - Create generate_puzzle method with difficulty and virtues
  - Implement evaluate_puzzle_solution for creative solutions
  - Support multiple valid solution paths
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 4.11 Write property test for puzzle solutions
  - **Property 10: Puzzles accept multiple solutions**
  - **Validates: Requirements 4.1**

- [ ]* 4.12 Write property test for solved puzzle state
  - **Property 11: Solved puzzles provide feedback and update state**
  - **Validates: Requirements 4.3, 4.5**

- [x] 4.13 Implement hint generation system
  - Create generate_hint method considering keys collected
  - Adjust hint specificity based on progress
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ]* 4.14 Write property test for hint availability
  - **Property 22: Hint availability based on keys collected**
  - **Validates: Requirements 14.1, 14.4**

- [x] 5. Implement command processing logic






- [x] 5.1 Create command processor with AI-powered parsing


  - Implement CommandProcessor class
  - Use Strands Agent to parse natural language commands
  - Handle ambiguous and invalid commands
  - _Requirements: 1.1, 1.2, 1.3_

- [ ]* 5.2 Write property test for ambiguous commands
  - **Property 2: Ambiguous commands request clarification**
  - **Validates: Requirements 1.2**

- [ ]* 5.3 Write property test for invalid commands
  - **Property 3: Invalid commands provide helpful feedback**
  - **Validates: Requirements 1.3**



- [x] 5.4 Implement action validation with context





  - Create action validation logic considering location, inventory, state
  - Provide explanations for invalid actions
  - _Requirements: 12.1, 12.2, 12.3_

- [ ]* 5.5 Write property test for action validation
  - **Property 18: Action validation considers context**


  - **Validates: Requirements 12.1, 12.2, 12.3**

- [x] 5.6 Implement inventory management commands





  - Handle pick up, drop, view inventory, use item commands
  - Update game state accordingly
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 5.7 Write property test for inventory round-trip
  - **Property 7: Inventory round-trip consistency**
  - **Validates: Requirements 3.1, 3.5**

- [ ]* 5.8 Write property test for invalid item pickup
  - **Property 8: Invalid item pickup produces error**
  - **Validates: Requirements 3.2**



- [ ]* 5.9 Write property test for inventory display
  - **Property 9: Inventory view shows all items**
  - **Validates: Requirements 3.3**

- [x] 5.10 Implement core game mechanics





  - Handle door opening and world generation
  - Implement key retrieval and vault insertion
  - Detect vault opening with all 6 keys
  - _Requirements: 13.1, 13.2, 13.3, 13.5, 13.6_

- [ ]* 5.11 Write property test for door world generation
  - **Property 19: Door opening generates world**


  - **Validates: Requirements 13.3**

- [ ]* 5.12 Write property test for key insertion
  - **Property 20: Key insertion into vault**
  - **Validates: Requirements 13.5**

- [x] 5.13 Implement decision tracking





  - Record significant player choices in decision_history
  - Use history to influence future content generation
  - _Requirements: 10.1, 10.2, 10.5_

- [ ]* 5.14 Write property test for decision recording
  - **Property 17: Significant choices recorded in history**
  - **Validates: Requirements 10.5**

- [ ] 6. Build frontend terminal interface
- [ ] 6.1 Create HTML structure for terminal UI
  - Build index.html with terminal layout
  - Add footer with Privacy, Terms, About links and copyright
  - Create privacy.html, terms.html, about.html pages
  - _Requirements: 7.1, 17.1, 17.2, 17.6**

- [ ]* 6.2 Write test for footer links
  - **Property 27: Footer contains required links and copyright**
  - **Validates: Requirements 17.1, 17.6**

- [ ] 6.3 Implement CSS styling for retro terminal
  - Create terminal.css with monospace fonts and color schemes
  - Add CRT effects (scanlines, phosphor glow) using CSS filters
  - Create themes.css for different color schemes (amber, green)
  - _Requirements: 7.1, 7.2_

- [ ] 6.4 Implement accessibility mode toggle
  - Add toggle control for accessibility mode
  - Disable visual effects when enabled
  - Maintain core functionality
  - _Requirements: 7.4_

- [ ]* 6.5 Write property test for accessibility mode
  - **Property 14: Accessibility mode disables effects**
  - **Validates: Requirements 7.4**

- [ ] 6.6 Create JavaScript terminal UI controller
  - Implement terminal.js for DOM manipulation
  - Handle input/output display
  - Implement typing animation effects
  - _Requirements: 1.5, 7.3_

- [ ] 6.7 Implement streaming response handler
  - Create client-side streaming handler using Fetch API
  - Display text chunks incrementally as they arrive
  - Show visual feedback during streaming
  - Handle stream errors gracefully
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ]* 6.8 Write property test for streaming
  - **Property 28: Server streams responses to client**
  - **Validates: Requirements 18.1, 18.2**

- [ ] 6.9 Implement game client logic
  - Create game-client.js for game state management
  - Handle command sending and response processing
  - Coordinate with terminal UI for display
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 7. Implement browser storage
- [ ] 7.1 Create storage manager module
  - Implement storage.js using IndexedDB
  - Add serialization/deserialization functions
  - Handle storage quota and errors
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 7.2 Implement automatic save on state changes
  - Hook into game state updates
  - Automatically persist to IndexedDB
  - _Requirements: 5.1_

- [ ] 7.3 Implement automatic restore on page load
  - Check for saved game on initialization
  - Prompt user to continue or start fresh
  - Handle corrupted data gracefully
  - _Requirements: 5.2, 5.4, 5.5_

- [ ]* 7.4 Write property test for corrupted storage
  - **Property 13: Corrupted storage handled gracefully**
  - **Validates: Requirements 5.5**

- [ ] 8. Implement sharing functionality
- [ ] 8.1 Create shareable postcard generator
  - Generate formatted summary with image and description
  - Include keys collected count
  - Exclude puzzle solutions and spoilers
  - _Requirements: 15.1, 15.2, 15.3, 15.5_

- [ ]* 8.2 Write property test for shareable content fields
  - **Property 23: Shareable content includes required fields**
  - **Validates: Requirements 15.1, 15.2, 15.3**

- [ ]* 8.3 Write property test for share exclusions
  - **Property 25: Shares exclude puzzle solutions**
  - **Validates: Requirements 15.5**

- [ ] 8.4 Implement unique share code generation
  - Generate unique codes for each share
  - Store share data for retrieval
  - _Requirements: 15.4_

- [ ]* 8.5 Write property test for share code uniqueness
  - **Property 24: Share codes are unique**
  - **Validates: Requirements 15.4**

- [ ] 9. Create legal and informational pages
- [ ] 9.1 Write Privacy Policy content
  - Document AI/LLM data usage
  - Explain browser storage usage
  - Detail data retention policies
  - _Requirements: 17.3_

- [ ] 9.2 Write User Agreement content
  - Create terms of service for AI-powered game
  - Include age requirements (13+)
  - _Requirements: 17.4_

- [ ] 9.3 Write About page content
  - Provide high-level game overview
  - Explain core mechanics and objectives
  - Describe the six keys quest
  - _Requirements: 17.5_

- [ ] 10. Implement image generation
- [ ] 10.1 Integrate Strands SDK for image generation
  - Use Strands tools for location image creation
  - Apply age-appropriate content filters
  - Handle generation failures with placeholders
  - _Requirements: 2.2, 16.4_

- [ ] 10.2 Implement image display in terminal
  - Add image rendering to terminal UI
  - Handle loading states and errors
  - _Requirements: 2.2_

- [ ] 11. Initialize game with forest clearing
- [ ] 11.1 Create static forest clearing location
  - Implement starting location with 6 doors and vault
  - Add vault examination showing "The Ultimate Question" inscription
  - Ensure consistent starting state
  - _Requirements: 13.1, 13.2_

- [ ] 11.2 Implement vault opening sequence
  - Detect when all 6 keys are inserted
  - Display the philosophical message about meaning of 42
  - Show game completion
  - _Requirements: 13.6_

- [ ] 12. Error handling and resilience
- [ ] 12.1 Implement comprehensive error handling
  - Add error handlers for all API endpoints
  - Implement retry logic with exponential backoff
  - Handle Strands SDK unavailability
  - _Requirements: 11.3, 11.4_

- [ ] 12.2 Add user-friendly error messages
  - Create error message templates
  - Display helpful information to players
  - Provide recovery options
  - _Requirements: 1.3, 5.5, 18.4_

- [ ] 13. Testing and quality assurance
- [ ]* 13.1 Set up Hypothesis for property-based testing
  - Install Hypothesis library
  - Configure test settings for 100+ iterations
  - Create test data generation strategies
  - _Requirements: All property tests_

- [ ]* 13.2 Implement unit tests for core functionality
  - Test command parsing with specific examples
  - Test state management edge cases
  - Test storage serialization scenarios
  - Test UI component behavior
  - _Requirements: All requirements_

- [ ]* 13.3 Create integration tests
  - Test complete game flow from start to first key
  - Test save/restore across sessions
  - Test full door exploration cycle
  - Test vault opening with all keys
  - _Requirements: All requirements_

- [ ] 14. Deployment preparation
- [ ] 14.1 Create requirements.txt
  - List all Python dependencies with versions
  - Include FastAPI, Strands SDK, Hypothesis
  - _Requirements: 11.1_

- [ ] 14.2 Configure environment variables
  - Document required environment variables
  - Set up AWS_BEDROCK_API_KEY configuration
  - Configure App Runner environment
  - _Requirements: 11.1_

- [ ] 14.3 Test deployment to AWS App Runner
  - Deploy to App Runner
  - Verify health check endpoint
  - Test streaming functionality in production
  - Verify static file serving
  - _Requirements: 11.1_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
