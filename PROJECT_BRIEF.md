# Selection Protocol - Project Brief

**Status:** Phase 1 Complete - System Operational
**Date:** 2025-11-24 (updated Session 6)

---

## Core Concept

**Democratic artificial selection experiment using The Bibites.**

Chat votes every ~60 seconds on three actions for the currently auto-followed bibite:
- **K** (Kill) - Delete key
- **L** (Lay) - Insert key
- **X** (Extend) - Do nothing, keep watching

**The hook:** Winning L voters claim lineage naming rights. Their username tags the parent bibite, inheriting to all future offspring through the game's built-in tag system.

---

## Current State (What Exists)

### ✅ Operational Infrastructure

**Core System:**
- **The Bibites** simulation via Steam/Proton (window auto-discovered at startup)
- **Flask overlay server** with full-page black background (OBS "lighten" blend mode)
- **TwitchIO EventSub bot** - Receives chat, parses votes + commands
- **OAuth authorization flow** - Token caching, auto-refresh
- **WebSocket state sync** - Real-time updates (overlay ↔ admin ↔ bot)
- **xdotool keypress automation** - Window targeting, fail-fast validation

**Voting System:**
- **Vote manager** - Tracks k/l/x votes, first-L claimant logic
- **Dynamic timer** - 30-120s based on Shannon entropy of vote ratios
- **Elapsed-time tracking** - Immune to delay exploits, bounded duration
- **Automated execution** - Timer expiry → winner determination → keypress
- **Overlay display** - Real-time counts, timer countdown, first-L claimant

**Game Commands (Chat → Direct Execution):**
- **Zoom** (`+`/`-`) - Self-regulating cooldowns (1-120s based on distance ±50)
- **Info Panels** (`1`/`2`/`3`/`4`) - 15s cooldown, rejects current panel (prevents toggle)
- **UI Visibility** (`h`/`s`) - Explicit hide/show, 2s cooldown, state tracking
- **Game State** - Tracks metadata (current/previous, user, cause, rejections)

**Admin Panel:**
- **Vote injection** - Add/remove test votes for testing
- **Force execution** - K/L/X immediate override (no cooldowns)
- **Camera controls** - Direct keypresses (no cooldowns)
- **Live state display** - Vote counts, timer, first-L claimant, action log

### 📅 Planned (Phase 2+)
- Lineage tagging system (username → parent before Insert keypress)
- Overlay UI polish (game state indicators branched, needs layout work)
- Chat announcements (CTA, round start/end, outcome notifications)
- Community commands (!lineage, !stats)
- Vote history persistence (SQLite)

---

## Vote Mechanics (Final Design)

### The Three-Command System

**Commands:**
- `k` = Kill current bibite (Delete key)
- `l` = Lay egg, reproduce (Insert key)
- `x` = Extend, do nothing (keep watching)

### Resolution Rules

**One person, one vote:**
- Latest vote replaces previous (no weight accumulation)
- Vote changes allowed anytime during window
- Empty stream = auto-extend (X behavior)
- Single voter = 100% power

**Lineage Naming Rights:**
1. **First L voter** gets claim (by timestamp)
2. **Switching away from L** forfeits claim to next L voter
3. **Claim is live/contested** until window closes
4. **If L wins:** First L claimant's username tags parent bibite

**Winner Determination:**
- K wins IF: K > 33% AND K > L
- L wins IF: L > 33% AND L > K
- X wins (no action) IF: Neither K nor L > 33%, OR K = L (tie)
- Tie-break window deferred to Phase 2

### Why This Works

**Strategic depth:**
- Early L commitment = guaranteed naming rights if L wins
- But risk: locked in, can't change without losing claim
- Late L vote = see trends, but someone else has claim
- X votes meaningful: "keep watching this one"

**Engagement hooks:**
- Personal legacy building through lineage tracking
- Competitive dynamics (whose lineage dominates?)
- Accountability (did your vote help or hurt?)
- Tie-break drama (single hero can steal lineage)

**Democracy at any scale:**
- Works with 1 viewer or 1000
- Empty stream = natural selection continues
- Single voter = THE god (not A god)

---

## Game Commands (Direct Control)

**Unlike votes (k/l/x), game commands execute immediately with self-regulating cooldowns.**

### Command Types

**Zoom Control:**
- `+` / `-` - Zoom in/out
- **Self-regulating cooldown:** 1s at center → 120s at limits (±50)
- **Distance tracking:** Current zoom relative to initial state
- **Hard limits:** Rejects at ±50 distance (prevents extreme zoom)
- **Philosophy:** System naturally resists extremes, creates equilibrium at edge of chaos

**Info Panels:**
- `1` / `2` / `3` / `4` - Select game info panel to display
- **15s cooldown** (time to read panel content)
- **Rejects current:** Selecting active panel rejected (prevents unwanted toggle)
- **State tracking:** Current/previous panel, last user, rejection count

**UI Visibility:**
- `h` - Hide UI (clean view of simulation)
- `s` - Show UI (restore interface)
- **Explicit commands:** Not a toggle - must specify intent
- **2s cooldown**
- **State tracking:** Current visibility state, rejects redundant commands

### Self-Regulating Design

**Why dynamic cooldowns:**
- Fixed cooldowns → always maxed or always available (no complexity)
- Dynamic cooldowns → creates tension between viewer desires and system limits
- Distance-based scaling → natural rubber-banding effect
- Viewers learn system dynamics through transparency

**Zoom formula:**
```python
cooldown = 1s + (|distance| / 50) * 119s
# At distance 0: 1 second
# At distance 25: ~60 seconds
# At distance 50: 120 seconds
```

---

## Lineage Inheritance System

**Game Integration:**
The Bibites has built-in tag inheritance - tags applied to parent automatically propagate to:
- The egg being laid RIGHT NOW
- All future eggs from that parent
- All descendants recursively
- Until parent dies or tag is replaced

**Our Implementation:**
1. L wins majority vote
2. Tag first L voter's username to parent bibite **before** Insert keypress
3. Game handles rest automatically
4. Track lineage stats (descendants per username)

**Display Requirements:**
- Current bibite's lineage tag (overlay)
- Population breakdown by username (top 5-10 lineages)
- Lineage events: "user_alice lineage continues!" / "RIP user_bob lineage - 47 generations"
- Leaderboard: most descendants, longest survival, etc.

---

## Technical Architecture

**Vote Flow:**
```
Twitch Chat → EventSub WebSocket → Bot (parse k/l/x)
    ↓
Vote Manager (track votes, first-L claim)
    ↓
Timer (30-120s dynamic, entropy-based)
    ↓
Winner Determination (>33% + majority logic)
    ↓
Keypress Execution (Delete/Insert/nothing)
    ↓
Overlay Updates (vote_update broadcasts)
```

**Game Command Flow:**
```
Twitch Chat → EventSub WebSocket → Bot (parse +/-/1-4/h/s)
    ↓
Game State (validation, cooldown check, state tracking)
    ↓
Accept/Reject Decision
    ↓
If Accepted: Keypress Execution (KP_Add/1/h/etc)
    ↓
Broadcast (game_state_update events)
```

### Integration Points

**Existing admin panel:**
- Already has WebSocket handlers for keypress execution
- `admin_send_keypress(key, cooldown_group)` working
- Cooldown enforcement operational
- Just need to call it from vote resolution

**Game tagging:**
- Use game's tag system (already implemented)
- Apply tag **before** Insert keypress
- Tag persists through inheritance automatically

**Overlay display:**
- Extend current overlay with vote section
- Show: K/L/X counts, countdown timer, first-L claim
- Add: lineage tag display, population stats

---

## Implementation Phases

### Phase 1: Vote Display (No Execution)
**Goal:** Visual vote counter working, manual admin execution

- [x] TwitchIO bot connects to channel (EventSub)
- [x] Parse chat for k/l/x commands
- [x] Track votes per user (latest replaces previous)
- [x] Identify first-L claimant
- [ ] Display vote tally in overlay (vote_manager ready, HTML update needed)
- [ ] Manual testing: Admin executes winner via panel

**Status:** 5/6 complete. Vote tracking fully operational, just needs overlay HTML update.

**Deliverable:** Working vote counter, admin verifies logic before automation

### Phase 2: Automated Execution
**Goal:** Votes automatically trigger admin panel actions

- [ ] Vote resolution logic (majority wins)
- [ ] Tie detection + tie-break window
- [ ] Call admin panel's keypress handlers via WebSocket
- [ ] Confirmation logging
- [ ] Cooldown respect (don't execute if on cooldown)

**Deliverable:** Votes execute K/L/X automatically

### Phase 3: Lineage Tagging
**Goal:** Username dynasties begin forming

- [ ] Tag application to parent bibite (before Insert)
- [ ] Track lineage statistics (descendants per username)
- [ ] Display current bibite's lineage in overlay
- [ ] Lineage event notifications (extinction, milestones)
- [ ] Population breakdown by username

**Deliverable:** Dynasty competition operational

### Phase 4: Community Features
**Goal:** Full engagement loop

- [ ] Chat commands: !lineage (show your descendants)
- [ ] Leaderboard overlay panel
- [ ] Historical stats (hall of fame)
- [ ] Vote history logging
- [ ] Anti-spam/rate limiting per user

**Deliverable:** Complete Selection Protocol experience

---

## Configuration

### Tunable Parameters

**Vote cycle:**
- Duration: 60s (configurable)
- Tie-break window: 10s (configurable)
- Auto-extend on empty: Yes

**Vote mechanics:**
- Changes allowed: Yes (latest replaces)
- First-L claim: Locked until switch away
- Tie default: X (extend)

**Display:**
- Top N lineages shown: 5-10
- Lineage event notifications: Yes
- Vote change notifications: Optional

**Admin overrides:**
- Manual vote trigger (skip timer)
- Pause/resume voting
- Emergency stop
- Direct action execution (bypass votes)

---

## Technical Stack

### Required Libraries
```
python >= 3.10
twitchio >= 3.1.0
flask >= 3.1.0
flask-socketio >= 5.5.0
pillow >= 12.0.0
```

### System Requirements
- Linux (Manjaro confirmed working)
- xdotool (keypress automation)
- The Bibites via Steam/Proton

### Development Environment
- Project root: `/home/daniel/prj/selection-protocol/`
- Overlay server: Already built, running on port 5000
- Game window: PID 1377474, Window ID 132120577
- venv: `.venv` (already configured)

---

## Branding & Presentation

### Name: Selection Protocol
**Tagline:** "Democratic Evolution Experiment"

**Why this name:**
- Natural + Artificial Selection (double meaning)
- Protocol = systematic, scientific, experimental
- Clean, memorable, not game-specific
- Matches terminal/data aesthetic

### Stream Title Format
```
Selection Protocol // Session [N] // [Scenario Name]
```

### Overlay Aesthetic
- Terminal/clinical data presentation
- Monospace fonts
- Minimal color (grey/white on black, purple accents)
- Data-focused, not entertainment-focused
- Full-page black background (OBS "lighten" blend)

### Documentation Approach
- GitHub README as primary explainer
- Transparent about mechanics/algorithms
- "Observation logs" not highlight reels
- Community as participants, not viewers

---

## Success Criteria

### Phase 1
- Bot stays connected >1 hour
- Votes counted accurately
- Overlay updates in real-time
- Zero missed votes

### Phase 2
- Votes execute within 2s of resolution
- Cooldowns respected
- Tie-breaks work correctly
- Admin can override anytime

### Phase 3
- Lineage tags persist across generations
- Multiple competing lineages visible
- Extinction events tracked
- Population stats accurate

### Phase 4
- Users return to check lineage status
- Chat develops strategies/rivalries
- System runs overnight unattended
- Organic discovery happening

---

## Open Questions

### Technical
- [ ] Twitch OAuth token setup (need user guidance)
- [ ] Channel name configuration
- [ ] Vote state persistence (SQLite vs JSON?)
- [ ] Connection resilience (reconnect IRC on drop)

### Design
- [ ] Show vote changes in overlay? (user_alice: l → k)
- [ ] Tie-break window too short/long? (currently 10s)
- [ ] Lineage tag format (just username or prefix?)
- [ ] Cap lineages per user? (or allow unlimited)

### Community
- [ ] Bot moderation needed?
- [ ] Multi-account prevention?
- [ ] Rate limiting per user?
- [ ] Chat command cooldowns?

---

## Next Steps (Priority Order)

1. **Create new repo structure:**
   ```
   selection-protocol/
   ├── src/
   │   ├── bot.py              # TwitchIO integration
   │   ├── vote_manager.py     # Vote counting + first-L tracking
   │   ├── executor.py         # Action execution via WebSocket
   │   ├── tagger.py           # Lineage tagging logic
   │   └── config.py           # Tunable parameters
   ├── tests/
   ├── docs/
   │   └── PROTOCOL.md         # How it works
   ├── README.md
   └── requirements.txt
   ```

2. **Port existing overlay/admin panel** from `bibites-prediction` repo

3. **Implement TwitchIO bot skeleton:**
   - Connect to channel
   - Parse k/l/x commands
   - Basic logging

4. **Build vote manager:**
   - Track votes per user
   - Identify first-L claimant
   - Resolution logic

5. **Integrate with admin panel:**
   - Call existing WebSocket handlers
   - Test with simulated chat

6. **Add overlay display:**
   - Vote counts section
   - Timer countdown
   - First-L claim indicator

7. **Test end-to-end:**
   - Multiple test accounts
   - Verify first-L claim logic
   - Validate tie-breaks

8. **Deploy & monitor:**
   - Let organic discovery happen
   - Iterate based on actual usage

---

## Why This Will Work

**Infrastructure is 80% done:**
- Overlay, admin panel, keypress automation all operational
- Game integration proven and stable
- Just need voting layer + lineage tracking

**Mechanics are elegant:**
- Simple rules (k/l/x, first-L gets naming rights)
- Strategic depth (when to commit vs wait)
- Scales from 1 to infinite viewers
- Natural engagement through personal lineages

**Unique positioning:**
- Not "Twitch Plays" derivative
- Competitive dynasty building through evolution
- Scientific experiment meets social game
- Built for discovery, not marketing

**Technical advantages:**
- Auto-follow solves targeting problem
- Game's tag inheritance does heavy lifting
- Cooldowns prevent spam/chaos
- Linux + xdotool = reliable automation

---

> DEMOCRACY ONLINE
> AWAITING FIRST PARTICIPANT
> LINEAGE INHERITANCE: READY
> SELECTION PROTOCOL: INITIALIZED

🔥

---

**Last Updated:** 2025-11-20
**Next Review:** After Phase 1 completion
