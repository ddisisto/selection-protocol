# CLAUDE.md - AI Assistant Handover

**Purpose:** Fast context load for AI assistants jumping into this codebase.

**Last Updated:** 2025-11-20
**Current Phase:** Pre-Phase 1 (no src/ code yet, just docs)

---

## 1. Quick Context Load

**What is this?**
Twitch streaming experiment: chat votes K/L/X (Kill/Lay/Extend) every 60s on organisms in [The Bibites](https://thebibites.com). First L voter claims lineage naming rights if L wins. Democracy meets evolution meets competitive dynasty building.

**Current state:**
- Working prototype exists in `../bibites-prediction/src/tools/twitch_overlay_server.py` (~1200 lines)
- Overlay, admin panel, xdotool automation, cooldowns, WebSocket sync - all operational
- This repo: documentation only, awaiting code port + TwitchIO integration

**Key files:**
- [PROJECT_BRIEF.md](PROJECT_BRIEF.md) - Full technical spec
- [CONTEXT.md](CONTEXT.md) - Design decisions & philosophy
- [HANDOVER.md](HANDOVER.md) - Detailed next-step instructions
- This file - Your fast-track orientation

---

## 2. Code Architecture (Target State)

```
src/
├── server.py           # Flask app, main entry point
├── overlay.py          # HTML/CSS/JS template for OBS
├── admin_panel.py      # Left-sidebar admin UI (cropped from stream)
├── websocket.py        # SocketIO handlers (state sync)
├── game_controller.py  # xdotool keypress → The Bibites window
├── cooldowns.py        # Shared cooldown enforcement (15s/10s/5s/30s)
├── vote_manager.py     # Track k/l/x votes, first-L claim logic
├── twitch_bot.py       # TwitchIO IRC integration (MISSING)
└── config.py           # Settings (vote timing, Twitch creds)
```

**Integration flow:**
```
Twitch Chat → TwitchIO Bot → Vote Manager → WebSocket Broadcast
                                                ↓
                              Overlay (display) + Admin Panel (execution)
                                                ↓
                                        game_controller.py → xdotool
                                                ↓
                                        The Bibites (Window ID: 132120577)
```

---

## 3. Current Development State

**Phase 0:** Documentation complete, repo initialized
**Phase 1 (Next):** Port prototype, modularize, add TwitchIO, display votes (no auto-exec)
**Phase 2:** Automated vote execution
**Phase 3:** Lineage tagging system
**Phase 4:** Community features (!lineage, leaderboards)

**What's working in prototype:**
- Full-page black background overlay (OBS "lighten" blend)
- Admin panel: Delete/Insert/x, Ctrl+G/O/R (camera), KP+/- (zoom)
- Cooldown system (shared groups, individual timers)
- WebSocket state sync overlay ↔ admin
- xdotool automation (Linux/Proton tested)

**What's missing:**
- Actual src/ code in this repo (prototype is in `../bibites-prediction/`)
- TwitchIO bot integration
- Vote counting & display
- Automated execution from votes
- Lineage tagging before Insert keypress

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

**Cooldown system (battle-tested, keep as-is):**
- Primary actions (Del/Ins): 15s shared
- Camera modes: 10s shared
- Zoom: 5s individual
- Extend: 30s cooldown

**Window targeting (Linux/Proton specific):**
- Window ID: `132120577`
- PID: `1377474`
- xdotool confirmed working, zero lag observed

**Philosophy:**
- Process over outcomes (build systems, not one-offs)
- Democracy at any scale (1 viewer or 1000)
- Scientific experiment aesthetic (terminal/data presentation)
- Organic discovery (no marketing blitz)

---

## 5. Common Tasks

**Setup (first time):**
```bash
# From project root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run overlay server (when implemented):**
```bash
source .venv/bin/activate
python -m src.server
# Open http://localhost:5000
```

**Study working prototype:**
```bash
# Read the monolith that works
cat ../bibites-prediction/src/tools/twitch_overlay_server.py

# Key sections:
# - Lines ~50-200: Cooldown system
# - Lines ~200-600: WebSocket handlers
# - Lines ~600-1000: HTML/CSS overlay + admin
# - Lines ~1000-1200: Client-side JavaScript
```

**Testing Phase 1 (vote display):**
1. Start overlay server
2. Start Twitch bot (needs OAuth token from https://twitchapps.com/tmi/)
3. Type k/l/x in your Twitch chat
4. Verify counts update in overlay
5. Test first-L claim logic with multiple votes

**Git workflow:**
```bash
# Commit often, clear messages
git add src/
git commit -m "Implement vote manager with first-L tracking"

# Reference the philosophy
# - Commits should tell a story
# - Clean history > squashing everything
```

---

## 6. Gotchas & Pitfalls

**Linux/Proton quirks:**
- The Bibites runs via Steam/Proton (Wine layer)
- Window ID can change on game restart (check with `xdotool search --name "The Bibites"`)
- xdotool requires window focus, but game stays focused during stream

**First-L claim logic (subtle):**
- User votes L → gets claim
- User changes to K or X → loses claim to next L voter
- User changes from K to L → gets claim if no current claimant
- Multiple L voters → only first by timestamp has claim
- Test this with multiple accounts before trusting it

**WebSocket state sync:**
- Overlay and admin panel share state via SocketIO
- Vote manager must broadcast to both on every update
- Don't break the existing admin panel when adding vote display

**Empty stream handling:**
- Zero votes ≠ error condition
- Default to X (extend) and keep going
- System works autonomously without viewers

**Twitch OAuth:**
- Token stored in config (don't commit)
- Scope needed: `chat:read`
- Bot username can be your main account or separate bot account

**Code porting:**
- Don't rewrite what works (cooldowns, xdotool, WebSocket)
- Modularize the monolith, don't reinvent it
- Keep the admin panel functional during Phase 1 (manual testing)

---

## Context Handover Protocol

**When you finish a session:**
1. Update this section with current phase/state
2. Note any gotchas you discovered
3. Update HANDOVER.md with specific next steps
4. Clean git history, meaningful commits
5. Update "Last Updated" timestamp at top

**When you start a session:**
1. Read this file first (you are here)
2. Skim PROJECT_BRIEF.md for mechanics
3. Check HANDOVER.md for specific tasks
4. Read recent git log for context
5. Review the prototype in `../bibites-prediction/src/tools/twitch_overlay_server.py`

---

## Next Session TODO (Session starting 2025-11-20)

See discussion with Daniel about planning next N commits.

---

> CLAUDE.md INITIALIZED
> CONTEXT TRANSFER: ENABLED
> NEXT AI: YOU'VE GOT THIS

**Remember:** The hard part (overlay, admin, game integration) is done in the prototype. You're just organizing it and adding the final layer (TwitchIO). Trust the design. Ship it. 🔥
