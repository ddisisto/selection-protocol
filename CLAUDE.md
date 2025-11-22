# CLAUDE.md - AI Assistant Handover & Methodology

**Purpose:** Fast context load + repeatable patterns for working on this codebase.

**Last Updated:** 2025-11-22 (Session 5)
**Sessions Completed:** 5

---

## Quick Orientation

**What is this?**
Twitch streaming experiment where chat votes K/L/X (Kill/Lay/Extend) on organisms in [The Bibites](https://thebibites.com). First L voter claims lineage naming rights. Democracy meets evolution meets competitive dynasty building.

**Current State:**
Phase 1 essentially complete. Dynamic timer (30-120s), automated execution, vote display working. Ready for live testing and polish.

**Full Context:**
@README.md

---

## How to Work on This Project

### Core Values (User's Preferences)

**Fail-Fast Philosophy:**
- Strict validation, clear error messages
- No fallbacks to hardcoded values
- Example: Window auto-discovery fails if count != 1 (not found OR duplicates)
- Better to crash with explanation than silently do wrong thing

**Clean Code:**
- DRY - eliminate duplication aggressively
- Single source of truth
- Extract patterns (action registry, design tokens, etc.)
- Refactor when you see duplication

**Professional Objectivity:**
- Concise communication, no superlatives
- Technical accuracy over validation
- No unnecessary praise or emojis (unless explicitly requested)
- Focus on facts and problem-solving

**Direct & Immediate (Admin Panel):**
- Admin actions should be instant (no cooldowns, no delays)
- It's the admin panel - user has full control
- Cooldowns/delays are for viewer commands, not admin

### Work Patterns That Succeed

**1. Use TodoWrite Proactively**
- Create todos at start of complex tasks
- Mark in_progress when starting
- Complete immediately when done (don't batch)
- Exactly ONE todo in_progress at a time
- Helps track progress, shows user what's happening

**2. Parallel Tool Use**
- When tools are independent, call them in same message
- Example: Read multiple files, run multiple bash commands
- Maximize efficiency, minimize round-trips

**3. Commit Messages (Detailed & Structured)**
```
Title: What changed (imperative, 50 chars)

**Problem:** What issue this solves
**Root Cause:** Why it happened (with file:line references)
**Solution:** How we fixed it
**Implementation:** Key changes (bullet points)
**Testing:** What was verified

Include code snippets showing before/after when useful.

🔥 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

**4. Documentation Workflow**
- End of session: Add summary to HANDOVER.md
- Archive: `HANDOVER.md` → `docs/archive/HANDOVER-SESSION-N.md`
- Create fresh HANDOVER.md for next session
- CLAUDE.md (this file) grows organically, captures patterns

**5. Testing Approach**
- Write code first
- Test manually (user tests while server hot-reloads)
- Iterate based on feedback
- No premature abstraction - wait for patterns to emerge

### Common Gotchas

**Linux/Proton Quirks:**
- The Bibites runs via Steam/Proton (Wine layer)
- Window ID changes on game restart
- Auto-discovery handles this (searches by name)

**Timer System:**
- Elapsed-time based (wall clock immutable)
- `time_remaining = target - elapsed`
- New votes change target, but can't "undo" elapsed time
- Prevents indefinite delay

**First-L Claimant Logic:**
- First L voter by timestamp gets claim
- Switching away from L loses claim
- Switching back to L goes to back of queue (new timestamp)
- Test with multiple accounts before trusting

### User Communication Patterns

**Effective:**
- "I notice X, suspect Y, here's my proposed fix Z"
- "This broke because [root cause], fix is [solution]"
- "Three options: A (simple), B (robust), C (complex). Recommend B because..."

**Ineffective:**
- "Great job!", "Perfect!", excessive enthusiasm
- Long explanations without code/examples
- Vague status updates without specifics

---

## Current Session State

@HANDOVER.md

---

## Vote Mechanics (Locked Specification)

@docs/VOTING_RULES.md

---

## System Architecture

**Key Components:**
- **Flask Server** ([src/server.py](src/server.py)) - Main entry, routes, background timer
- **Vote Manager** ([src/vote_manager.py](src/vote_manager.py)) - Vote tracking, timer logic, execution
- **Game Controller** ([src/game_controller.py](src/game_controller.py)) - Window discovery, xdotool keypresses
- **Twitch Bot** ([src/twitch_bot.py](src/twitch_bot.py)) - EventSub integration, OAuth flow
- **WebSocket** ([src/websocket.py](src/websocket.py)) - SocketIO event handlers
- **Actions** ([src/actions.py](src/actions.py)) - Action registry (DRY)

**Data Flow:**
```
Twitch Chat → EventSub Bot → SocketIO → Flask Server → Vote Manager
                                                             ↓
                                                  Broadcasts vote_update
                                                             ↓
                                            Overlay + Admin Panel (display)
                                                             ↓
                                            Game Controller → xdotool
                                                             ↓
                                            The Bibites (auto-discovered window)
```

**Timer System (Elapsed-Time Based):**
```python
# Round starts:
round_start_time = datetime.now()
target_duration = get_timer_limit(ratios)  # 30-120s via entropy

# Each tick:
elapsed = now() - round_start_time
time_remaining = max(0, target - elapsed)

# New vote:
target_duration = get_timer_limit(new_ratios)  # Target changes
# time_remaining recalculates on next tick (always decreasing)

# Expiry:
if elapsed >= target_duration:
    execute_winner()
```

**Design Patterns:**
- **Server-authoritative:** Zero client-side state (timers, counters)
- **Single source of truth:** Action registry, design tokens (CSS variables)
- **Fail-fast validation:** Window discovery, vote validation, etc.
- **DRY composition:** Templates use @includes, CSS uses custom properties

---

## Philosophy & Design Decisions

@CONTEXT.md

---

## Quick Reference

### Starting the System
```bash
# Terminal 1: Server (requires game running first for window discovery)
source .venv/bin/activate
python -m src.server
# → http://localhost:5000

# Terminal 2: Bot (optional, for Twitch integration)
python -m src.twitch_bot --test  # 30s test
python -m src.twitch_bot          # daemon
```

### Testing Vote Flow
```bash
# Admin panel (left sidebar):
# Click "l+" → adds test vote
# Click "k+" → adds test vote
# Watch timer adjust, overlay update
# Click "L" → force execute Lay (Insert keypress)
```

### File Locations
- **Templates:** `src/templates/*.html`
- **Static assets:** `src/static/*.{js,css}`
- **Docs:** `docs/*.md`
- **Archived handovers:** `docs/archive/HANDOVER-SESSION-*.md`

---

## Growth & Learning

**Session-to-Session Patterns:**

**Session 3:**
- EventSub integration (IRC deprecated)
- Vote manager foundation
- End-to-end vote flow

**Session 4:**
- Server-authoritative refactor
- Shannon entropy timer formula
- Complete Phase 1 implementation

**Session 5:**
- CSS design system (600+ lines → DRY tokens)
- Admin panel refactor (cooldowns removed)
- Window auto-discovery
- Elapsed-time timer (prevent indefinite delay)

**Key Learnings:**
- Start with simplest working solution
- Refactor when duplication becomes obvious
- Test manually before abstracting
- Document decisions when made (CONTEXT.md)
- Fail-fast > silent fallbacks

**What Works:**
- TodoWrite for complex tasks
- Detailed commit messages with context
- Parallel tool use for efficiency
- @includes for documentation (no duplication)
- Archive handovers each session

**Avoid:**
- Premature abstraction
- Hardcoded fallback values
- Client-side state (server-authoritative)
- Cooldowns in admin panel
- Emojis (unless requested)

---

## Next Session Priorities

See current HANDOVER.md for detailed next steps.

Typically involves:
1. Polish from previous session's testing
2. Bug fixes discovered during use
3. New feature implementation
4. Documentation updates

---

## Historical Context

**Previous Sessions:**
See `docs/archive/HANDOVER-SESSION-*.md` for session-by-session history.

**Major Milestones:**
- Session 0: Documentation & planning
- Session 1: OAuth flow, foundation
- Session 2: EventSub bot, vote manager
- Session 3: End-to-end vote flow
- Session 4: Server-authoritative, Phase 1 MVP
- Session 5: Polish, CSS refactor, admin panel, window discovery

---

> "Process over outcomes. Build systems, not one-offs."
> "Democracy at any scale. 1 viewer or 1000."
> "Let them find it. Organic discovery, word of mouth."

**DEMOCRACY ONLINE**
**SELECTION PROTOCOL: OPERATIONAL**
