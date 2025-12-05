# Command Processor Refactoring Plan

## Overview
The command_processor.py file has grown to 1513 lines. This document outlines the refactoring to break it into smaller, more maintainable modules.

## New Module Structure

### 1. `command_models.py` ✅ CREATED
**Purpose:** Data classes for command processing
**Contents:**
- `Intent` - Parsed command intent
- `ValidationResult` - Action validation result
- `ActionResult` - Action execution result
- `CommandResult` - Complete command result

### 2. `action_handlers.py` ✅ CREATED
**Purpose:** Basic game action handlers
**Contents:**
- `ActionHandlers` class with methods:
  - `handle_movement()` - Player movement
  - `handle_take_item()` - Pick up items
  - `handle_drop_item()` - Drop items
  - `handle_inventory()` - View inventory
  - `handle_use_item()` - Use items
  - `handle_examine()` - Examine objects/environment
  - `handle_help()` - Display help

### 3. `door_handlers.py` ✅ CREATED
**Purpose:** Door-specific action handlers
**Contents:**
- `DoorHandlers` class with methods:
  - `handle_open_door()` - Open doors and generate worlds
  - `handle_retrieve_key()` - Get keys from worlds
  - `handle_insert_key()` - Insert keys into vault

### 4. `command_processor.py` (SIMPLIFIED)
**Purpose:** Main command processing coordination
**Contents:**
- `CommandProcessor` class with:
  - `process_command()` - Main entry point
  - `_parse_intent()` - AI-powered command parsing
  - `_validate_action()` - Context-aware validation
  - `_execute_action()` - Route to appropriate handler
  - `_is_significant_decision()` - Decision tracking
  - `_create_decision()` - Decision creation

## Benefits

1. **Improved Maintainability**
   - Each module has a single, clear responsibility
   - Easier to locate and modify specific functionality
   - Reduced cognitive load when working on code

2. **Better Testability**
   - Can test handlers independently
   - Easier to mock dependencies
   - More focused unit tests

3. **Reduced Complexity**
   - Smaller files are easier to understand
   - Clear separation of concerns
   - Better code organization

4. **Easier Collaboration**
   - Multiple developers can work on different modules
   - Reduced merge conflicts
   - Clear module boundaries

## Migration Strategy

### Phase 1: Create New Modules ✅ DONE
- Created `command_models.py`
- Created `action_handlers.py`
- Created `door_handlers.py`

### Phase 2: Update CommandProcessor (TODO)
- Import new modules
- Replace method calls with handler calls
- Remove extracted methods
- Keep validation and parsing logic

### Phase 3: Update Tests (TODO)
- Update imports in test files
- Ensure all tests still pass
- Add tests for new modules if needed

### Phase 4: Update Documentation (TODO)
- Update docstrings
- Update README if needed
- Document new module structure

## File Size Comparison

**Before:**
- `command_processor.py`: 1513 lines

**After (Estimated):**
- `command_models.py`: ~120 lines
- `action_handlers.py`: ~380 lines
- `door_handlers.py`: ~250 lines
- `command_processor.py`: ~400 lines (simplified)
- **Total**: ~1150 lines (better organized)

## Import Changes Required

### In command_processor.py:
```python
from backend.services.command_models import (
    Intent, ValidationResult, ActionResult, CommandResult
)
from backend.services.action_handlers import ActionHandlers
from backend.services.door_handlers import DoorHandlers
```

### In test files:
```python
# Old
from backend.services.command_processor import Intent, ActionResult, CommandResult

# New
from backend.services.command_models import Intent, ActionResult, CommandResult
from backend.services.command_processor import CommandProcessor
```

## Testing Checklist

- [ ] Run all existing tests
- [ ] Verify command processing still works
- [ ] Test door opening
- [ ] Test inventory management
- [ ] Test movement
- [ ] Test key retrieval and insertion
- [ ] Test help command
- [ ] Test examination
- [ ] Integration test: Complete game flow

## Rollback Plan

If issues arise:
1. Keep original `command_processor.py` as `command_processor_backup.py`
2. Can quickly revert by renaming files
3. Git history preserves all changes

## Next Steps

1. Update `command_processor.py` to use new modules
2. Run tests to verify functionality
3. Fix any import errors in test files
4. Document changes
5. Delete backup file once stable
