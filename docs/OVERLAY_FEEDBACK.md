# Sprint: Overlay State Feedback

**Created:** 2025-11-28
**Status:** Planning
**Branch:** feature/overlay-state-feedback (create from main)

---

## Goal

Close the feedback loop between chat commands and game state. Participants should see what's happening, what got rejected, who's responsible for cooldowns, and gauge their own latency.

---

## Core Components

### 1. Command History List

**Single chronological list of all commands (accepted + rejected).**

| Element | Treatment |
|---------|-----------|
| Column 1 | Command char (single char, fixed width) |
| Column 2 | Username (max length, alpha fade right on truncation) |
| Accepted | Normal text |
| Rejected | Strikethrough (subtle, uses text itself as indicator) |

**Visual aging:**
- Newest entries: full opacity, normal size
- Older entries: decreasing alpha, decreasing font size
- Scrolls/ages out naturally, no explicit timestamps

**Purpose:** "What just happened" — shows rhythm of commands, who's participating, what's failing.

### 2. Cooldown Elements

**Persistent display for each cooldown group showing timer + attribution.**

| Element | Content |
|---------|---------|
| Label | Command/group name (e.g., "Zoom In", "Info Panels") |
| Timer | Seconds remaining, ticking down |
| Attribution | Username who triggered cooldown |

**Visual states:**
- Active cooldown: Bright/prominent, username solid
- Cooldown expiring: Username fades as timer approaches zero
- Ready (no cooldown): Element dims, username fully faded or hidden

**Purpose:** "What can happen next and why not" — shows constraints and accountability.

### 3. Zoom Distance Indicator

**Current zoom distance from initial state.**

- Value: Signed integer (-15 to +15)
- Visual: Consider bar/gauge showing position in range
- Updates on each zoom command

**Purpose:** Context for why zoom cooldowns vary.

---

## Visual Design Principles

- **Monospace throughout** — terminal aesthetic, predictable column alignment
- **Strikethrough over icons** — rejection is visual treatment, not separate symbol
- **Alpha fade for aging/truncation** — softer than hard cuts or ellipsis
- **Dim when ready, bright when constrained** — attention on blockers, not openings
- **Username truncation via alpha fade** — avoids `...` breaking grid

---

## Information Hierarchy

1. **Primary:** Current cooldown constraints (what's blocked)
2. **Secondary:** Recent command history (what just happened)
3. **Tertiary:** Zoom distance, other metadata

---

## Layout TBD

Placement relative to existing overlay elements (vote display, timer, pie chart). Options:
- Left edge (opposite vote display)
- Below vote container
- Separate panel/region

Decide during implementation based on visual balance.

---

## Future Considerations (Not This Sprint)

- **Voting progress sparkline** — compact momentum visualization
- **Per-user lag indicator** — track round-trip for individual viewers
- **Command statistics** — acceptance rate, rejection reasons breakdown
- **Highlight own entries** — if viewer identity trackable, emphasize their commands

---

## Acceptance Criteria

- [ ] Commands appear in history list within 1s of execution
- [ ] Rejected commands visually distinct (strikethrough)
- [ ] History ages out gracefully (alpha + size reduction)
- [ ] Cooldown timers tick down in real-time
- [ ] Cooldown attribution shows username who triggered
- [ ] Attribution fades as cooldown expires
- [ ] Zoom distance displayed and updates on change
- [ ] All elements monospace, consistent with overlay aesthetic
- [ ] No performance degradation with sustained command flow

---

## Technical Notes

- Cooldown data already broadcast via `game_state_update` SocketIO event
- Command history may need new event or extension of existing
- Consider max history length (DOM element count)
- CSS handles aging animation (no JS timers per element)

---

## Open Questions

1. Max history entries before removal? (10? 20? viewport-based?)
2. Fade timing curve for aging entries? (linear? ease-out?)
3. Username max length before truncation? (12 chars? 16?)
4. Cooldown element layout (horizontal row? vertical stack?)

---

## Dependencies

- Existing game_state.py cooldown tracking (complete)
- SocketIO broadcast infrastructure (complete)
- Base CSS design tokens (complete)

---

> **Sprint Focus:** Feedback loop, not polish. Get information visible first, refine aesthetics after validation.