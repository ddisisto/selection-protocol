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

## Session 6 Priorities

### Priority 1: Documentation Review & Alignment
**User Request:** "review PROJECT_BRIEF and README"

Tasks:
1. Review [README.md](README.md) - align with current Phase 1 complete state
2. Review [PROJECT_BRIEF.md](PROJECT_BRIEF.md) - update mechanics, remove outdated info
3. Consolidate/update any other docs as needed

### Priority 2: Live Testing Preparation
With Phase 1 complete, system is ready for real Twitch testing:
1. End-to-end test with actual Twitch chat
2. Multi-user voting scenarios
3. Edge cases: ties, empty stream, rapid vote changes
4. Performance under load

### Priority 3: Polish & Quality
Based on testing feedback:
1. UI/UX improvements
2. Error handling edge cases
3. Logging clarity
4. Performance optimization

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

## Next Session Start Checklist

1. Read [CLAUDE.md](CLAUDE.md) for workflows and patterns
2. Read this HANDOVER.md for current state
3. Check recent git log for context
4. Review Priority 1 tasks (documentation alignment)
5. Run system locally to verify operational state

---

> **Phase 1 Complete** - System operational, democracy functional
> **Next:** Documentation alignment, live testing, polish
> **Status:** Ready for real-world Twitch deployment
