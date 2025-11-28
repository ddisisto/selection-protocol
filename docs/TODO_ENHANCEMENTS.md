# Selection Protocol - Future Enhancements

**Status:** Post Phase 2 Core Implementation
**Created:** 2025-11-28

---

## Priority 1: Game Speed Field-Based Pause/Unpause

**Problem:** Current space-based pause/unpause has no verification. Can't observe game state.

**Solution:** Replace with game speed field verification at (1500, 50)

### Implementation Snippet

```python
def set_game_speed(speed, log_func=None):
    """
    Set game speed with field verification.

    Location: (1500, 50) window-relative
    Validates numeric field (0.0-100.0 range)
    Auto-detects UI hidden state
    """
    with io() as game_io:
        # Click speed field
        game_io.click(1500, 50, log_func)
        time.sleep(0.05)

        # Stuff clipboard with garbage
        game_io.write_clipboard("x", log_func)
        time.sleep(0.05)

        # Read current speed
        game_io.keypress('ctrl+a', log_func)
        time.sleep(0.05)
        game_io.keypress('ctrl+c', log_func)
        time.sleep(0.05)

        current_speed = game_io.read_clipboard(log_func)

        # Validate numeric field
        try:
            speed_val = float(current_speed)
            if not (0.0 <= speed_val <= 100.0):
                raise ValueError(f"Speed out of range: {speed_val}")
        except ValueError as e:
            if log_func:
                log_func("Speed field validation FAILED",
                         f"Not numeric or out of range: '{current_speed}'")
            # Field not visible - toggle UI and retry
            game_io.keypress('h', log_func)
            time.sleep(0.2)
            return set_game_speed(speed, log_func)  # Retry

        # Write new speed
        game_io.write_clipboard(str(speed), log_func)
        time.sleep(0.05)
        game_io.keypress('ctrl+v', log_func)
        time.sleep(0.05)
        game_io.keypress('Return', log_func)
```

### Benefits
- **Observable state:** 0 = paused, >0 = running
- **Verifiable targeting:** Numeric validation ensures correct field
- **Auto focus stealing:** Click steals focus from stuck inputs
- **UI state detection:** Field existence check detects hidden UI

### Migration
Replace in `GameState.paused()`:
```python
# OLD:
game_io.keypress('space', log_func)

# NEW:
set_game_speed(0, log_func)  # Pause
# ... do work ...
set_game_speed(original_speed, log_func)  # Restore
```

---

## Priority 2: Timing Adjustments

### Increase Base Delays
**Current:** 0.05s - 0.1s between actions
**Target:** 0.2s (200ms) for reliability

**Files to update:**
- `src/game_controller.py` - All time.sleep() calls in GameIO methods
- `src/game_controller.py` - apply_lineage_tag() sequence delays

### Post-Execution Drama Delay
**Purpose:** Give viewers time to see outcome, prevent rushed feel

**Implementation:**
```python
# In vote_manager._execute_winner()
if winner == 'k':
    result = send_keypress('Delete', self.log_action)
    time.sleep(1.5)  # Drama delay
elif winner == 'l':
    # ... tagging sequence ...
    result = send_keypress('Insert', self.log_action)
    time.sleep(1.5)  # Drama delay
```

---

## Priority 3: Enter Cleanup Strategy

**Problem:** Game input fields sometimes remain selected after sequences

**Solution:** Liberal Enter keypresses to terminate inputs

**Pattern:**
```python
# After any sequence that might leave input focused
game_io.keypress('Return', log_func)
time.sleep(0.05)
game_io.keypress('Return', log_func)  # Belt and suspenders
```

**Apply to:**
- End of apply_lineage_tag()
- After zoom commands
- After game speed changes
- After any clipboard operations

---

## Implementation Priority

1. **Timing adjustments** - Low risk, high impact (stability)
2. **Enter cleanup** - Low risk, prevents edge cases
3. **Game speed field** - Medium complexity, high value (observability)

---

## Testing Checklist

- [ ] All delays increased to 200ms
- [ ] Post-execution delays after K/L (1.5s)
- [ ] Enter cleanup prevents stuck inputs
- [ ] Game speed field validation works
- [ ] Game speed field detects hidden UI
- [ ] Pause/unpause via speed field reliable
- [ ] Original speed restored after operations

---

> ENHANCEMENTS DOCUMENTED
> LINEAGE TAGGING: OPERATIONAL
> FUTURE IMPROVEMENTS: QUEUED
