# Unified Bot Interface Refactor Plan

**Status:** Planned (from code review session)
**Created:** 2025-11-25

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
- Parse first word: `parse_first_word(message)` → single char or None
- Forward ANY single character to server
- Log server response for debugging
- Optionally provide user feedback based on response

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
    await self.sio.emit('vote', {...})
elif len(command) == 1:
    await self.sio.emit('game_command', {...})

# Proposed (single event):
if len(command) == 1:  # Any single character
    response = await self.sio.call('chat_input', {
        'username': username,
        'command': command,
        'timestamp': datetime.now().isoformat()
    })
    # Optional: Log response, provide user feedback
```

**Remove:**
- `self.valid_actions` (fetched from server)
- `get_actions` SocketIO call at startup
- Distinction between vote/command in bot code

**Keep:**
- `parse_first_word()` - pattern matching preprocessor
- Single-char validation before forwarding
- Response logging (for debugging)

---

### Step 2: Server Router

**File:** `src/server.py` or new `src/input_router.py`

**Add new handler:**
```python
@socketio.on('chat_input')
def handle_chat_input(data):
    """
    Route single-char chat input to appropriate handler.

    Args:
        data: {username: str, command: str, timestamp: str}

    Returns:
        {accepted: bool, type: str, reason: str, ...}
    """
    username = data.get('username')
    command = data.get('command')

    # Route to vote manager (k/l/x)
    if is_valid_action(command):
        result = vote_manager.add_vote(username, command, ...)
        return {'accepted': True, 'type': 'vote', 'action': command}

    # Route to game state (+/-/0-4)
    if command in ['+', '-', '0', '1', '2', '3', '4']:
        result = game_state.handle_command(command, username, cause='chat')
        return {
            'accepted': result['accepted'],
            'type': 'command',
            'reason': result['reason'],
            'cooldown_remaining': result.get('cooldown_remaining', 0)
        }

    # Invalid command
    return {'accepted': False, 'type': 'invalid', 'reason': 'unknown_command'}
```

---

### Step 3: Remove Old Handlers

**File:** `src/websocket.py` (or wherever vote/game_command handlers live)

**Remove:**
- `@socketio.on('vote')` (if exists)
- `@socketio.on('game_command')` (current implementation)
- `@socketio.on('get_actions')` (bot no longer needs this)

**Keep:**
- Admin panel handlers
- State broadcast handlers
- Other non-chat-input handlers

---

### Step 4: Optional User Feedback

**If bot needs to provide chat feedback:**

```python
# In twitch_bot.py after server response:
response = await self.sio.call('chat_input', {...})

if not response['accepted']:
    reason = response['reason']
    if reason == 'cooldown':
        cooldown = response.get('cooldown_remaining', 0)
        # await self.send_chat(f"@{username} Command on cooldown ({cooldown:.0f}s)")
    elif reason == 'invalid_command':
        # Silently ignore (don't spam chat for typos)
        pass
```

**Note:** User feedback optional for Phase 1, can defer to Phase 2.

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
- `parse_first_word()` edge cases (already working)
- Server router: k/l/x → vote_manager
- Server router: +/-/0-4 → game_state
- Server router: invalid → reject

### Integration Tests
1. Bot sends 'k' → vote_manager receives
2. Bot sends '+' → game_state receives
3. Bot sends 'z' → server rejects
4. Bot receives response with correct structure
5. Cooldown rejection returns correct remaining time

### Manual Tests
1. Run bot + server + game
2. Send k/l/x in Twitch chat → votes tracked
3. Send +/-/0-4 in Twitch chat → game responds
4. Send 'asdf' in Twitch chat → nothing breaks
5. Check server logs for routing

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

**Bot:**
- `src/twitch_bot.py` - Replace dual events with `chat_input`

**Server:**
- `src/server.py` - Add `@socketio.on('chat_input')` router
- `src/websocket.py` - Remove old `vote`/`game_command` handlers (if they exist there)

**Delete:**
- `src/game_commands.py` - Already deleted in code review

**Documentation:**
- Update architecture diagrams showing unified interface
- Update bot startup documentation (no action fetching)

---

## Decision Log

**Why single event instead of fixing dual events?**
- Bot shouldn't distinguish vote vs command
- Server is authoritative, should make routing decision
- Simpler mental model for future developers

**Why not use REST endpoint instead of SocketIO?**
- Already using SocketIO for bot-server connection
- Need bidirectional communication (server → bot events)
- Response structure matches SocketIO call pattern

**Why pattern match in bot at all?**
- Prevents spam of invalid messages to server
- Clear contract: bot only sends single-char
- Server can assume valid input shape (single char)

---

## Example Flow

**User types:** "k"

1. Bot: `parse_first_word("k")` → "k"
2. Bot: `len("k") == 1` → True, forward to server
3. Bot: `await sio.call('chat_input', {username: 'alice', command: 'k'})`
4. Server: `is_valid_action('k')` → True, route to vote_manager
5. Vote manager: `add_vote('alice', 'k')` → success
6. Server: Return `{accepted: True, type: 'vote', action: 'k'}`
7. Bot: Log response, optionally provide feedback

**User types:** "hey k"

1. Bot: `parse_first_word("hey k")` → "hey"
2. Bot: `len("hey") != 1` → False, ignore (not a command)

**User types:** "+"

1. Bot: `parse_first_word("+")` → "+"
2. Bot: `len("+") == 1` → True, forward to server
3. Bot: `await sio.call('chat_input', {username: 'bob', command: '+'})`
4. Server: `command in ['+', '-', ...]` → True, route to game_state
5. Game state: `handle_command('+', 'bob')` → {accepted: True, keypress: 'KP_Add'}
6. Server: Return `{accepted: True, type: 'command', reason: 'executed'}`
7. Bot: Log success

---

> **Status:** Ready to implement when time permits
> **Priority:** Medium (improves architecture, not blocking functionality)
> **Effort:** ~2-3 hours (bot changes + server router + testing)
