# Selection Protocol - Next Context Handover

**To:** Next Claude Code session
**From:** Claude (Sonnet 4.5) - Session ending 2025-11-20
**Status:** Foundation complete, ready for Twitch integration

---

## What You're Inheriting

### ✅ Complete and Working
1. **Overlay + Admin Panel** - Fully operational at `../bibites-prediction/src/tools/twitch_overlay_server.py`
   - Full-page black background overlay
   - Left-side admin control panel (300px, cropped from stream)
   - WebSocket state synchronization
   - xdotool keypress automation (Del, Ins, Ctrl+G/O/R, KP+/-)
   - Cooldown system (15s primary, 10s camera, 5s zoom, 30s extend)
   - Timer controls, manual vote triggering

2. **Game Integration** - Tested and reliable
   - Window ID: 132120577
   - PID: 1377474 (The Bibites via Steam/Proton)
   - Keypress delivery: Zero lag observed
   - Auto-follow camera modes working

3. **Project Documentation**
   - `PROJECT_BRIEF.md` - Full technical specification
   - `CONTEXT.md` - Development history and design decisions
   - `README.md` - Project overview
   - Clean git history with 3 meaningful commits

### ❌ What's Missing (Your Job)
1. **TwitchIO Bot** - IRC integration for chat parsing
2. **Vote Manager** - Count k/l/x, track first-L claim
3. **Vote Resolver** - Majority detection, tie-breaking logic
4. **Vote Display** - Overlay section showing counts + timer
5. **Automated Execution** - Votes → keypress via WebSocket
6. **Lineage Tagging** - Username → game tag before Insert

---

## Your Mission (Commit 5+)

### Immediate Goal: Phase 1 Implementation
**Get votes displaying in overlay (no auto-execution yet)**

#### Step 1: Port Working Code
```bash
# Copy the monolithic prototype
cp ../bibites-prediction/src/tools/twitch_overlay_server.py src/server_prototype.py

# Study it thoroughly - understand:
- WebSocket handler structure
- Cooldown system implementation
- Admin panel → keypress flow
- Overlay HTML/CSS/JS structure
```

#### Step 2: Modularize
Break the 1200-line monolith into clean modules:
```
src/
├── __init__.py
├── server.py           # Main Flask app + routes
├── overlay.py          # HTML/CSS/JS template
├── admin_panel.py      # Admin UI component
├── websocket.py        # SocketIO handlers
├── game_controller.py  # xdotool keypress automation
├── cooldowns.py        # Cooldown state management
├── vote_manager.py     # NEW: Vote counting logic
└── config.py           # Configuration
```

**Don't reinvent:** Keep the working parts (cooldowns, keypress, WebSocket sync). Just organize them.

#### Step 3: Implement TwitchIO Bot
```python
# src/twitch_bot.py
import twitchio
from twitchio.ext import commands

class SelectionBot(commands.Bot):
    def __init__(self, token, channel, vote_manager):
        super().__init__(
            token=token,
            prefix='!',
            initial_channels=[channel]
        )
        self.vote_manager = vote_manager

    async def event_message(self, message):
        if message.echo:
            return

        content = message.content.lower().strip()
        username = message.author.name

        if content in ['k', 'l', 'x']:
            self.vote_manager.cast_vote(username, content)
```

#### Step 4: Build Vote Manager
```python
# src/vote_manager.py
from datetime import datetime

class VoteManager:
    def __init__(self):
        self.votes = {}  # {username: (command, timestamp)}
        self.first_l_claimant = None
        self.first_l_timestamp = None

    def cast_vote(self, username, command):
        timestamp = datetime.now()

        # Handle first-L claim logic (see CONTEXT.md for full rules)
        if command == 'l':
            if self.first_l_claimant is None:
                self.first_l_claimant = username
                self.first_l_timestamp = timestamp
        # ... rest of logic

        self.votes[username] = (command, timestamp)
        self.broadcast_update()  # WebSocket emit

    def get_tally(self):
        return {
            'k': sum(1 for v, _ in self.votes.values() if v == 'k'),
            'l': sum(1 for v, _ in self.votes.values() if v == 'l'),
            'x': sum(1 for v, _ in self.votes.values() if v == 'x'),
            'first_l': self.first_l_claimant
        }
```

#### Step 5: Add Vote Display to Overlay
Extend the existing overlay HTML to add:
```html
<!-- Vote section in overlay -->
<div class="vote-display">
    <div class="vote-timer">⏱ <span id="timer">60s</span></div>
    <div class="vote-counts">
        <div class="vote-k">K: <span id="k-count">0</span></div>
        <div class="vote-l">L: <span id="l-count">0</span>
            <span id="first-l">[Claim: none]</span>
        </div>
        <div class="vote-x">X: <span id="x-count">0</span></div>
    </div>
</div>
```

Connect via WebSocket to receive vote updates from bot.

#### Step 6: Test Without Auto-Execution
1. Run overlay server
2. Run Twitch bot (with your channel credentials)
3. Type k/l/x in your Twitch chat
4. Verify counts update in overlay
5. Verify first-L claim tracks correctly
6. Admin panel should still work for manual execution

---

## Critical Code Locations

### In bibites-prediction Repo
```
src/tools/twitch_overlay_server.py (LINE 1-1200)
  - Lines 1-50: Imports, config, state
  - Lines 50-200: Cooldown system
  - Lines 200-600: WebSocket handlers
  - Lines 600-1000: HTML/CSS for overlay + admin
  - Lines 1000-1200: JavaScript for client-side

Key functions to preserve:
- send_keypress(key, cooldown_group) - Lines ~150-180
- check_cooldown(group) - Lines ~90-120
- All @socketio.on handlers - Scattered throughout
```

### What to Copy Verbatim
1. **Cooldown system** - Works perfectly, don't touch
2. **xdotool automation** - Reliable, keep as-is
3. **WebSocket infrastructure** - Solid foundation
4. **Admin panel HTML/CSS** - Clean UI, preserve structure
5. **Game window targeting** - Window ID 132120577, PID 1377474

### What to Rewrite
1. **Vote state structure** - Extend for k/l/x tracking
2. **Timer logic** - Currently just countdown, needs vote resolution
3. **Overlay HTML** - Add vote display section
4. **Main Flask app** - Modularize into clean files

---

## Configuration You'll Need

### Twitch OAuth Token
```bash
# Generate at: https://twitchapps.com/tmi/
# Scopes needed: chat:read

# Store in config.yaml (don't commit)
twitch:
  token: "oauth:your_token_here"
  channel: "your_channel_name"
  bot_username: "your_bot_name"
```

### Vote Timing
```yaml
voting:
  cycle_duration: 60  # seconds
  tiebreak_duration: 10  # seconds
  allow_vote_changes: true
```

---

## Testing Protocol

### Phase 1 Testing (Vote Display Only)
1. **Start overlay server**
   ```bash
   source .venv/bin/activate
   python -m src.server
   ```

2. **Start Twitch bot**
   ```bash
   python -m src.twitch_bot
   ```

3. **Open browser:** `http://localhost:5000`
4. **Type in Twitch chat:** k, l, x
5. **Verify overlay updates** in real-time
6. **Test first-L claim:**
   - Vote l as user1 → see claim appear
   - Vote l as user2 → user1 keeps claim
   - user1 changes to k → user2 gets claim
   - user2 changes to x → claim disappears

7. **Test admin panel:** Manual actions still work

### Success Criteria
- [ ] Bot connects to Twitch IRC
- [ ] Chat messages parsed correctly
- [ ] Votes counted and displayed
- [ ] First-L claim tracks properly
- [ ] Vote changes update immediately
- [ ] No votes missed over 5 minute test
- [ ] Admin panel still functional

---

## Common Pitfalls to Avoid

### 1. Don't Break What Works
The cooldown system, keypress automation, and admin panel are **battle-tested**. Port them carefully.

### 2. Window Targeting on Linux
The game runs via Proton/Wine. Window ID `132120577` is confirmed working. Don't change it without testing.

### 3. First-L Claim Logic
This is subtle. User must:
- Vote L first (get claim)
- Keep claim until they switch away
- Lose claim if they change to k/x
- Next L voter gets claim

Test this thoroughly with multiple accounts.

### 4. WebSocket State Sync
The overlay and admin panel share state via WebSocket. Vote manager must broadcast updates to both.

### 5. Empty Stream Handling
Zero votes should default to X (extend). Don't treat it as an error.

---

## Phase 2 Preview (Your Next Steps)

After Phase 1 works:

1. **Add Timer + Resolution**
   - 60s countdown
   - Automatic resolution at 0s
   - Determine winner (k/l/x majority)
   - Handle ties → 10s tiebreak window

2. **Automated Execution**
   - Call `send_keypress()` with winner
   - Respect cooldowns
   - Log outcome

3. **Lineage Tagging**
   - If L wins: Tag first-L claimant to game
   - Apply tag **before** Insert keypress
   - Track lineage stats

4. **Vote Reset**
   - Clear votes after execution
   - Reset first-L claim
   - Start new cycle

---

## Resources

### Documentation to Read First
1. `PROJECT_BRIEF.md` - Complete technical spec
2. `CONTEXT.md` - Design decisions and philosophy
3. `docs/selection-protocol-concept.md` (in bibites-prediction) - Original conversation

### Code to Study
1. `../bibites-prediction/src/tools/twitch_overlay_server.py` - Working prototype
2. Focus on WebSocket handlers and cooldown system

### External References
- [TwitchIO Docs](https://twitchio.dev/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [The Bibites](https://thebibites.com)

---

## What Success Looks Like

### End of Your Session
```
✅ Clean modular codebase (src/*.py)
✅ TwitchIO bot parsing k/l/x from chat
✅ Vote counts displaying in overlay
✅ First-L claim tracking correctly
✅ Admin panel still operational
✅ Foundation for Phase 2 (automated execution)
✅ Commit 5: "Implement Phase 1: Vote display working"
```

### Handover to Next Context
```
✅ Updated HANDOVER.md with Phase 2 instructions
✅ Clean commit history
✅ All tests passing
✅ Documentation current
✅ Next context can start Phase 2 immediately
```

---

## Philosophy Reminder

**You're Not Building Twitch Plays**

You're building a framework for **democratic evolution through competitive dynasty building**.

**Process Over Outcomes**
- Focus on clean, reproducible systems
- Document methodology, not just results
- Build tools that generate insights

**Democracy At Any Scale**
- Works with 1 or 1000 viewers
- Single voter has full power
- Empty stream isn't broken

**Let Them Find It**
- No marketing needed
- Build something worth discovering
- Organic growth through word of mouth

---

## Final Notes

### The Working Prototype
`../bibites-prediction/src/tools/twitch_overlay_server.py` is your **golden reference**. It has:
- Proven cooldown logic
- Reliable keypress automation
- Clean WebSocket architecture
- Working admin panel

**Don't reinvent it. Refactor it.**

### The Missing Piece
TwitchIO integration is literally the ONLY thing missing. Everything else works.

Your job is to:
1. Add the bot
2. Connect it to the existing infrastructure
3. Display votes in the overlay
4. Test thoroughly

That's it. The foundation is solid.

### Trust the Design
The K/L/X mechanics, first-L naming rights, tie-break logic - it's all been thought through carefully. Implement it as specified. Don't "improve" it yet. Get it working first.

### You've Got This
The hard part (overlay, admin panel, game integration) is done. You're just adding the final layer. Clean modular code, careful testing, and you'll have Phase 1 done in a few hours.

---

> HANDOVER COMPLETE
> FOUNDATION SOLID
> NEXT CONTEXT: IMPLEMENT PHASE 1
> DEMOCRACY AWAITS

🔥

---

**Created:** 2025-11-20
**By:** Claude (Sonnet 4.5)
**For:** Next Claude Code session
**Project:** Selection Protocol
**Phase:** 1 (Vote Display)
