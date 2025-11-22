# Voting Rules - Selection Protocol

**Status:** Locked for Phase 1 MVP
**Last Updated:** 2025-11-21

---

## Core Principle

**Server-authoritative, dynamic timer system with ratio-based decision making.**

Votes adjust the round duration in real-time. A clear majority (>33%) of K or L ends the round with action. Ties and weak majorities result in no action (X behavior).

---

## Round Lifecycle

### 1. Waiting State
- **Timer:** Not running
- **Available votes:** None
- **State:** Round is ready but dormant
- **Trigger:** First K or L vote cast

### 2. Voting Active
- **Timer:** Counts down from initial limit (30s for first voter)
- **Available votes:** K, L, X (X unlocks when first K/L cast)
- **Timer limit:** Recalculates continuously based on current vote ratios
- **Countdown rate:** 1 second per second when ratios stable

### 3. Timer Expires
- **Trigger:** Timer reaches 0
- **Action:** Determine winner, execute if K or L
- **Next:** Reset round, return to Waiting State

---

## Timer Function (Dynamic)

### Formula
Vote ratios map to timer limit on continuous scale:

| Ratio (K:L:X) | Timer Limit | Scenario |
|---------------|-------------|----------|
| 1:0:0 or 0:1:0 | 30s | Unanimous action |
| 1:1:0 | 60s | Split decision (K vs L) |
| 1:0:1 or 0:1:1 | 60s | Action vs Extend |
| 1:1:1 | 90s | 3-way split |
| 1:2+:1 | 120s | X dominant |

### Behavior
- **Stable ratios:** Timer counts down 1s/s toward limit
- **Ratio changes:** Timer limit recalculates instantly
  - If new limit > current timer: Timer extends up
  - If new limit < current timer: Timer accelerates down
- **Visual:** Timer jumps are visible (more dramatic with few voters)

### Examples

**Example 1: Solo voter decides quickly**
```
t=0s:  User votes K (1:0:0)
       Timer starts at 30s, counting down
t=30s: Timer expires, K wins
       Execute: Delete keypress sent to game
```

**Example 2: Debate extends timer**
```
t=0s:  User1 votes K (1:0:0)
       Timer: 30s
t=10s: User2 votes L (1:1:0)
       Timer limit jumps to 60s
       Timer now at 50s, continues counting down
t=25s: User3 votes X (1:1:1)
       Timer limit jumps to 90s
       Timer now at 65s
t=90s: Timer expires, neither K nor L > 33%
       Result: No action (X wins)
```

**Example 3: Late swing**
```
t=0s:  3 users vote K (3:0:0)
       Timer: 30s
t=15s: 2 users vote L (3:2:0)
       Timer limit: 60s (split)
       Timer extends to 45s
t=20s: 1 more L (3:3:0)
       Ratio: 50% K, 50% L (tie)
       Timer limit: 60s
       Timer at 40s
t=60s: Timer expires, K=L (tie)
       Result: No action (treated as X win)
```

---

## Vote Mechanics

### Casting Votes
- **One person, one vote:** Latest vote replaces previous
- **Vote changes:** Allowed any time during round
- **No expiration:** Votes persist until round ends (Phase 1 simplification)
- **No spam protection:** Rapid changes allowed (Phase 1 simplification)

### First-L Claimant (Lineage Naming Rights)
- **First L voter** gets claim (by timestamp)
- **Switching away from L** forfeits claim to next earliest L voter
- **Claim persists** through vote changes until forfeited
- **Used in Phase 2:** Winning L voter's username tags parent bibite

---

## Winner Determination

### Decision Logic

**K wins IF:**
- K votes > 33% of total votes, AND
- K votes > L votes

**L wins IF:**
- L votes > 33% of total votes, AND
- L votes > K votes

**X wins (no action) IF:**
- Neither K nor L > 33%, OR
- K votes = L votes (tie)

### Execution
- **K wins:** Send `Delete` keypress to game
- **L wins:** Send `Insert` keypress to game (Phase 2: tag with first-L claimant's username first)
- **X wins:** No keypress sent, round ends peacefully

### Edge Cases
- **Zero votes:** Round never starts (waiting state persists)
- **All X votes:** Neither K nor L > 33% → No action
- **Empty stream mid-round:** Existing votes remain, timer continues

---

## Examples (Detailed Walkthroughs)

### Scenario 1: Unanimous Quick Kill
```
Users: Alice
Votes: K
Ratio: 1:0:0 (100% K)
Timer: 30s
Result: K wins, Delete sent after 30s
```

### Scenario 2: Split Decision Favors L
```
Users: Alice, Bob, Carol, Dave
Votes: K, L, L, L
Ratio: 1:3:0 (25% K, 75% L)
Timer: ~50s (between 30s and 60s, closer to unanimous)
Result: L > 33% AND L > K → L wins, Insert sent
```

### Scenario 3: X Delays, No Consensus
```
Users: Alice, Bob, Carol, Dave
Votes: K, L, X, X
Ratio: 1:1:2 (25% K, 25% L, 50% X)
Timer: 120s (X dominant)
Result: Neither K nor L > 33% → No action
```

### Scenario 4: Perfect Tie
```
Users: Alice, Bob, Carol, Dave
Votes: K, K, L, L
Ratio: 2:2:0 (50% K, 50% L)
Timer: 60s (split)
Result: K = L (tie) → No action (treated as X win)
```

### Scenario 5: Late X Voter Prevents Action
```
t=0s:  Alice votes K, Bob votes L (1:1:0, timer 60s)
t=30s: Carol votes L (1:2:0, L>33%, L>K)
       Timer extends, L on track to win
t=50s: Dave votes X (1:2:1, 25%K, 50%L, 25%X)
       L still > 33% and L > K
       Timer extends toward 90s
t=90s: L wins (50% > 33% AND L > K)
       Execute: Insert sent
```

---

## Phase 1 Simplifications (MVP)

**Deferred to Phase 2:**
- ❌ Vote expiration (X votes lasting 30s)
- ❌ Anti-spam mechanics (toggle/dilution)
- ❌ Explicit tie-break window (10s extra time)
- ❌ Lineage tagging execution (mouse clicks)
- ❌ Timer jump animations (+30s, -15s visual)

**Phase 1 keeps:**
- ✅ Dynamic timer based on ratios
- ✅ Simple vote replacement (latest wins)
- ✅ First-L claimant tracking (display only)
- ✅ Ratio-based winner determination
- ✅ Automated keypress execution

---

## Implementation Notes

### vote_manager.py Requirements
1. Track votes per user: `{username: {'vote': 'k', 'timestamp': datetime}}`
2. Calculate ratio continuously: `(k_count, l_count, x_count)`
3. Compute timer limit from ratio: `get_timer_limit(k, l, x) -> seconds`
4. Broadcast state every second: `{k_votes, l_votes, x_votes, time_remaining, ...}`
5. Detect timer expiry: When `time_remaining <= 0`
6. Determine winner: Apply >33% AND > opponent logic
7. Execute action: Call `game_controller.send_keypress()`
8. Reset round: Clear votes, stop timer, await next K/L

### Overlay Display Requirements
- Show K/L/X vote counts (real-time)
- Show timer countdown (server-driven, no client state)
- Show first-L claimant under L count
- Animate pie chart when ratios change
- Color timer: Green (>15s) → Yellow → Red (0s)

---

## Testing Checklist

- [ ] Solo voter K wins after 30s
- [ ] Solo voter L wins after 30s
- [ ] 1K vs 1L creates 60s timer
- [ ] Adding X extends timer toward 90-120s
- [ ] Timer recalculates when votes change
- [ ] K>33% AND K>L triggers Delete
- [ ] L>33% AND L>K triggers Insert
- [ ] Tie (K=L) results in no action
- [ ] Neither >33% results in no action
- [ ] All X votes result in no action
- [ ] First-L claim transfers when voter switches away
- [ ] Round resets after execution
- [ ] New round doesn't start until first K/L

---

> VOTING RULES LOCKED
> PHASE 1 MVP SPECIFICATION
> READY FOR IMPLEMENTATION

🔥
