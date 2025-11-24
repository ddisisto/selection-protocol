# Selection Protocol - Session 8 Handover

**Date:** 2025-11-25
**Phase:** Phase 1 Polish - Chat Integration & Cooldown Refinement
**Status:** Bot fully operational, game commands refined, ready for live testing

---

## Quick Orientation

**Session 8 Achievements:**
- ✅ Fixed command parsing to match CHAT_UX.md specification
- ✅ Refactored info panels (0-4 with hide logic, removed h/s)
- ✅ Implemented bot message filtering + colored announcements
- ✅ Fixed OAuth token validation with fail-fast behavior
- ✅ Refined zoom cooldowns (exponential formula, directional asymmetry)
- ✅ Tuned cooldown values (±15 zoom range, 10s info panels)

**What Changed:**
- Command parsing now follows CHAT_UX.md (first word only)
- Info panels: `0` hides, `1-4` show specific panels (smart state tracking)
- Bot filters its own messages (prevents announcement loops)
- Colored announcements: blue (default), green (L-related), orange (K-related)
- OAuth token must be authorized by bot account (fail-fast validation)
- Zoom cooldowns: 1.464^distance, ±15 range, directional (toward=1s, away=exponential)

**Next Session (9):**
- Code review and cleanup
- Documentation updates
- Overlay state display + layout/visual improvements

---

## Session 8 Detailed Progress

### 1. Command Parsing Fix (CHAT_UX.md Compliance)
**Problem:** Parser was accepting commands anywhere in message, conflicting with natural conversation.

**Solution:** Implemented first-word-only parsing per CHAT_UX.md spec
- Created `parse_first_word()` function (src/twitch_bot.py)
- Handles leading punctuation, whitespace, case-insensitive
- Rejects commands mid-message ("hey k" → no match)

**Files Changed:**
- `src/twitch_bot.py` - Added parse_first_word(), updated event_message()

**Commit:** `ef577fc`

---

### 2. Info Panel Refactor (0-4 with Hide Logic)
**Problem:** Commands `h` and `s` were confusing (hide/show toggle). Needed explicit panel selection.

**Solution:** Changed to 0-4 system
- `0` = hide UI (sends `h`)
- `1-4` = show specific panel (sends `h` then number if needed)
- Smart state tracking: current + last_non_zero
- Multi-step keypresses for hide→show transitions
- Rejects duplicate selections (prevents toggle spam)

**Files Changed:**
- `src/game_commands.py` - Added 0-4, removed h/s
- `src/game_state.py` - Created InfoPanelGroup class
- `src/twitch_bot.py` - Parse 0-4 commands

**Commit:** `03822e8`

---

### 3. Bot Message Filtering + Colored Announcements
**Problem:** Bot parsed its own announcements, creating loops. Needed colored announcements for context.

**Solution:**
1. **Message filtering** - Compare `payload.chatter.id` to `bot_id`
2. **Colored announcements** - Prefix with `/announceblue`, `/announcegreen`, `/announceorange`
   - Blue: default/neutral (startup, X outcomes)
   - Green: L-related (L opens round, L wins)
   - Orange: K-related (K opens round, K wins)
3. **OAuth scope fix** - URL-encode scope parameter with `quote()`

**Files Changed:**
- `src/twitch_bot.py` - Added user ID filtering, colored _send_chat_message()
- `src/oauth_flow.py` - URL encoding for OAuth parameters

**Commits:** `4b6fc94`, `5c31737`

---

### 4. OAuth Token Validation (Fail-Fast)
**Problem:** Bot couldn't send messages because token belonged to channel owner, not bot account.

**Root Cause:** User authorized OAuth while logged into wrong Twitch account.

**Solution:**
1. Enhanced `_validate_token()` with critical checks:
   - Token user ID must match bot user ID (FATAL if not)
   - All required scopes must be present (FATAL if missing)
   - Exit immediately with clear remediation steps
2. Added detailed error messages with step-by-step fix instructions

**Files Changed:**
- `src/twitch_bot.py` - Enhanced _validate_token() (lines 115-181)

**Commit:** `5c31737`

---

### 5. Zoom Cooldown Refinements
**Problem:** Initial cooldown scaling too gradual (1.1^distance, ±50 range). Directional cooldowns not working.

**Solution (3 iterations):**

**Iteration 1: Exponential + Directional Concept** (`984d39e`)
- Changed from linear to exponential: `1.0 * 1.1^distance`
- Separate cooldowns: toward center = 1s, away = exponential
- Added last_direction tracking

**Iteration 2: Steeper Curve + Logging** (`ad5522e`)
- Reduced range: ±50 → ±15
- Steeper exponential: 1.1 → 1.464 (120s at distance 14)
- Added detailed logging: `[ZOOM] Distance: +5 | Next cooldowns: IN=7.30s, OUT=1.00s`

**Iteration 3: Direction Check Fix** (`d102b69`)
- **Critical bug:** Cooldown checked `self.last_direction` instead of requested `direction`
- Fixed: Check cooldown for requested direction (enables asymmetry)
- Now works: zoom out 6.73s → immediately zoom in 1s ✓

**Files Changed:**
- `src/game_state.py` - ZoomTracker class, exponential formula, logging

**Commits:** `984d39e`, `ad5522e`, `d102b69`

---

### 6. Info Panel Cooldown Tuning
**Problem:** 15s cooldown felt too long for rapid interaction.

**Solution:** Reduced to 10s for faster iteration while preventing spam.

**Files Changed:**
- `src/game_state.py` - InfoPanelGroup cooldown: 15.0 → 10.0

**Commit:** `984d39e`

---

## Technical Highlights

### Directional Zoom Cooldowns (Self-Regulating)
**Formula:**
```python
# Moving toward center: 1s (always)
# Moving away from center: 1.0 * 1.464^|distance|

# At distance 0: 1.0s
# At distance 5: 7.30s
# At distance 10: 53.4s
# At distance 14: 120s (max)
```

**Key Insight:** Cooldown is based on **requested direction**, not last direction taken. This enables true asymmetry: easy return, hard escape.

### OAuth Token Ownership
**Critical:** Token must belong to the bot account (`sp_bot_`), not the channel owner (`selection_protocol`). The `/helix/chat/messages` API requires `sender_id` to match the token's user ID.

**Validation:** Fail-fast on startup, clear error messages with remediation steps.

### Info Panel State Tracking
**Smart Logic:**
- `current`: Current value (0-4), None = unknown
- `last_non_zero`: Last selected panel (1-4)
- `0` command: Hide if visible, reject if already hidden
- `1-4` command: If hidden, send `h` + number (if ≠ last_non_zero). If visible, send number (if ≠ current).

**Prevents:** Toggle spam, redundant state changes.

---

## Current System State

**Architecture:**
```
Twitch Chat → EventSub Bot → SocketIO → Flask Server
                                              ↓
                              Vote Manager + Game State
                                              ↓
                              Broadcasts (vote_update, game_state_update)
                                              ↓
                              Overlay + Admin Panel (displays)
                                              ↓
                              game_controller → xdotool → The Bibites
```

**Key Files:**
- `src/server.py` - Flask app, instantiates vote_manager + game_state
- `src/vote_manager.py` - Votes, timer, execution, round_start/round_end events
- `src/game_state.py` - Commands, cooldowns, state tracking (ZoomTracker, InfoPanelGroup)
- `src/twitch_bot.py` - EventSub, parses votes + commands, colored announcements
- `src/websocket.py` - SocketIO handlers (votes, commands, events)
- `src/game_commands.py` - Command registry (0-4, +/-)
- `src/oauth_flow.py` - OAuth flow with URL encoding

**Branches:**
- `main` - Clean, operational (current)
- `feature/game-state-overlay-ui` - UI widgets (deferred to Session 9)

**Recent Commits (Session 8):**
```
d102b69 - Fix zoom cooldown direction check (enable asymmetric cooldowns)
ad5522e - Tune zoom cooldown formula: ±15 range, steeper exponential curve
984d39e - Refine game command cooldowns (zoom exponential + info panels 10s)
5c31737 - Fix OAuth token validation and add colored announcements
4b6fc94 - Filter bot messages and add colored announcements
03822e8 - Refactor info panels: add 0 (hide), remove h/s commands
ef577fc - Fix command parsing to match CHAT_UX.md spec
```

---

## Testing Performed

**Live Testing Throughout Session:**
- Command parsing (first word only, rejects mid-message)
- Info panels (0-4, hide/show logic, multi-step keypresses)
- Bot message filtering (no announcement loops)
- Colored announcements (blue/green/orange in Twitch chat)
- OAuth token validation (fail-fast on mismatch)
- Zoom cooldowns (exponential scaling, directional asymmetry)
- Server logs (zoom distance + cooldowns displayed)

**Results:** All features operational, ready for live stream testing.

---

## Known Issues & Gotchas

**OAuth Token:**
- Must be authorized by bot account (`sp_bot_`), not channel owner
- Delete `.twitch_token` and re-authorize if user mismatch
- Token validation exits immediately on critical errors

**Zoom Cooldowns:**
- Logging shows both directions (IN/OUT) after each zoom
- Formula: 1.464^distance (exponential growth)
- Range capped at ±15 (hard limits)

**Info Panels:**
- Rejects selecting current panel (prevents toggle)
- Multi-step keypresses logged sequentially
- `0` command rejects if already hidden

**Game Window:**
- Must be running before server starts (auto-discovery)
- Server exits with error if not found (fail-fast)

---

## Session 8 Success Metrics

**Completed:**
- ✅ All planned commits (5 major features)
- ✅ Bot fully operational (sends colored announcements)
- ✅ OAuth authentication working (token ownership fixed)
- ✅ Command parsing compliant with CHAT_UX.md spec
- ✅ Game commands refined (0-4 info panels, exponential zoom)
- ✅ Cooldowns tuned (10s panels, 1-120s zoom)
- ✅ Live testing validated all features

**Deferred to Session 9:**
- Overlay UI polish (feature/game-state-overlay-ui branch)
- Code review and cleanup
- Documentation updates
- Design discussions for visual feedback

---

## Next Session (9) Priorities

### Priority 1: Code Review
**Scope:** Review Session 6-8 code for consistency, DRY principles, documentation

**Focus Areas:**
- Game state classes (ZoomTracker, InfoPanelGroup)
- Command parsing logic
- OAuth validation
- Cooldown formulas

### Priority 2: Documentation Updates
**Files to Update:**
- README.md - Game commands section, current status
- PROJECT_BRIEF.md - Architecture updates
- CLAUDE.md - New patterns learned (fail-fast, directional cooldowns)

### Priority 3: Overlay State Display
**Context:** feature/game-state-overlay-ui branch has working widgets

**Tasks:**
1. Design discussion: Layout, placement, sizing
2. Visual feedback polish: Animations, colors, states
3. Integration with main overlay
4. Merge when ready

### Priority 4: Optional - Live Stream Preparation
**If time permits:**
- End-to-end testing with multiple users
- Performance testing (sustained load)
- Edge case testing (rapid commands, cooldown edge cases)

---

## Documentation Structure

For complete context:
- **[CLAUDE.md](../CLAUDE.md)** - Workflows, patterns (START HERE)
- **[README.md](../README.md)** - Project overview
- **[PROJECT_BRIEF.md](../PROJECT_BRIEF.md)** - Technical spec
- **[CONTEXT.md](../CONTEXT.md)** - Design philosophy
- **[VOTING_RULES.md](VOTING_RULES.md)** - Vote mechanics
- **[docs/archive/](.)** - Historical handovers (0-8)

---

## Key Learnings (Session 8)

**Fail-Fast Design:**
- OAuth token validation immediately exits on critical errors
- Clear error messages with remediation steps
- Prevents confusing downstream failures

**Directional Cooldowns:**
- Check cooldown for **requested** direction, not last direction
- Enables true asymmetry (easy return, hard escape)
- Self-regulating system creates natural equilibrium

**Bot Message Filtering:**
- User ID comparison more reliable than username matching
- Prevents announcement loops (bot parsing its own messages)

**Colored Announcements:**
- Context-aware colors improve chat readability
- Blue (default), green (L-related), orange (K-related)

**Exponential Formula Tuning:**
- 1.464^14 ≈ 120s (target reached at edge)
- Steeper curve creates stronger self-regulation
- Logging essential for tuning (distance + both cooldowns)

---

> **Session 8 Complete** - Chat integration polished, cooldowns refined
> **Status:** Bot operational, commands working, ready for code review
> **Philosophy:** Fail-fast configuration, self-regulating mechanics
