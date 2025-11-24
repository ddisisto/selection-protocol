# Selection Protocol - Session 6 Handover

**Date:** 2025-11-22
**Phase:** Phase 1 Complete - Live Testing Phase
**Status:** System operational, ready for real-world testing

---

## Current State

**Phase 1: Complete ✅**
- Overlay server (Flask + SocketIO)
- TwitchIO EventSub bot
- Vote tracking system (k/l/x + first-L claimant)
- Dynamic timer (30-120s, entropy-based)
- Admin panel with vote injection
- Window auto-discovery
- CSS design system
- End-to-end vote flow operational

**What's Working:**
```
Twitch Chat → EventSub Bot → SocketIO → Flask → Vote Manager
                                                      ↓
                                         Broadcasts vote_update
                                                      ↓
                              Overlay Display + Admin Panel
                                                      ↓
                                         game_controller.py → xdotool
                                                      ↓
                                         The Bibites (auto-discovered window)
```

**Architecture Highlights:**
- **Window Auto-Discovery:** Finds "The Bibites" at startup, fails fast if not found
- **Elapsed-Time Timer:** Bounded 30-120s, immune to vote-based delay exploits
- **CSS Design System:** 3-tier structure (base/admin/overlay), DRY tokens
- **Admin Testing:** Vote injection (+/-), force execution (K/L/X), live state display
- **First-L Claim Logic:** Tracks first L voter per round, lineage naming rights

---

## Session 6 Progress

**Actual Work (pivoted from planned priorities):**

### Chat Commands & Self-Regulating Game State ✅
Implemented from [docs/IDEAS.md](docs/IDEAS.md) "Commands" task:
- **Chat commands:** +/- (zoom), 1/2/3/4 (info panels), h/s (hide/show UI)
- **Self-regulating system:** Dynamic cooldowns based on distance from equilibrium
- **Zoom tracking:** ±50 range, 1-120s cooldown scaling exponentially with distance
- **Info panels:** 15s cooldown, rejects selecting current panel (prevents toggle)
- **State tracking:** Full metadata (current/previous, user, cause, rejected count)
- **Branch:** Overlay UI → `feature/game-state-overlay-ui` (needs polish)

**Files:**
- `src/game_state.py` - Core system (CommandGroup, ZoomTracker, StatefulToggle)
- `src/game_commands.py` - Command registry (added 's' show UI)
- `src/websocket.py` - Validation, cooldown enforcement, rejection logging
- `src/twitch_bot.py` - Parse h/s, emit game_command events
- `src/vote_manager.py` - Added round_start event (supports future CTA)

**Testing:** Continuous live end-to-end testing throughout session

**Commits:**
- `73739cc` - Add chat commands for game controls
- `465dacd` - Implement self-regulating game state system

### Documentation Review & Alignment ✅
**Updated:**
- **README.md** - Phase 1 status complete, added game commands, updated mechanics
- **PROJECT_BRIEF.md** - Removed outdated info, added game commands section, updated architecture

---

## Original Session 6 Priorities

~~Priority 1: Documentation Review~~ → Completing now
~~Priority 2: Live Testing~~ → Validated throughout (user testing every step)
~~Priority 3: Polish & Quality~~ → UI branched, deferred to Session 7

---

## System Overview

### Core Components

**Server Side:**
- `src/server.py` - Flask app, main entry point
- `src/websocket.py` - SocketIO event handlers
- `src/vote_manager.py` - Vote tracking, timer, first-L logic
- `src/game_controller.py` - xdotool automation, window discovery
- `src/twitch_bot.py` - EventSub integration
- `src/oauth_flow.py` - Token management
- `src/actions.py` - Action registry
- `src/cooldowns.py` - Cooldown system (not used in admin panel)
- `src/config.py` - Configuration

**Client Side:**
- `src/templates/base.html` - Layout
- `src/templates/overlay.html` - Vote display overlay
- `src/templates/admin_panel.html` - Admin controls (left sidebar)
- `src/static/base.css` - Design tokens, utilities, shared components
- `src/static/overlay.css` - Overlay-specific styles
- `src/static/admin.css` - Admin panel styles
- `src/static/overlay.js` - Overlay display logic
- `src/static/admin.js` - Admin panel interactions

### Running the System

**Terminal 1: Overlay Server**
```bash
source .venv/bin/activate
python -m src.server
# → http://localhost:5000
# Auto-discovers game window at startup
```

**Terminal 2: Twitch Bot**
```bash
source .venv/bin/activate
python -m src.twitch_bot --test  # 30s test mode
python -m src.twitch_bot          # daemon mode
```

**Browser:**
- Overlay: http://localhost:5000/overlay
- Admin Panel: http://localhost:5000 (left sidebar)

### Key Mechanics

**Vote System:**
- One person, one vote (latest replaces previous)
- k = Kill (Delete key), l = Lay egg (Insert key), x = Extend (do nothing)
- First L voter gets naming claim, loses if they switch away

**Timer System:**
- Base: 30s minimum
- Extended by vote entropy (Shannon entropy formula)
- Maximum: 120s total round duration
- Elapsed-time based (immune to delay exploits)
- Formula: `30 + (entropy × 90)`

**Admin Panel:**
- **Vote Injection:** +/- buttons add/remove test votes with random usernames
- **Force Execution:** K/L/X buttons execute immediately (bypass timer)
- **Camera Controls:** Direct keypress (no cooldowns)
- **Live State:** Real-time vote counts, timer, first-L claimant

**Window Targeting:**
- Auto-discovers "The Bibites" window at server startup
- Fails fast if not found or multiple windows
- xdotool delivers keypresses via window ID

---

## Recent Changes (Session 5)

**Major Achievements:**
1. **CSS Design System** - Extracted 600+ lines inline CSS → DRY token system
2. **Admin Panel Refactor** - Testing-focused 3x3 grid interface
3. **Window Auto-Discovery** - Fail-fast validation, no hardcoded IDs
4. **Timer System Fixes** - Extension bug, "VOTE NOW!" display, elapsed-time system

**Commits:**
- CSS refactor (design system)
- Admin panel refactor (vote injection)
- Window auto-discovery
- Cooldown removal from admin panel
- Timer extension fix + "VOTE NOW!" display
- Elapsed-time timer system

---

## Known Gotchas

**Window Discovery:**
- Game must be running before starting server
- Server will exit with clear error if window not found
- Window ID can change on game restart (auto-discovery handles this)

**First-L Claim Logic:**
- User votes L → gets claim
- User switches to K/X → loses claim to next L voter
- Multiple L voters → only first by timestamp has claim
- Test with multiple accounts before trusting

**Timer System:**
- Bounded 30-120s total (immune to delay exploits)
- Empty stream defaults to 30s (no votes = minimum timer)
- Displays "VOTE NOW!" when timer inactive (white, 36px)
- Countdown shown in accent color (green/yellow/red), 54px

**OAuth Tokens:**
- Cached in `.twitch_token` (gitignored)
- Auto-refreshes every 4 hours
- Bot must be authorized by channel owner
- Scopes: `chat:read`, `chat:edit`, `user:read:chat`, `user:write:chat`, `user:bot`, `channel:bot`

**Admin Panel:**
- No cooldowns (immediate execution)
- Vote injection creates test_XXXXXX usernames
- Force execution bypasses timer entirely
- Camera controls are direct keypresses

---

## Documentation Structure

For complete context, see:
- **[CLAUDE.md](CLAUDE.md)** - Workflows, patterns, methodologies (START HERE)
- **[README.md](README.md)** - Project overview & quick start
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** - Full technical spec
- **[CONTEXT.md](CONTEXT.md)** - Design philosophy
- **[VOTING_RULES.md](VOTING_RULES.md)** - Vote mechanics reference
- **[docs/archive/](docs/archive/)** - Historical handovers (Sessions 0-5)

---

## Session 6 Wrap-Up

**Completed:**
- ✅ Game commands system (+/-/1-4/h/s) with chat integration
- ✅ Self-regulating cooldown system (distance-based, prevents extremes)
- ✅ State tracking (metadata for tuning/feedback)
- ✅ round_start event (supports future CTA features)
- ✅ Documentation review (README.md, PROJECT_BRIEF.md updated)

**Deferred to Session 7:**
- Overlay UI polish (branched to `feature/game-state-overlay-ui`)
- Layout/spacing/sizing for game state widgets
- Design discussions for visual feedback

**Branch Status:**
- **main:** Clean, functional backend ready for parallel work
- **feature/game-state-overlay-ui:** UI work in progress

**Key Insights:**
- Self-regulating systems create complexity potential (edge of chaos)
- Transparency teaches system dynamics (viewers see cooldowns scale)
- Live testing throughout ensures operational code

---

## Next Session (7) Priorities

1. **Design discussion:** Overlay UI layout, visual feedback for commands
2. **Polish:** Game state indicators (merge feature branch when ready)
3. **Chat announcements:** CTA, round start/end, outcomes (uses round_start event)
4. **Optional:** Lineage tagging preparation (Phase 2 kickoff)

---

> **Session 6 Complete** - Commands operational, system self-regulating
> **Status:** Ready for UI polish + chat announcements
> **Philosophy:** Build systems that resist extremes, create natural equilibrium
