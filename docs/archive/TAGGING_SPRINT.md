# Sprint: Lineage Tagging (Phase 2 Core)

**Goal:** First L voter's username tags parent organism on L-win, verified via clipboard.

**Why:** This is the engagement hook. Voting without lineage ownership is just infrastructure.

---

## Current State

**Working:**
- Vote system (k/l/x) with first-L claimant tracking
- Dynamic timer, automated execution (K→Delete, L→Insert)
- `vote_manager.first_l_claimant` holds username on L-win
- Game controller (`send_keypress`) handles xdotool automation
- Window auto-discovery at startup

**Not yet built:**
- Tagging sequence (click, paste, confirm)
- Clipboard verification
- Overlay display of lineage ownership

---

## Tagging Sequence

**Trigger:** L wins vote resolution (in `vote_manager._execute_winner()`)

**Sequence (pseudocode):**

```
on L win:
    username = first_l_claimant
    
    # 1. Pause for drama + stability
    send_keypress('space')  # pause game
    wait(500ms)
    
    # 2. Click tag input field (window-relative coords)
    click_element(TAG_FIELD_X, TAG_FIELD_Y)
    wait(200ms)
    
    # 3. Verify we're in right field
    send_keypress('ctrl+a')
    send_keypress('ctrl+c')
    clipboard_content = read_clipboard()
    
    if clipboard_looks_valid(clipboard_content):
        # 4. Apply tag
        write_clipboard(username)
        send_keypress('ctrl+v')
        wait(100ms)
        send_keypress('Return')  # confirm
        
        # 5. Optional: verify it stuck
        send_keypress('ctrl+a')
        send_keypress('ctrl+c')
        verify_content = read_clipboard()
        success = (verify_content == username)
    else:
        success = False
        log("Tag field verification failed, aborting")
    
    # 6. Resume
    wait(300ms)
    send_keypress('space')  # unpause
    
    # 7. Then execute the L action
    send_keypress('Insert')
    
    return success
```

---

## Implementation Components

### 1. Click Automation

**Extend `game_controller.py`:**

```
click_at(x, y)
    # Window-relative click using xdotool
    # xdotool mousemove --window {window_id} x y
    # xdotool click --window {window_id} 1
```

**Coordinate discovery:**
- Manual: run game, find tag field location at known zoom/view
- Store in config.yaml under `game.tag_field` coords
- May need multiple coord sets for different UI states

### 2. Clipboard Operations

**New module or extend `game_controller.py`:**

```
read_clipboard()
    # xclip -selection clipboard -o
    # or xsel --clipboard --output
    # returns string

write_clipboard(text)
    # echo {text} | xclip -selection clipboard
    # or xsel --clipboard --input
```

**Validation function:**

```
clipboard_looks_valid(content)
    # Empty or whitespace-only = probably correct field
    # Existing username pattern = field has old tag (ok to overwrite)
    # Long text / unexpected = wrong field, abort
```

### 3. Execution Integration

**Modify `vote_manager._execute_winner()`:**

Current:
```python
elif winner == 'l':
    send_keypress('Insert', self.log_action)
```

New:
```python
elif winner == 'l':
    claimant = self.first_l_claimant
    if claimant:
        success = apply_lineage_tag(claimant, self.log_action)
        # Tag attempt logged regardless of success
    send_keypress('Insert', self.log_action)
```

Tag failure shouldn't block the L action—lineage is bonus, not gate.

### 4. Overlay Display

**On L-win, broadcast lineage claim:**

```python
socketio.emit('lineage_claimed', {
    'username': claimant,
    'verified': success,
    'timestamp': datetime.now().isoformat()
})
```

**Overlay shows:**
- "Lineage claimed by @username" (transient notification)
- Optionally: running list of active lineages (later, from savefile)

---

## Configuration

**Add to `config.yaml`:**

```yaml
game:
  window_title: "The Bibites"
  
  # Tag field coordinates (window-relative)
  # Discover manually, may vary by resolution/UI state
  tag_field:
    x: 850
    y: 450
  
  # Timing (ms)
  tagging:
    pause_delay: 500
    click_delay: 200
    verify_delay: 100
    resume_delay: 300
```

---

## Failure Handling

**Clipboard verification fails:**
- Log warning with clipboard content
- Skip tagging, continue with Insert
- Emit event with `verified: false`
- Manual cleanup later if needed

**Click misses target:**
- Clipboard check catches this (unexpected content)
- Same handling as above

**Timing issues:**
- Increase delays in config
- Add retry logic if persistent (later)

**Philosophy:** Fail open. Tagging is enhancement, not critical path. Better to execute L without tag than block on tagging failure.

---

## Testing Approach

1. **Manual coordinate discovery:** Run game, identify tag field location
2. **Isolated click test:** Click function hits correct spot
3. **Clipboard round-trip:** Write → read → verify
4. **Full sequence (paused):** Run tagging sequence with game paused manually
5. **Integrated test:** L-win triggers full sequence automatically
6. **Failure injection:** Wrong coords, verify graceful degradation

---

## Out of Scope (This Sprint)

- Savefile verification/reconciliation
- OCR of info panels
- Lineage tracking/statistics
- Leaderboard display
- Multiple tag field locations for different UI states

---

## Success Criteria

- [ ] L-win triggers tagging sequence
- [ ] Username appears in game tag field (visually confirmed)
- [ ] Clipboard verification catches wrong-field clicks
- [ ] Failure doesn't block L execution
- [ ] Overlay shows lineage claim event
- [ ] Works reliably 3+ times in manual testing

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/game_controller.py` | Add `click_at()`, clipboard functions |
| `src/vote_manager.py` | Call tagging sequence on L-win |
| `config.yaml` | Add tag field coords, timing config |
| `src/static/overlay.js` | Handle `lineage_claimed` event |
| `src/templates/overlay.html` | Lineage notification element |

---

## Open Questions (Resolve During Implementation)

1. **What zoom/view state exposes tag field?** Need consistent UI state before clicking.
2. **Does tag field exist for all organisms?** Or only when selected?
3. **Exact xdotool syntax for window-relative click?** Test and confirm.
4. **xclip vs xsel?** Check what's installed, pick one.

---

> **Core deliverable:** First L voter sees their username on the organism.
> **Verification:** Clipboard check before paste.
> **Failure mode:** Skip tagging, log, continue.