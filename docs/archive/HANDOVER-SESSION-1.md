# Selection Protocol - Session 2 Handover

**To:** Next Claude Code session
**From:** Claude (Sonnet 4.5) - Session ending 2025-11-21
**Status:** OAuth flow complete, EventSub bot rewrite planned

---

## Session 1 Recap

**Started:** Documentation only (PROJECT_BRIEF, CONTEXT, HANDOVER)
**Goal:** Port overlay, build TwitchIO bot, integrate Phase 1

**Completed:**
- ✅ Ported & modularized overlay server (Commit 5)
- ✅ Implemented modern OAuth flow (Commit 6)
- ✅ Discovered IRC deprecation → EventSub required
- ✅ OAuth authorization code grant flow working perfectly
- ✅ Token caching & refresh logic operational
- ✅ Bot infrastructure (test mode, heartbeat, logging)

**Key Discovery:** Twitch deprecated IRC chat in favor of EventSub WebSocket. TwitchIO removed IRC from core library. Current bot skeleton uses IRC (receives 0 messages). Need complete rewrite to EventSub.

---

## What You're Inheriting

### ✅ Complete and Working

**1. Overlay Server** - `src/server.py` + modules
- Full Flask + SocketIO server on port 5000
- Admin panel (left sidebar, 300px, cropped from stream)
- OBS overlay (full-page black background, "lighten" blend mode)
- WebSocket state synchronization
- xdotool keypress automation → The Bibites (window ID: 132120577)
- Cooldown system: 15s primary, 10s camera, 5s zoom, 30s extend
- Manual controls: Del/Ins, Ctrl+G/O/R, KP+/-, vote trigger, timer

**2. OAuth Infrastructure** - `src/oauth_flow.py`
- Authorization code grant flow (browser-based)
- Local HTTP server on localhost:3000 for callback
- Token exchange (code → access + refresh tokens)
- Token caching to `.twitch_token` (gitignored)
- Automatic token refresh on expiry
- Scopes: `chat:read`, `chat:edit`, `user:read:chat`, `user:write:chat`, `user:bot`, `channel:bot`

**3. Bot Skeleton** - `src/twitch_bot.py` (needs rewrite)
- Integrated OAuth flow (gets user access token automatically)
- Auto-fetches bot_id from username via Twitch API
- Test mode: `--test` flag runs 30s then exits cleanly
- Heartbeat logging (uptime, messages, votes every 10s)
- Currently uses IRC (deprecated) - **NEEDS EVENTSUB REWRITE**

**4. Configuration**
- `config.yaml.example` - Simple template (client_id, client_secret, channel, nick)
- `.twitch_token` - OAuth token cache (gitignored)
- All token management automated

**5. Documentation**
- `CLAUDE.md` - AI assistant handover guide
- `docs/TWITCH_SETUP.md` - OAuth setup instructions (accurate for current flow)
- `PROJECT_BRIEF.md` - Full spec
- `CONTEXT.md` - Development history
- `README.md` - Updated with current status

### ❌ What's Missing (Your Job)

**1. EventSub Bot Rewrite** ⚠️ CRITICAL BLOCKER
- Replace IRC-based `commands.Bot` with EventSub `commands.AutoBot`
- Use `EventSubWSClient` to connect to `wss://eventsub.wss.twitch.tv/ws`
- Subscribe to `ChatMessageSubscription` events
- Handle `event_message` from EventSub (not IRC)
- Send messages via Twitch API (not IRC PRIVMSG)

**2. Vote Manager** - `src/vote_manager.py` (not yet created)
- Track votes per user (username → k/l/x, latest replaces)
- First-L claimant tracking (timestamp-based, loses on switch)
- Vote cycle timer (60s default)
- Tie detection & tie-break window (10s)
- WebSocket broadcast to overlay on vote changes

**3. Vote Display in Overlay** - Update `src/overlay.py`
- Vote counts section (K: 5, L: 3, X: 2)
- Timer countdown (60s → 0s)
- First-L claim indicator ("@username claims lineage")
- Live updates via WebSocket

**4. Vote Resolver** - `src/vote_resolver.py` (not yet created)
- Majority detection (highest count wins)
- Tie-break logic (10s window for L steals)
- Default to X when empty stream
- Trigger admin panel keypress via WebSocket

---

## Your Mission: EventSub Bot Rewrite

### Goal
Get TwitchIO bot receiving chat messages via EventSub, then build Phase 1 vote display.

### Step 1: Rewrite Bot to Use EventSub

**Current state:** `src/twitch_bot.py` uses `commands.Bot` (IRC, deprecated)

**Target state:** Use `commands.AutoBot` with EventSub subscriptions

**Architecture pattern (from TwitchIO docs):**

```python
from twitchio.ext import commands, eventsub

class Bot(commands.AutoBot):
    def __init__(self):
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,  # Same as bot_id for personal bot
            prefix="!",
            force_subscribe=True,
        )

    async def event_ready(self):
        print(f"Bot connected: {self.user_id}")

        # Subscribe to chat messages for our channel
        subs = [
            eventsub.ChatMessageSubscription(
                broadcaster_user_id=OWNER_ID,
                user_id=self.bot_id
            ),
        ]
        await self.multi_subscribe(subs)

    @commands.Component.listener()
    async def event_message(self, payload: eventsub.ChatMessage):
        # This receives EventSub chat messages (not IRC!)
        username = payload.chatter.name
        text = payload.text
        print(f"[{username}] {text}")

        # Parse k/l/x votes here
```

**Key changes needed:**
1. Replace `commands.Bot` → `commands.AutoBot`
2. Remove IRC-specific code (capabilities, initial_channels)
3. Add `ChatMessageSubscription` in `event_ready`
4. Update `event_message` to handle `eventsub.ChatMessage` payload
5. Keep OAuth flow integration (still need user access token)
6. Keep test mode (--test flag, 30s timeout)

**Critical notes:**
- EventSub receives JSON payloads, not raw IRC strings
- `payload.chatter.name` is username (not `message.author.name`)
- `payload.text` is message content (not `message.content`)
- `payload.broadcaster` is the channel object
- Still need same OAuth scopes (`user:bot`, `channel:bot`, etc.)

### Step 2: Test EventSub Reception

```bash
python -m src.twitch_bot --test
# Should now show:
# [11:30:00] username: hello world
# [11:30:05] viewer123: k
#   → VOTE: K
```

If you see chat messages logged, **EventSub is working!**

### Step 3: Build Vote Manager

Once bot receives messages, create `src/vote_manager.py`:

**Required functionality:**
- `cast_vote(username, vote, timestamp)` - Record/update vote
- `get_vote_counts()` - Return dict {k: 5, l: 3, x: 2}
- `get_first_l_claimant()` - Return username or None
- `reset_votes()` - Clear for next cycle
- `start_cycle()` / `end_cycle()` - Timer management

**First-L logic:**
- Track timestamp of each L vote
- Claimant = earliest L voter who hasn't switched away
- Switching to K or X loses claim
- Switching back to L = new timestamp (back of queue)

### Step 4: Integrate Vote Display

Update `src/overlay.py` HTML to add vote section:
- Position: TBD (top-right? bottom-center?)
- Show: K count, L count, X count, timer, first-L claim
- Update via WebSocket event from vote manager

**WebSocket event:**
```javascript
socket.on('vote_update', (data) => {
    // data = {k: 5, l: 3, x: 2, timer: 45, claimant: "username"}
    updateVoteDisplay(data);
});
```

---

## Architecture Decisions Made

### Separate Processes (Recommended)
```
Process 1: python -m src.server       # Flask overlay + admin
Process 2: python -m src.twitch_bot   # EventSub chat bot
```

**Communication:** Bot connects to Flask SocketIO as a client, broadcasts vote updates.

**Why separate:**
- Independent failure domains (bot crash ≠ overlay crash)
- Easier debugging (clear logs per process)
- Clean separation of concerns (UI vs chat logic)
- Async complexity avoided (Flask sync, EventSub async)

**Bot → Server communication:**
```python
# In bot:
import socketio
sio = socketio.AsyncClient()
await sio.connect('http://localhost:5000')
await sio.emit('vote_update', {'k': 5, 'l': 3, 'x': 2})
```

---

## Testing Checklist

**Before declaring EventSub bot working:**
- [ ] Bot connects without errors
- [ ] Chat messages appear in terminal with timestamps
- [ ] k/l/x votes highlighted with "→ VOTE: K"
- [ ] Test mode (--test) runs 30s and exits cleanly
- [ ] Heartbeat shows non-zero message count
- [ ] OAuth token cached to `.twitch_token`
- [ ] Token refresh works on subsequent runs

**Before declaring Phase 1 complete:**
- [ ] Overlay shows vote counts updating live
- [ ] Timer counts down from 60s → 0s
- [ ] First-L claimant displays correctly
- [ ] Multiple users voting (k/l/x) reflected accurately
- [ ] Vote switching (user changes from k→l) updates counts
- [ ] First-L claim transfers when claimant switches away
- [ ] Admin panel still works (manual keypresses)

---

## Known Issues & Gotchas

**1. EventSub vs IRC confusion**
- Old tutorials/docs use IRC (`commands.Bot`)
- TwitchIO 3.x moved to EventSub (`commands.AutoBot`)
- IRC code won't receive messages anymore
- Look for EventSub examples, not IRC

**2. Token scopes are critical**
- Need `user:bot` and `channel:bot` for EventSub chat
- Old `chat:read`/`chat:edit` not sufficient alone
- OAuth flow in `src/oauth_flow.py` already requests correct scopes
- If chat not working, check token has all 6 scopes

**3. Bot ID vs Owner ID**
- `bot_id` = numeric ID of bot account
- `owner_id` = numeric ID of channel owner (same for personal bot)
- Currently auto-fetched from username via Twitch API
- Keep this auto-fetch logic, it's clean

**4. Test mode is your friend**
- Use `--test` flag during development (30s run, clean exit)
- Avoids background processes hanging
- Easy to iterate rapidly

**5. Overlay server runs independently**
- Don't kill the Flask server when testing bot
- Server on port 5000, bot connects as SocketIO client
- Can test admin panel while bot is stopped

---

## File Structure Reference

```
selection-protocol/
├── src/
│   ├── __init__.py
│   ├── server.py              # Flask + SocketIO (overlay + admin)
│   ├── overlay.py             # HTML/CSS/JS template
│   ├── admin_panel.py         # Placeholder
│   ├── websocket.py           # SocketIO handlers for server
│   ├── game_controller.py     # xdotool keypress automation
│   ├── cooldowns.py           # Cooldown state management
│   ├── config.py              # Game config (window ID, cooldowns)
│   ├── oauth_flow.py          # OAuth authorization code flow
│   └── twitch_bot.py          # Bot (NEEDS EVENTSUB REWRITE)
│
├── tools/
│   └── get_oauth_token.py     # Deprecated (OAuth flow automated now)
│
├── docs/
│   ├── TWITCH_SETUP.md        # OAuth setup guide
│
├── config.yaml.example        # Twitch config template
├── .twitch_token              # OAuth token cache (gitignored)
├── requirements.txt           # Python dependencies
│
├── PROJECT_BRIEF.md           # Full technical spec
├── CONTEXT.md                 # Development history
├── HANDOVER.md                # Session 1 handover (outdated)
├── HANDOVER-2.md              # This file
├── CLAUDE.md                  # AI assistant guide
└── README.md                  # Project overview
```

---

## Commit History Reference

```
289e058 Add OAuth authorization code flow and bot infrastructure
38393e4 (rolled back) Implement TwitchIO bot with modern OAuth flow
c1ece4f Port and modularize prototype from bibites-prediction
8f9d9da Add CLAUDE.md - AI assistant handover document
f649133 Add engagement hooks and organic growth strategy
0eb2276 Add comprehensive handover document for next context
bd36ece Add project structure and organization
c086a0f Add development context and history
97f568f Initial commit: Selection Protocol project brief
```

---

## Resources & Links

**TwitchIO EventSub:**
- Docs: https://twitchio.dev/en/latest/
- EventSub guide: https://twitchio.dev/en/latest/references/eventsub/eventsub_models.html
- Quickstart: https://twitchio.dev/en/latest/getting-started/quickstart.html

**Twitch API:**
- Dev console: https://dev.twitch.tv/console/apps
- EventSub reference: https://dev.twitch.tv/docs/eventsub/
- OAuth guide: https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/

**The Bibites:**
- Website: https://thebibites.com
- Game runs via Steam/Proton (window ID: 132120577)

---

## Next Session Plan

**Priority 1:** EventSub bot rewrite (BLOCKER for everything else)
**Priority 2:** Vote manager implementation
**Priority 3:** Vote display in overlay
**Priority 4:** End-to-end Phase 1 testing

**Estimated commits:**
- Commit 7: EventSub bot rewrite (working chat reception)
- Commit 8: Vote manager with first-L tracking
- Commit 9: Vote display in overlay
- Commit 10: Integration & Phase 1 testing

**Success criteria:**
- Type "k" in Twitch chat → overlay shows K count increment
- Multiple users voting → counts update correctly
- First-L claimant displayed and updates on vote switches
- Timer counts down, votes reset on cycle end
- Admin panel still works independently

---

## Tips for Success

1. **Start with EventSub bot** - Everything else depends on this
2. **Test early, test often** - Use `--test` mode for rapid iteration
3. **Trust the OAuth flow** - It works, token refresh works, don't touch it
4. **Keep processes separate** - Flask server + bot as separate processes
5. **Check TwitchIO version** - Should be 3.x (EventSub era, not 2.x IRC era)
6. **Read CLAUDE.md first** - Has architectural context and patterns
7. **Commit frequently** - Clean history tells the story
8. **Phase 1 before Phase 2** - Display before automation (validate logic)

---

## Questions You Might Have

**Q: Why not just fix IRC?**
A: IRC is deprecated by Twitch. TwitchIO removed it from core. EventSub is the future, works better, cleaner JSON payloads.

**Q: Why AutoBot instead of regular Bot?**
A: AutoBot handles EventSub subscription management automatically, including refresh on reconnect.

**Q: Why separate bot and server processes?**
A: Independent failure domains, cleaner async handling, easier debugging. Communication via SocketIO is clean.

**Q: OAuth flow seems complex - simplify?**
A: No! It's working perfectly. Browser auth → token cache → auto-refresh. Touch nothing.

**Q: Test mode vs daemon mode?**
A: Test mode (`--test`) runs 30s for rapid iteration. Daemon mode (no flag) runs forever for production.

**Q: Where's vote manager code?**
A: Doesn't exist yet. You're building it. Logic is in PROJECT_BRIEF.md Phase 1 section.

---

> SESSION 1 COMPLETE
> OAUTH FLOW: OPERATIONAL
> EVENTSUB REWRITE: READY TO BEGIN
>
> Next Claude: Rewrite the bot. Make it listen. Let democracy speak.

🔥 Good luck! 🔥
