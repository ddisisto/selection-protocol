# CLAUDE.md - Project Methodology

**Purpose:** Fast context load + repeatable patterns for working on this codebase.

---

## Quick Orientation

**What is this?**
Twitch streaming experiment where chat votes K/L/X (Kill/Lay/Extend) on organisms in [The Bibites](https://thebibites.com). First L voter claims lineage naming rights. Democracy meets evolution meets competitive dynasty building.

**Current State:**
@README.md

---

## Issue-Driven Workflow

**All work starts with an issue. All commits reference an issue.**

See @CONTRIBUTING.md for full workflow standards:
- Issue creation principles (explanatory over prescriptive, scope boundaries)
- Commit format (minimal, traceable)
- Session flow (issue → implement → close)

**Quick reference:**
- Point at single issue to start session
- Issue scope = session scope
- Block early and often - create dependency chains
- Commits: `Title (#N)` + optional context + `Closes #N`

---

## Core Values

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

---

## Work Patterns That Succeed

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

**3. Commit Messages (Minimal & Traceable)**
```
Brief description of change (#N)

[Optional 1-2 sentence context if title unclear]

Closes #N (if this commit completes the issue)
```

**Rationale:** Code details belong in code, discussion in issues, commits link the two.

See @CONTRIBUTING.md for full commit standards and examples.

**4. Testing Approach**
- Write code first
- Test manually (user tests while server hot-reloads)
- Iterate based on feedback
- No premature abstraction - wait for patterns to emerge

**5. Agent-Driven Workflow (Optional)**
- For complex, well-scoped work with deep alignment established
- See [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md) for full pattern
- Main session coordinates, agents execute implementation
- Use when: 3+ files, clear scope, context budget >60%
- Don't use when: trivial task, fuzzy exploration, `needs-discussion` active

---

## User Communication Patterns

**Effective:**
- "I notice X, suspect Y, here's my proposed fix Z"
- "This broke because [root cause], fix is [solution]"
- "Three options: A (simple), B (robust), C (complex). Recommend B because..."

**Ineffective:**
- "Great job!", "Perfect!", excessive enthusiasm
- Long explanations without code/examples
- Vague status updates without specifics

---

## System Architecture

**Python Layer:**
- **Flask Server** ([src/server.py](src/server.py)) - Main entry, routes, background timer
- **Vote Manager** ([src/vote_manager.py](src/vote_manager.py)) - Vote tracking, timer logic, execution
- **Mod Client** ([src/mod_client.py](src/mod_client.py)) - HTTP client for BepInEx mod API
- **Game State** ([src/game_state.py](src/game_state.py)) - Command cooldowns, context managers
- **Twitch Bot** ([src/twitch_bot.py](src/twitch_bot.py)) - EventSub integration, OAuth flow
- **WebSocket** ([src/websocket.py](src/websocket.py)) - SocketIO event handlers
- **Actions** ([src/actions.py](src/actions.py)) - Action registry (DRY)

**C# Layer (BepInEx Mod):**
- **GameController.cs** - Unity API interface (kill, lay, zoom, panels)
- **ApiHandlers.cs** - HTTP request handlers
- **HttpApi.cs** - HTTP server (localhost:5001)
- **CommandQueue** - Thread-safe command queue (background → Unity thread)

**Data Flow:**
```
Twitch Chat → EventSub Bot → SocketIO → Flask Server → Vote Manager
                                                             ↓
                                                  Broadcasts vote_update
                                                             ↓
                                            Overlay + Admin Panel (display)
                                                             ↓
                                                       Mod Client (HTTP)
                                                             ↓
                                            BepInEx Mod API (localhost:5001)
                                                             ↓
                                            The Bibites (Unity game)
```

**Design Patterns:**
- **Server-authoritative:** Zero client-side state (timers, counters)
- **Single source of truth:** Action registry, design tokens (CSS variables)
- **Fail-fast validation:** Mod API connection, vote validation, window discovery
- **DRY composition:** Templates use @includes, CSS uses custom properties
- **Threading isolation:** HTTP (background) → CommandQueue → Unity (main thread)

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

### File Locations
- **Templates:** `src/templates/*.html`
- **Static assets:** `src/static/*.{js,css}`
- **Docs:** `docs/*.md`
- **Issues:** Track via `gh issue list` or GitHub web

---

## Key Learnings

**What Works:**
- Start with simplest working solution, refactor when duplication obvious
- Test manually before abstracting
- TodoWrite for complex tasks, parallel tool use for efficiency
- Minimal commit messages linked to issues (reasoning in issues, not commits)
- Document decisions when made (issues, not commit bodies)
- Fail-fast validation > silent fallbacks

**Avoid:**
- Premature abstraction
- Hardcoded fallback values
- Client-side state (server-authoritative)
- Scope creep (create separate issues)
- Cooldowns in admin panel
- Emojis (unless requested)

---

> "Process over outcomes. Build systems, not one-offs."
> "Democracy at any scale. 1 viewer or 1000."
> "Let them find it. Organic discovery, word of mouth."

**DEMOCRACY ONLINE**
**SELECTION PROTOCOL: OPERATIONAL**
