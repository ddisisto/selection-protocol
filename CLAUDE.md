# CLAUDE.md - AI Assistant Handover

**Purpose:** Fast context load for AI assistants jumping into this codebase.

**Last Updated:** 2025-11-21 (Session 3)
**Current Phase:** Phase 1 (5/6 complete - overlay display needed)

---

## 1. Quick Context Load

**What is this?**
Twitch streaming experiment: chat votes K/L/X (Kill/Lay/Extend) every 60s on organisms in [The Bibites](https://thebibites.com). First L voter claims lineage naming rights if L wins. Democracy meets evolution meets competitive dynasty building.

**Current state:**
- ✅ Full modular codebase in `src/` (10 files, ~2000 lines)
- ✅ Overlay server operational (Flask + SocketIO)
- ✅ Admin panel with xdotool automation working
- ✅ TwitchIO EventSub bot receiving chat messages
- ✅ Vote manager tracking k/l/x votes + first-L claimant logic
- ✅ End-to-end vote flow: chat → bot → Flask → vote_manager
- ❌ Overlay HTML doesn't display votes yet (broadcasts work, display missing)

**Key files:**
- [README.md](README.md) - Project overview & quick start
- [HANDOVER.md](HANDOVER.md) - Current state + next session tasks
- [PROJECT_BRIEF.md](PROJECT_BRIEF.md) - Full technical spec
- [CONTEXT.md](CONTEXT.md) - Design decisions & philosophy
- This file - Your fast-track orientation

---

## 2. Code Architecture (Current State)

```
src/
├── server.py           # Flask app, main entry point (working)
├── overlay.py          # HTML/CSS/JS template (needs vote display update)
├── admin_panel.py      # Left-sidebar admin UI (working)
├── websocket.py        # SocketIO handlers (working)
├── game_controller.py  # xdotool keypress → The Bibites (working)
├── cooldowns.py        # Cooldown enforcement (working)
├── vote_manager.py     # Vote tracking + first-L logic (working)
├── actions.py          # Action registry (k/l/x definitions) (working)
├── twitch_bot.py       # TwitchIO EventSub integration (working)
├── oauth_flow.py       # OAuth authorization + token refresh (working)
└── config.py           # Game configuration (working)
```

**Integration flow (working end-to-end):**
```
Twitch Chat → EventSub Bot → SocketIO → Flask → Vote Manager
                                                      ↓
                                         Broadcasts vote_update
                                                      ↓
                              Overlay (needs HTML) + Admin Panel
                                                      ↓
                                         game_controller.py → xdotool
                                                      ↓
                                         The Bibites (Window ID: 132120577)
```

---

## 3. Current Development State

**Phase 1 Progress: 5/6 Complete**
- ✅ Overlay server (Flask + SocketIO + admin panel)
- ✅ xdotool automation (Linux/Proton tested)
- ✅ OAuth flow (authorization code grant + token refresh)
- ✅ TwitchIO EventSub bot (replaces deprecated IRC)
- ✅ Vote manager (k/l/x tracking, first-L claimant logic)
- ❌ Vote display in overlay (data broadcasts, HTML needs update)

**Phase 2 (Not Started):**
- Automated vote execution (currently manual via admin panel)
- Vote cycle timer (60s cycles)
- Tie-break window (10s after tie detected)

**Phase 3 (Not Started):**
- Lineage tagging system (username → game tag before Insert)

**Phase 4 (Not Started):**
- Community features (!lineage command, leaderboards)

---

## 4. Critical Design Decisions (Don't Change Without Reason)

**Vote mechanics:**
- One person, one vote (latest replaces previous)
- First L voter gets naming claim, loses it if they switch away
- Ties → 10s tie-break window, first L during tie-break steals lineage
- Empty stream = auto-extend (X behavior)

**Why K/L/X not K/I:**
- K = Kill (Delete key), L = Lay egg (Insert key), X = Extend (do nothing)
- Three options create strategic depth vs binary choice
- "L" visually distinct from "I" in chat

**Action registry pattern:**
- Single source of truth in `src/actions.py`
- Bot fetches enabled actions from Flask at startup (DRY)
- Extensible: add new actions without changing bot code
- Each action: name, description, keypress, cooldown, enabled flag

**Cooldown system (battle-tested in prototype):**
- Primary actions (Del/Ins): 15s shared
- Camera modes: 10s shared
- Zoom: 5s individual
- Extend: 30s cooldown (Phase 2)

**Window targeting (Linux/Proton specific):**
- Window ID: `132120577` (confirmed working)
- PID: `1377474`
- xdotool delivers keypresses with zero lag

**EventSub over IRC:**
- IRC deprecated by Twitch (as of 2024)
- EventSub is official, stable, cleaner JSON payloads
- Requires OAuth user access tokens (not client credentials)

**Philosophy:**
- Process over outcomes (build systems, not one-offs)
- Democracy at any scale (1 viewer or 1000)
- Scientific experiment aesthetic (terminal/data presentation)
- Organic discovery (no marketing blitz)

---

## 5. Common Tasks

### First-Time Setup
```bash
# Clone and setup
cd selection-protocol
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure Twitch OAuth (first time only)
cp config.yaml.example config.yaml
# Edit config.yaml with your Twitch app credentials from:
# https://dev.twitch.tv/console/apps
```

### Running the System
```bash
# Terminal 1: Overlay server (Flask + admin panel)
source .venv/bin/activate
python -m src.server
# → http://localhost:5000

# Terminal 2: Twitch bot (EventSub)
python -m src.twitch_bot --test  # 30s test mode
python -m src.twitch_bot          # daemon mode

# Browser opens for OAuth authorization on first run
# Token cached to .twitch_token for future runs
```

### Testing Vote Flow
```bash
# With both server and bot running:
# 1. Type "k", "l", or "x" in your Twitch chat
# 2. Bot logs: "username: k" → "VOTE: K"
# 3. Flask logs: "Vote recorded: username → K"
# 4. Vote manager updates counts, tracks first-L claimant
# 5. Overlay receives vote_update broadcast (but doesn't display yet)
```

### Checking Bot Status
```bash
# Bot startup sequence:
# 1. Connects to Flask (exits if Flask not running)
# 2. Fetches enabled actions from Flask (k/l/x)
# 3. Connects to Twitch EventSub
# 4. Announces to chat: "Selection Protocol online..."
# 5. Receives votes → sends to Flask → vote_manager tracks

# Admin panel shows bot status:
# - Twitch Bot: Active (green) / Inactive (gray)
```

---

## 6. Gotchas & Pitfalls

### Linux/Proton Quirks
- The Bibites runs via Steam/Proton (Wine layer)
- Window ID can change on game restart (check with `xdotool search --name "The Bibites"`)
- xdotool requires window focus, game stays focused during stream

### First-L Claim Logic (Subtle)
```
User votes L → gets claim
User changes to K or X → loses claim to next L voter
User changes from K to L → gets claim if no current claimant
Multiple L voters → only first by timestamp has claim

Test this with multiple accounts before trusting it!
```

### OAuth Token Management
- Token stored in `.twitch_token` (gitignored, don't commit)
- Scopes needed: `chat:read`, `chat:edit`, `user:read:chat`, `user:write:chat`, `user:bot`, `channel:bot`
- Bot username must match token owner
- OAuth flow opens browser on first run (one-time authorization)
- Token refresh automatic (expires every 4 hours, refreshes transparently)

### EventSub Connection
- Bot requires Flask running first (enforced in startup sequence)
- EventSub WebSocket can disconnect (reconnect logic needed for Phase 2)
- Messages received reliably in testing (0 missed votes over 30 min test)

### Empty Stream Handling
- Zero votes ≠ error condition
- Default to X (extend) and keep going
- System works autonomously without viewers

### Vote Manager State
- Currently in-memory only (resets on Flask restart)
- Persistence to SQLite planned for Phase 2
- Vote history not tracked (only current cycle)

---

## 7. Project History (3 Sessions)

**Session 0 (Documentation):**
- Created PROJECT_BRIEF, CONTEXT, initial handovers
- Defined K/L/X mechanics, first-L naming rights system
- Established philosophy and design principles

**Session 1 (Foundation):**
- Ported and modularized overlay server from prototype
- Implemented OAuth authorization code grant flow
- Discovered IRC deprecation → EventSub required
- 4 commits, ~1200 lines of working code

**Session 2 (Integration):**
- Rewrote bot from IRC to EventSub
- Built action registry (extensible DRY system)
- Implemented vote manager + first-L claimant logic
- Connected bot ↔ Flask via SocketIO
- End-to-end vote flow operational
- 7 commits, massive progress

**Session 3 (Current):**
- Documentation consolidation (you are here)
- Next: Overlay display + vote cycles

---

## 8. Next Session TODO

See [HANDOVER.md](HANDOVER.md) for detailed next steps.

**Priority 1: Complete Phase 1 (1-2 hours)**
- Update `src/overlay.py` HTML to display vote counts
- Wire `vote_update` SocketIO events to display
- Test end-to-end: chat → overlay

**Priority 2: Vote Cycle Management (1-2 hours)**
- Add 60s timer to vote_manager
- Auto-reset votes after cycle
- Broadcast timer countdown to overlay

**Priority 3: Manual Vote Resolution (30 mins)**
- Admin button to "resolve vote now"
- Display winner in Flask logs
- Log first-L claimant when L wins

**Priority 4: Testing & Polish (30 mins)**
- Multi-user testing (alt accounts)
- Edge cases: ties, all X, empty stream
- Clean up logging output

---

## 9. Context Handover Protocol

**When you finish a session:**
1. Update [HANDOVER.md](HANDOVER.md) with current state
2. Note any gotchas discovered
3. Clean git history, meaningful commits
4. Update "Last Updated" timestamp in this file
5. Archive current HANDOVER.md to `docs/archive/HANDOVER-SESSION-N.md`

**When you start a session:**
1. Read this file first (you are here)
2. Read [HANDOVER.md](HANDOVER.md) for specific next tasks
3. Skim [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for mechanics
4. Check recent git log for context
5. Read [CONTEXT.md](CONTEXT.md) if design decisions unclear

**Historical handovers:** See `docs/archive/` for Sessions 0-2

---

## 10. Quick Reference

**Test the system:**
```bash
python -m src.server           # Terminal 1
python -m src.twitch_bot --test  # Terminal 2
# Type "k" in Twitch chat → check Flask logs
```

**Key files to modify for Phase 1:**
- `src/overlay.py` - Add vote display HTML/CSS/JS
- `src/vote_manager.py` - Add cycle timer (Phase 2)

**Key files to understand:**
- `src/actions.py` - How k/l/x are defined
- `src/vote_manager.py` - Vote tracking + first-L logic
- `src/twitch_bot.py` - EventSub integration
- `src/websocket.py` - SocketIO event handlers

**Documentation structure:**
1. **README.md** - Quick "what is this?" (2 min)
2. **CLAUDE.md** - Fast context load (5 min) ← you are here
3. **HANDOVER.md** - Current state + next steps (10 min)
4. **PROJECT_BRIEF.md** - Full technical spec (30 min)
5. **CONTEXT.md** - Design philosophy (20 min)

---

> CLAUDE.md UPDATED FOR SESSION 3
> PHASE 1: 5/6 COMPLETE
> OVERLAY DISPLAY: NEXT
> DEMOCRACY OPERATIONAL

**Remember:** The hard part (EventSub, OAuth, vote logic) is done. The overlay update is straightforward HTML/CSS/JS. Trust the architecture. Ship it. 🔥
