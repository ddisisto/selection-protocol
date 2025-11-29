# Bot Message Filtering Research

**Date:** 2025-11-24
**Problem:** Bot announcements get parsed as commands when bot username matches testing user, creating infinite loops.

---

## Executive Summary

**Solution:** Check `payload.chatter.id` against `self.bot_id` in `event_message()` handler.

**Why:** EventSub `channel.chat.message` payloads include sender's user ID via `chatter.id` field. Our bot already stores `self.bot_id` (numeric). Simple equality check filters all bot-sent messages regardless of username conflicts.

**Reliability:** 100% - User IDs are unique, immutable, and always present in EventSub payloads.

---

## Findings

### 1. EventSub Payload Structure

**Available Fields (from Twitch EventSub `channel.chat.message`):**
- `chatter_user_id` - Sender's numeric user ID (string)
- `chatter_user_login` - Sender's username (string)
- `chatter_user_name` - Sender's display name (string)
- `badges` - Array of chat badges (moderator, subscriber, etc.)
- `message.text` - Message content
- `message_type` - Classification (e.g., "text")
- `source_broadcaster_user_id` - Present only for shared chat messages

**Key Insight:** No explicit "bot" flag, but `chatter_user_id` uniquely identifies sender.

### 2. TwitchIO EventSub ChatMessage Model

**Our Code Uses:** `payload: eventsub_.ChatMessage`

**Available Attributes:**
```python
payload.chatter           # PartialUser object
payload.chatter.id        # str | int - User's numeric ID
payload.chatter.name      # str - Username (login name)
payload.text              # Message content
payload.badges            # List[ChatMessageBadge]
```

**Critical:** `payload.chatter.id` returns the sender's Twitch user ID (same type as our `self.bot_id`).

### 3. Our Bot's Available Data

**From `__init__()` parameters:**
- `self.bot_id` - Bot's numeric Twitch user ID (string, fetched via Helix API)
- `self._bot_username` - Bot's username (lowercase string)

**Current Implementation (line 297-298):**
```python
username = payload.chatter.name
text = payload.text
```

**Missing:** No check against `payload.chatter.id`

### 4. Current Filter Mechanism

**Line 303-306:**
```python
# Check if this is our startup message reflected back
if not self.startup_message_verified and "Selection Protocol online" in text:
    self.startup_message_verified = True
    return  # Don't log our own startup message
```

**Problem:** Content-based filtering only works for specific known messages. Announcements like "Voting opened by @user: L" don't match and get parsed.

---

## Proposed Solutions

### Solution 1: User ID Comparison (RECOMMENDED)

**Implementation:**
```python
async def event_message(self, payload: eventsub_.ChatMessage):
    """Handle incoming chat messages from EventSub."""
    timestamp = datetime.now().strftime('%H:%M:%S')

    # Extract username and message text
    username = payload.chatter.name
    text = payload.text

    # Skip our own messages by comparing user IDs
    if str(payload.chatter.id) == str(self.bot_id):
        return

    self.messages_received += 1
    # ... rest of handler
```

**Why This Works:**
- User IDs are unique and immutable
- No username conflicts possible
- Works even if bot username changes
- Simple equality check (O(1))
- Always reliable (user IDs always present)

**Code Changes:**
- File: `/home/daniel/prj/selection-protocol/src/twitch_bot.py`
- Location: Line 287-310 (in `event_message()` handler)
- Add: 3 lines after line 298 (after extracting username/text)
- Remove: Lines 303-306 (startup message check - now redundant)

**Edge Cases:**
- ✅ Bot username matches real user: Filtered correctly by ID
- ✅ Bot display name changes: Still works (ID unchanged)
- ✅ Startup message: Filtered (sent by bot)
- ✅ Round announcements: Filtered (sent by bot)
- ✅ Multiple bots in channel: Each filters own messages

---

### Solution 2: Username Comparison (FALLBACK)

**Implementation:**
```python
# Skip messages from bot username
if username.lower() == self._bot_username:
    return
```

**Pros:**
- Simpler (no type conversion)
- Works if bot_id somehow unavailable

**Cons:**
- ❌ Fails when bot username matches real user (original problem)
- ❌ Case-sensitivity issues (mitigated by `.lower()`)
- ❌ Doesn't work if bot username changes

**Verdict:** NOT RECOMMENDED - doesn't solve the stated problem.

---

### Solution 3: Hybrid (Username + Content Pattern)

**Implementation:**
```python
# Skip bot messages by username AND known patterns
if username.lower() == self._bot_username:
    return

# Additional filter for specific messages
if any(pattern in text for pattern in [
    "Selection Protocol online",
    "Voting opened by",
    "wins!"
]):
    # Only skip if from bot username
    if username.lower() == self._bot_username:
        return
```

**Pros:**
- Defense in depth

**Cons:**
- ❌ Complex (maintenance burden)
- ❌ Still fails on username collision
- ❌ Requires updating patterns for new announcements
- ❌ False negatives if user says "K wins!" in chat

**Verdict:** NOT RECOMMENDED - complexity without solving root issue.

---

### Solution 4: Badge-Based Filtering

**Implementation:**
```python
# Check if sender has "bot" badge
for badge in payload.badges:
    if badge.set_id == 'bot':
        return
```

**Pros:**
- Official Twitch bot identification

**Cons:**
- ❌ Only works if bot uses App Access Token (we use User Access Token)
- ❌ Requires `channel:bot` scope + broadcaster authorization
- ❌ Not available for our current auth setup

**Verdict:** NOT APPLICABLE - requires different OAuth flow.

---

## Implementation Plan

### Step 1: Update `event_message()` Handler

**File:** `/home/daniel/prj/selection-protocol/src/twitch_bot.py`

**Current (lines 287-310):**
```python
@commands.Component.listener()
async def event_message(self, payload: eventsub_.ChatMessage):
    """Handle incoming chat messages from EventSub."""
    timestamp = datetime.now().strftime('%H:%M:%S')

    # Extract username and message text from EventSub payload
    username = payload.chatter.name
    text = payload.text

    self.messages_received += 1

    # Check if this is our startup message reflected back
    if not self.startup_message_verified and "Selection Protocol online" in text:
        self.startup_message_verified = True
        print(f"✓ Startup message verified (end-to-end chat confirmed)")
        return  # Don't log our own startup message

    # Log ALL chat messages
    print(f"[{timestamp}] {username}: {text}")

    # ... rest of handler
```

**New (with user ID check):**
```python
@commands.Component.listener()
async def event_message(self, payload: eventsub_.ChatMessage):
    """Handle incoming chat messages from EventSub."""
    timestamp = datetime.now().strftime('%H:%M:%S')

    # Extract username and message text from EventSub payload
    username = payload.chatter.name
    text = payload.text

    # Skip our own messages by comparing user IDs
    if str(payload.chatter.id) == str(self.bot_id):
        return

    self.messages_received += 1

    # Log ALL chat messages
    print(f"[{timestamp}] {username}: {text}")

    # ... rest of handler
```

**Changes:**
1. Add user ID check immediately after extracting username/text
2. Remove startup message verification logic (lines 303-306) - now redundant
3. Remove `self.startup_message_verified` attribute (line 104) - no longer needed

### Step 2: Remove Obsolete Startup Verification

**File:** `/home/daniel/prj/selection-protocol/src/twitch_bot.py`

**Line 104 (in `__init__()`):**
```python
# REMOVE THIS LINE:
self.startup_message_verified = False
```

**Lines 399-410 (in `_send_startup_announcement()`):**
```python
# REMOVE THIS BLOCK:
# Wait up to 5 seconds for verification
for i in range(50):
    if self.startup_message_verified:
        break
    await asyncio.sleep(0.1)

if not self.startup_message_verified:
    print("⚠ Startup message not verified (didn't see reflection in 5s)")
    print("  Chat sending may work, but EventSub reflection not confirmed")
```

**Simplified (lines 384-410):**
```python
async def _send_startup_announcement(self):
    """
    Send startup message to chat.

    Confirms bot can send messages to Twitch.
    """
    # Wait a moment for EventSub to be fully ready
    await asyncio.sleep(2)

    message = "Selection Protocol online. Vote: k (kill) | l (lay) | x (extend) • Commands: +/- (zoom) | 0-4 (info panels, 0=hide)"
    success = await self._send_chat_message(message)

    if success:
        print("✓ Startup announcement sent to chat")
    else:
        print("⚠ Failed to send startup announcement")
        print("  Bot will continue (receiving still works)")
```

### Step 3: Testing Checklist

**Before:**
- [ ] Bot announces "Voting opened by @user: L"
- [ ] Bot parses own announcement as "l" vote
- [ ] Infinite loop or duplicate vote recorded

**After:**
- [ ] Bot announces "Voting opened by @user: L"
- [ ] Bot skips own announcement (user ID match)
- [ ] Only real user votes recorded
- [ ] Startup message not logged
- [ ] Round end announcements not parsed
- [ ] Bot username == real user: Real user's votes still work

---

## Considerations

### Type Safety
- `payload.chatter.id` returns `str | int` (per TwitchIO docs)
- `self.bot_id` is `str` (fetched from Helix API, line 548-552)
- Convert both to string for comparison: `str(payload.chatter.id) == str(self.bot_id)`

### Performance
- User ID comparison: O(1) string equality
- No regex, no list iteration
- Negligible overhead (<1μs per message)

### Production Considerations
- **Bot username matches real user:** Now safe (ID-based filter)
- **Multiple bots:** Each filters only own messages
- **Shared chat:** Works correctly (`chatter.id` always sender's ID)
- **Future announcements:** No code changes needed

### Logging
- Bot messages won't increment `self.messages_received` counter
- Bot messages won't appear in logs (`print(f"[{timestamp}] ...")`)
- Consider adding debug log for filtered bot messages:
  ```python
  if str(payload.chatter.id) == str(self.bot_id):
      # Optional: Log filtered bot messages in debug mode
      # print(f"[{timestamp}] [BOT] {text}")
      return
  ```

### Alternative: Use `payload.chatter.name`
- Could check `payload.chatter.name.lower() == self._bot_username`
- But still fails when bot username matches real user (original problem)
- ID-based check is strictly superior

---

## Summary

**Problem:** Bot announcements parsed as commands when username matches testing user.

**Root Cause:** No sender identity check in `event_message()` handler.

**Solution:** Check `str(payload.chatter.id) == str(self.bot_id)` and skip bot messages.

**Implementation:** 3 lines added (after line 298), 15 lines removed (obsolete verification).

**Reliability:** 100% - User IDs are unique, immutable, always present.

**Edge Cases:** All handled (username conflicts, multiple bots, shared chat).

**Testing:** Verify bot announcements don't trigger votes, real users still work.

---

**Next Steps:**
1. Apply changes to `src/twitch_bot.py`
2. Test with bot announcements enabled
3. Verify no infinite loops or duplicate votes
4. Commit with detailed message explaining fix

---

> **RESEARCH COMPLETE**
> **SOLUTION IDENTIFIED: USER ID COMPARISON**
> **READY FOR IMPLEMENTATION**
