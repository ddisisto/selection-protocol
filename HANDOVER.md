# Selection Protocol - Session 7 Handover

**Date:** 2025-11-24
**Phase:** Phase 1 Complete - Polish & Enhancements
**Status:** Core system operational, UI refinements needed

---

## Quick Orientation

**What We Have:**
- Fully operational voting system (k/l/x)
- Dynamic timer (30-120s, entropy-based, auto-execution)
- Game commands (+/-/1-4/h/s) with self-regulating cooldowns
- TwitchIO EventSub bot (chat → commands/votes)
- Overlay display (votes, timer, first-L claimant)
- Admin panel (testing interface)

**What's Next:**
- Overlay UI polish (game state indicators need layout work)
- Chat announcements (CTA, round events, outcomes)
- Design discussions for visual feedback

**Full Context:**
- @CLAUDE.md - Workflows and patterns (START HERE)
- @README.md - Project overview
- @docs/archive/HANDOVER-SESSION-6.md - Last session's details

---

## Session 7 Priorities

### Priority 1: Design Discussion & UI Polish
**Context:** Game state indicators implemented but need layout/design work

**Branch:** `feature/game-state-overlay-ui` has working widgets:
- Zoom controls (distance display, cooldown timers)
- Info panel grid (2x2, active highlight)
- Real-time SocketIO updates

**Needs:**
- Layout decisions (placement, sizing, spacing)
- Visual feedback polish (animations, colors, states)
- Integration with main overlay design
- Testing with full vote display active

**Tasks:**
1. Design discussion: Where do widgets go? How big? Style consistency?
2. Iterate on layout/spacing/sizing
3. Merge feature branch when polished
4. Test integrated overlay (votes + game state together)

### Priority 2: Chat Announcements (CTA Features)
**Context:** Bot needs outbound messages for engagement

**From [docs/IDEAS.md](docs/IDEAS.md) Task 1:**
- Every minute CTA if no recent votes ("Vote k/l/x to decide fate!")
- Announce when voting opens ("Voting opened by @user: k")
- Announce outcomes ("Round ended: L wins! @firstL claims lineage")

**Implementation Notes:**
- `round_start` event already exists (src/vote_manager.py:186)
- Bot has SocketIO connection to Flask (receives events)
- Need outcome event (round_end with winner/first-L)
- Twitch rate limits: ~20 messages/30s (space announcements appropriately)

### Priority 3: Optional - Lineage Tagging Prep
**If time permits:**
- Plan mouse automation for applying tags (pyautogui? xdotool?)
- Design tag format (username length limits, sanitization)
- Test tagging flow manually
- Not required for Session 7, but good to explore

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
- `src/vote_manager.py` - Votes, timer, execution, round_start event
- `src/game_state.py` - Commands, cooldowns, state tracking
- `src/twitch_bot.py` - EventSub, parses votes + commands
- `src/websocket.py` - SocketIO handlers (votes, commands, events)
- `src/templates/overlay.html` - Vote display
- `src/static/overlay.js` - SocketIO listeners, rendering

**Branches:**
- `main` - Clean, operational backend (current)
- `feature/game-state-overlay-ui` - UI widgets (needs polish)

**Recent Commits:**
```
465dacd - Implement self-regulating game state system
73739cc - Add chat commands for game controls
a83544b - Implement elapsed-time-based timer
```

---

## Testing Checklist

Before going live, verify:
- [ ] Votes from Twitch chat work (k/l/x)
- [ ] Timer counts down correctly (30-120s dynamic)
- [ ] Winner executes (K→Delete, L→Insert, tie→nothing)
- [ ] Game commands work (+/-/1-4/h/s)
- [ ] Cooldowns scale properly (zoom 1-120s, panels 15s)
- [ ] Overlay displays everything (votes, timer, claimant)
- [ ] Admin panel testing tools work (vote injection, force execute)
- [ ] Multiple Twitch users (if possible - edge case testing)

---

## Known Gotchas

**Game Window:**
- Must be running before server starts (auto-discovery)
- Server exits with error if not found (fail-fast)

**Twitch Bot:**
- Separate process from server (2 terminals)
- Requires OAuth flow first time (browser opens)
- Token cached in `.twitch_token` (auto-refresh)

**UI Feature Branch:**
- Don't merge until design discussion complete
- Overlay needs layout decisions before polish
- Main branch is clean for parallel work

**Self-Regulating Cooldowns:**
- Zoom cooldown scales with distance (1-120s)
- Info panels reject current selection (prevents toggle)
- UI commands (h/s) reject redundant state (h when hidden)

---

## Session 7 Success Criteria

**Minimum:**
- UI polish discussion complete (decisions made)
- Feature branch merged OR clear plan for merge

**Ideal:**
- Overlay UI polished and merged
- Chat announcements implemented (CTA + round events)
- Full end-to-end test with complete system

**Stretch:**
- Lineage tagging exploration
- Multi-user testing scenarios

---

## Documentation Structure

For complete context:
- **[CLAUDE.md](CLAUDE.md)** - Workflows, patterns, start here
- **[README.md](README.md)** - Project overview
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** - Technical spec
- **[CONTEXT.md](CONTEXT.md)** - Design philosophy
- **[VOTING_RULES.md](docs/VOTING_RULES.md)** - Vote mechanics
- **[docs/archive/](docs/archive/)** - Historical handovers (0-6)

---

> **Session 7 Starting Point** - Core complete, polish time
> **Focus:** Design, visual feedback, chat engagement
> **Philosophy:** Transparency teaches dynamics, self-regulation creates equilibrium
