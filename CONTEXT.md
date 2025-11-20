# Selection Protocol - Development Context

**Origin:** Twitch chat conversation + Claude Code session (2025-11-20)
**Parent Project:** `bibites-prediction` (ecosystem analysis tools)
**Status:** Spinoff project for democratic evolution streaming

---

## What Happened Before This Repo

### The Bibites Analysis Project
Original project focused on:
- Ecosystem dynamics analysis
- Population tracking and neural architecture studies
- Evolutionary tracking across 490+ save files
- Python tooling for .bb8 file analysis

### The Streaming Idea
Emerged from Claude chat discussion:
- "Twitch Plays God" concept for The Bibites
- Binary democracy: Kill vs Reproduce
- Evolved into K/L/X three-vote system
- **Key innovation:** Lineage naming rights for engagement

### Rapid Prototyping Session
Built in single Claude Code session (Nov 19-20, 2025):
- Full-page overlay with black background (OBS "lighten" blend)
- Admin control panel with cooldown system
- xdotool keypress automation (Del/Ins/Ctrl+G/O/R/KP+/-)
- WebSocket state synchronization
- Camera auto-follow integration

**Result:** Live stream operational, awaiting Twitch chat integration

---

## Key Design Decisions

### Why "Selection Protocol"?
- Double meaning: Natural + Artificial selection
- "Protocol" = systematic, scientific, experimental
- Clean aesthetic fit (terminal/cyberpunk)
- Not game-specific (scalable concept)
- Avoids generic "Twitch Plays" branding

### Why K/L/X Not K/I?
- K = Kill (Delete key)
- L = Lay egg (Insert key - Del/Ins paired keys)
- X = Extend (do nothing, keep watching)
- Three options > binary for strategic depth

### Why First-L Naming Rights?
- Rewards early commitment
- Creates tension (can lose claim by switching)
- Simple, deterministic (no complex weighting)
- Tie-break drama (single hero steals lineage)

### Why Cooldowns?
- Prevents spam/chaos
- Admin testing validated timing
- Shared cooldowns for related actions
- Individual cooldowns for independent actions
- Creates strategic resource management

---

## Technical Decisions

### Linux + xdotool
- Reliable keypress automation
- The Bibites runs via Steam/Proton
- Window targeting by ID (132120577)
- Zero input lag observed

### Full-Page Black Background
- OBS "lighten" blend mode as alpha
- Clean compositing without alpha channels
- Easy cropping (admin panel left, overlay right)
- Terminal aesthetic matches branding

### Flask + SocketIO
- Real-time WebSocket updates
- Admin panel ↔ Overlay state sync
- Easy to extend for Twitch bot integration
- Proven working in prototype

### Game's Built-in Tag System
- Perfect for lineage inheritance
- Tags propagate automatically to offspring
- No save file hacking required
- Just apply tag before Insert keypress

---

## What Works Right Now

### Infrastructure (100% Operational)
```
✅ Overlay server (Flask + SocketIO)
✅ Admin control panel (left sidebar, 300px)
✅ Keypress automation (xdotool)
✅ Cooldown system (15s primary, 10s camera, 5s zoom, 30s extend)
✅ Camera auto-follow (random mode active)
✅ WebSocket state sync
✅ OBS stream live
✅ Full-page black background for compositing
```

### Admin Controls (All Tested)
```
Game Actions:
- Delete (Kill) ✅
- Insert (Lay) ✅
- x (Extend) ✅

Camera Modes:
- Ctrl+G (Generation) ✅
- Ctrl+O (Oldest) ✅
- Ctrl+R (Random) ✅

Zoom:
- KP+ (Zoom In) ✅
- KP- (Zoom Out) ✅

Timer Controls:
- Pause/Resume ✅
- Reset ✅
- Manual Trigger ✅
```

### What's Missing
```
❌ Twitch IRC bot (TwitchIO)
❌ Vote counting system
❌ Vote resolution logic
❌ Automated execution from votes
❌ Lineage tagging automation
❌ Vote display in overlay
❌ Chat commands (!lineage, !stats)
```

---

## The Voting Mechanics (Finalized)

### Rules
1. **One person, one vote** - Latest replaces previous
2. **First L gets naming rights** - Until they switch away
3. **Ties trigger tie-break window** - 10s for single L to steal lineage
4. **Empty stream = extend** - Natural selection continues
5. **Single voter = god** - 100% power regardless of population

### Why This Is Elegant
- No vote weight manipulation
- No complex algorithms
- Deterministic outcomes
- Strategic depth (when to commit vs wait)
- Scales from 1 to infinite viewers
- Empty stream isn't "broken" - just autonomous

---

## The Lineage System

### How It Works
1. Vote window ends, L wins majority
2. Identify first L voter (by timestamp)
3. Tag parent bibite with username **before** Insert keypress
4. Game's inheritance system handles rest automatically
5. Tag propagates to:
   - Egg being laid right now
   - All future eggs from that parent
   - All descendants recursively

### Why This Creates Engagement
- Personal investment ("my lineage!")
- Competitive dynamics (whose dynasty dominates?)
- Accountability (did your vote help or hurt?)
- Social dynamics (protect allied lineages)
- Natural leaderboard (descendants = success)
- Return visitors (check lineage status)

---

## Code Location (bibites-prediction repo)

### Working Prototype
```
/home/daniel/prj/bibites-prediction/src/tools/twitch_overlay_server.py
```

**This file contains:**
- Full overlay HTML/CSS/JS
- Admin panel UI
- WebSocket handlers for all admin actions
- Cooldown system implementation
- xdotool keypress automation
- Vote state structure (ready for Twitch bot)

**Size:** ~1200 lines (comprehensive but monolithic)

### What Needs Porting
1. **Overlay server** - Port to new repo, modularize
2. **Admin panel** - Keep as testing interface
3. **Cooldown system** - Already working perfectly
4. **WebSocket infrastructure** - Extend for vote display
5. **Keypress automation** - Already tested and reliable

---

## Development Environment

### System Info
- OS: Linux Manjaro
- Python: 3.13 in venv
- Game: The Bibites via Steam/Proton
- Game PID: 1377474
- Window ID: 132120577

### Dependencies (Already Installed in bibites-prediction)
```
flask==3.1.2
flask-socketio==5.5.1
pillow==12.0.0
```

### To Add
```
twitchio>=3.1.0
```

---

## Next Context Handover

The next developer should:

1. **Review this CONTEXT.md** - Understand the journey
2. **Read PROJECT_BRIEF.md** - Get technical specs
3. **Copy working overlay code** - Port from bibites-prediction
4. **Modularize structure** - Break monolith into clean modules
5. **Implement TwitchIO bot** - Phase 1 (vote display only)
6. **Test vote mechanics** - Verify first-L claim logic
7. **Add automated execution** - Phase 2 (votes → keypresses)
8. **Implement lineage tagging** - Phase 3 (dynasties begin)

### Critical Files to Understand
- `PROJECT_BRIEF.md` - Full technical specification
- `twitch_overlay_server.py` (in bibites-prediction) - Working prototype
- `docs/twitch-plays-status.md` (in bibites-prediction) - Development history

### Don't Reinvent
- Cooldown system works perfectly
- Admin panel UI is clean
- xdotool automation is reliable
- WebSocket sync is solid

### Focus On
- TwitchIO integration (the only missing piece)
- Vote manager logic (first-L tracking)
- Overlay vote display section
- Lineage tagging automation

---

## Philosophy

**Process Over Outcomes:**
- Build systematic methodologies
- Create reproducible frameworks
- Document the "how" not just the "what"
- Tools that generate insights

**Democracy At Any Scale:**
- Works with 1 or 1000 viewers
- Empty stream isn't broken
- Single voter has full power
- Pure equality regardless of population

**Scientific Experiment:**
- Depersonalized presentation
- Terminal/data aesthetic
- Transparent mechanics
- Community as participants, not audience

**Let Them Find It:**
- No marketing blitz
- Organic discovery
- Word of mouth
- Build something worth discovering

---

> CONTEXT ESTABLISHED
> FOUNDATION SOLID
> DEMOCRACY AWAITS

🔥

---

**Created:** 2025-11-20
**By:** Claude (Sonnet 4.5) + Daniel
**Session:** bibites-prediction → selection-protocol spinoff
