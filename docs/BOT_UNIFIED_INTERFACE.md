# Unified Bot Interface Refactor Plan

**Status:** In Review (final approval pending)
**Created:** 2025-11-25
**Updated:** 2025-11-25

---

## Current Problem

Bot has split interface to server:
- `vote` event → vote_manager (for k/l/x)
- `game_command` event → game_state (for +/-/0-4)
- Bot fetches enabled votes at startup
- Bot whitelists specific commands (`len(command) == 1`)

**Issues:**
1. Bot knows too much about server internals
2. Two parallel event paths
3. Adding new commands requires bot changes
4. Inconsistent with server-authoritative philosophy

---

## Proposed Solution

### Single Interface Pattern

**Bot responsibility:** Pattern matching only
- Parse first word: `parse_chat_input(message)` → single char or None
- Forward ANY parsed input to server (parser is sole authority on validity)
- Log single consolidated line per message with server response
- No fallbacks, no client-side validation

**Server responsibility:** Routing and validation
- Receive generic `chat_input` event
- Route to vote_manager (k/l/x) or game_state (+/-/0-4) or reject (invalid)
- Return structured response: `{accepted: bool, type: 'vote'|'command'|'invalid', reason: str, ...}`

---

## Implementation Steps

### Step 1: Bot Simplification

**File:** `src/twitch_bot.py`

**Changes:**
```python
# Current (dual events):
if command in self.valid_actions:
    await self.sio.emit('vote_cast', {...})
elif len(command) == 1:
    await self.sio.emit('game_command', {...})

# Proposed (unified event):
parsed_input = parse_chat_input(text)
if parsed_input:  # Parser determines validity
    try:
        response = await self.sio.call('chat_input', {
            'username': username,
            'input': parsed_input,
            'timestamp': datetime.now().isoformat()
        }, timeout=5)

        # Single consolidated log line
        log_chat_input(username, text, parsed_input, response)
    except Exception as e:
        # Fail-fast: let exceptions surface
        print(f"[ERROR] Failed to send chat_input: {e}")
        raise
```

**Log format:**
```
[12:34:56] alice: "k boring" → k (type:vote, accepted:true)
[12:34:57] bob: "+ zoom in" → + (type:command, accepted:false, reason:cooldown, remaining:5.2s)
[12:34:58] charlie: "hello" → None (not parsed)
```

**Remove:**
- `self.valid_actions` attribute
- `self.votes_received` counter
- `self.game_commands_received` counter
- `get_actions` SocketIO call at startup
- All vote/command distinction in bot code
- Separate logging for votes vs commands

**Rename:**
- `parse_first_word()` → `parse_chat_input()`

**Keep:**
- Pattern matching logic (single-char extraction)
- Response-based logging (consolidated format)

---

### Step 2: Server Router

**File:** `src/server.py`

**Add new handler:**
```python
@socketio.on('chat_input')
def handle_chat_input(data):
    """
    Route single-char chat input to appropriate handler.

    Args:
        data: {username: str, input: str, timestamp: str}

    Returns:
        {accepted: bool, type: str, reason: str, ...}
    """
    username = data.get('username')
    chat_input = data.get('input')
    timestamp_str = data.get('timestamp')

    # Parse timestamp if provided
    timestamp = None
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.now()

    # Route to vote manager (k/l/x)
    if chat_input in vote_manager.get_enabled_actions():
        success = vote_manager.cast_vote(username, chat_input, timestamp)
        return {
            'accepted': success,
            'type': 'vote',
            'input': chat_input
        }

    # Route to game state (+/-/0-4)
    if chat_input in ['+', '-', '0', '1', '2', '3', '4']:
        result = game_state.handle_command(chat_input, username, cause='chat')
        return {
            'accepted': result['accepted'],
            'type': 'command',
            'reason': result.get('reason', 'executed' if result['accepted'] else 'rejected'),
            'cooldown_remaining': result.get('cooldown_remaining', 0)
        }

    # Invalid input
    return {
        'accepted': False,
        'type': 'invalid',
        'reason': 'unknown_input'
    }
```

---

### Step 3: Remove Old Handlers

**Files:** `src/server.py`, `src/websocket.py`

**Remove from server.py:**
- `@socketio.on('get_actions')` handler (lines 110-119)
- `@socketio.on('vote_cast')` handler (lines 141-174)

**Remove from websocket.py:**
- `@socketio.on('game_command')` handler (lines 114-178)

**Keep:**
- `@socketio.on('bot_connected')` - Bot status tracking
- Admin panel handlers - Testing interface
- State broadcast handlers - Real-time updates
- Vote manager event handlers - Round lifecycle

---

### Step 4: Consolidated Logging

**File:** `src/twitch_bot.py`

**Implement single log line per message:**

```python
def log_chat_input(username, raw_message, parsed_input, response):
    """
    Log single consolidated line showing chat input processing result.

    Format: [HH:MM:SS] username: "raw_message" → parsed (type:X, accepted:Y, ...)
    """
    timestamp = datetime.now().strftime('%H:%M:%S')

    if parsed_input is None:
        # Not a command, don't log (too verbose)
        return

    # Build response details
    type_str = response.get('type', 'unknown')
    accepted = response.get('accepted', False)
    reason = response.get('reason', '')
    cooldown = response.get('cooldown_remaining', 0)

    # Format: [12:34:56] alice: "k boring" → k (type:vote, accepted:true)
    details = f"type:{type_str}, accepted:{accepted}"
    if reason:
        details += f", reason:{reason}"
    if cooldown > 0:
        details += f", remaining:{cooldown:.1f}s"

    print(f'[{timestamp}] {username}: "{raw_message}" → {parsed_input} ({details})')
```

**Note:** User feedback to chat (Phase 2) - response structure supports it but not implemented yet.

---

## Migration Path

### Option A: Clean Break (Recommended)
1. Implement new `chat_input` handler in server
2. Update bot to use single event
3. Remove old handlers
4. Test end-to-end
5. Commit as single cohesive change

### Option B: Gradual Migration
1. Add new `chat_input` handler alongside old ones
2. Update bot to use new handler
3. Verify working in production
4. Remove old handlers in separate commit

**Recommendation:** Option A - changes are isolated to bot/server interface, not user-facing.

---

## Testing Strategy

### Unit Tests
- `parse_chat_input()` edge cases (already working as parse_first_word)
- Server router: k/l/x → vote_manager
- Server router: +/-/0-4 → game_state
- Server router: invalid → reject with type='invalid'
- Log formatting with various response types

### Integration Tests
1. Bot sends 'k' → vote_manager receives, response type='vote'
2. Bot sends '+' → game_state receives, response type='command'
3. Bot sends 'z' → server rejects, response type='invalid'
4. Bot receives response with correct structure (accepted, type, reason)
5. Cooldown rejection returns correct remaining time
6. Consolidated log shows all fields correctly

### Manual Tests
1. Run bot + server + game
2. Send "k boring" in Twitch chat → vote tracked, log shows parsed 'k'
3. Send "+ zoom in" in Twitch chat → game responds, log shows command
4. Send "hello world" in Twitch chat → not parsed, nothing happens
5. Send rapid commands → cooldown logged with remaining time
6. Check server logs for routing decisions

---

## Benefits

**Simplicity:**
- Bot has single responsibility: pattern matching
- Server has single entry point for all chat input
- Clear separation of concerns

**Extensibility:**
- Add new commands: change server router only
- Add new vote types: change vote_manager only
- Bot code unchanged

**Consistency:**
- Single source of truth (server)
- No dual-fetch pattern (votes vs commands)
- Uniform response structure

**Debugging:**
- Single event to monitor in SocketIO logs
- Clear accept/reject signals in response
- Type field indicates routing decision

---

## Risks & Mitigations

**Risk:** Bot-server coupling if response structure changes
**Mitigation:** Document response schema, version if needed

**Risk:** Breaking existing vote/command flow during migration
**Mitigation:** Test thoroughly before deployment, consider gradual migration

**Risk:** Performance impact of routing logic in server
**Mitigation:** Routing is trivial (dict lookup + if statements), negligible overhead

---

## Future Enhancements

**Phase 2:**
- User feedback via chat (cooldown messages, invalid command hints)
- Per-user rate limiting in server router
- Command statistics (acceptance rate, rejection reasons)

**Phase 3:**
- Multi-char commands (e.g., `!stats`, `!lineage`)
- Different routing based on prefix (! vs single-char)
- Expansion beyond single-char pattern

---

## Files to Change

**Bot (`src/twitch_bot.py`):**
- Rename `parse_first_word()` → `parse_chat_input()`
- Remove `self.valid_actions`, `self.votes_received`, `self.game_commands_received`
- Remove `get_actions` call in `connect_to_flask()`
- Replace dual `vote_cast`/`game_command` events with single `chat_input` event
- Add `log_chat_input()` function for consolidated logging
- Update `event_message()` handler to use truthiness check
- Use `sio.call()` with 5s timeout for request/response pattern

**Server (`src/server.py`):**
- Add `@socketio.on('chat_input')` router (new handler)
- Remove `@socketio.on('get_actions')` handler (lines 110-119)
- Remove `@socketio.on('vote_cast')` handler (lines 141-174)

**Server (`src/websocket.py`):**
- Remove `@socketio.on('game_command')` handler (lines 114-178)

**Documentation:**
- Update architecture diagrams showing unified interface
- Update HANDOVER.md with refactor summary
- Update README.md if bot startup flow documented there

---

## Decision Log

**Why single event instead of fixing dual events?**
- Bot shouldn't distinguish vote vs command
- Server is authoritative, should make routing decision
- Simpler mental model for future developers

**Why not use REST endpoint instead of SocketIO?**
- Already using SocketIO for bot-server connection
- Need bidirectional communication (server → bot events)
- Response structure matches SocketIO call pattern (`sio.call()` for request/response)

**Why pattern match in bot at all?**
- Prevents spam of invalid messages to server
- Clear contract: bot only sends parsed single-char inputs
- Server can assume valid input shape (already validated by parser)

**Why "chat_input" terminology?**
- Neutral term covering both votes and game commands
- "action" reserved for votes (k/l/x) in vote_manager
- "command" reserved for game controls (+/-/0-4) in game_state
- Bot-server interface uses neutral "input" to avoid confusion

**Why consolidated logging?**
- Single source of truth per message (server response)
- Easier to grep logs for specific users/commands
- Shows complete picture: raw message → parsed → server decision
- Reduces log noise (no duplicate vote/command lines)

**Why fail-fast error handling?**
- SocketIO is reliable within local network
- Exceptions indicate real problems (server down, network issues)
- Better to surface errors than silently fail
- No fallbacks or backwards compatibility - clean final state

**Why truthiness check instead of `len(command) == 1`?**
- Parser is sole authority on validity
- Simpler: if parsed successfully, forward it
- Easier to extend parser for multi-char commands later (!stats, !lineage)
- No duplicate validation logic in caller

---

## Example Flow

**User types:** "k boring"

1. Bot: `parse_chat_input("k boring")` → "k"
2. Bot: `if "k":` → True, forward to server
3. Bot: `response = await sio.call('chat_input', {username: 'alice', input: 'k', ...})`
4. Server: `'k' in vote_manager.get_enabled_actions()` → True, route to vote_manager
5. Vote manager: `cast_vote('alice', 'k', timestamp)` → success
6. Server: Return `{accepted: True, type: 'vote', input: 'k'}`
7. Bot: Log single line: `[12:34:56] alice: "k boring" → k (type:vote, accepted:true)`

**User types:** "hey k"

1. Bot: `parse_chat_input("hey k")` → "hey"
2. Bot: Length check: "hey" has 3 chars, not single char
3. Bot: Returns None (invalid pattern)
4. Bot: `if None:` → False, don't forward (not a command)
5. No log output (too verbose to log non-commands)

**User types:** "+ zoom in"

1. Bot: `parse_chat_input("+ zoom in")` → "+"
2. Bot: `if "+":` → True, forward to server
3. Bot: `response = await sio.call('chat_input', {username: 'bob', input: '+', ...})`
4. Server: `'+' in ['+', '-', '0', '1', '2', '3', '4']` → True, route to game_state
5. Game state: `handle_command('+', 'bob', cause='chat')` → {accepted: True, keypress: 'KP_Add'}
6. Server: Return `{accepted: True, type: 'command', reason: 'executed'}`
7. Bot: Log single line: `[12:34:57] bob: "+ zoom in" → + (type:command, accepted:true, reason:executed)`

**User types:** "z invalid"

1. Bot: `parse_chat_input("z invalid")` → "z"
2. Bot: `if "z":` → True, forward to server
3. Bot: `response = await sio.call('chat_input', {username: 'charlie', input: 'z', ...})`
4. Server: Not a vote, not a command → invalid
5. Server: Return `{accepted: False, type: 'invalid', reason: 'unknown_input'}`
6. Bot: Log single line: `[12:34:58] charlie: "z invalid" → z (type:invalid, accepted:false, reason:unknown_input)`

---

> **Status:** Ready for implementation (pending final approval)
> **Priority:** Medium (architectural improvement, clean design)
> **Effort:** ~2-3 hours (bot refactor + server router + cleanup + testing)
> **Approach:** Clean break (Option A) - single cohesive commit
