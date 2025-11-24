# Selection Protocol - Chat UX Specification

**Version:** 0.1.0
**Status:** Draft
**Last Updated:** 2025-11-24

---

## Design Philosophy

### Core Principle: Single Character Democracy

Users interact through single-character commands. The interface is designed for:

- **Minimal friction:** One keypress = one action
- **Expressive optional context:** Repetition and commentary allowed but ignored
- **Rate limit as resource:** Users manage their Twitch message budget strategically
- **Timing criticality:** Position within a window matters (races, thresholds)
- **Scalable chaos:** System works for 1 user or 10,000 users

### The 99.9% / 0.1% Ratio

The simulation runs autonomously 99.9% of the time. Chat's 0.1% intervention creates butterfly effects that ripple through generations. Commands should feel like discrete moments of divine intervention, not continuous control.

### Chat as Visual Medium

The chat stream itself becomes content. Floods of `k k k l k x l` create visual texture. The overlay cuts through noise with clean data visualization. Chaos is aesthetic, not failure.

---

## Command Syntax

### General Pattern

```
<command_char>[<repetition>][<whitespace><commentary>]
```

**Parsing rule:** Extract FIRST valid command character(s) before word boundary. Everything after first whitespace is commentary (ignored by parser, visible in chat). Inconsistent first word invalidates.

**Examples:**
```
# valid command/vote == first word == repeats of one char only.
"k"                    → command: k
"k boring kill it"     → command: k
"kkKkK! IT MUST DIE"   → command: k
"l first!"             → command: l
"lllllll"              → command: l
"x let it live longer" → command: x

"I think k"            → command: none (no action: "i")
"let it live!"         → command: none (first word contains multiple chars)
```

### Case Sensitivity

All commands are **case-insensitive**. Internally normalized to lowercase.

```
"K" "k" "kKkK" → all parse as: k
```

---

## Command Groups

### Group 1: Primary Votes (KLX)

**Purpose:** Core selection cycle voting
**Cooldown:** Per-user, resets each vote window
**Threshold:** None (every vote counts equally)

| Char | Action | Notes |
|------|--------|-------|
| `k` | Kill current bibite | Ends life, camera moves to next |
| `l` | Lay / Give Life | First `l` timestamp claims lineage naming rights |
| `x` | Extend (do nothing) | Continue observing current bibite |

**Vote mechanics:**
- One vote per user per window (latest vote replaces previous)
- Majority wins
- Tie-break window: switch from first `l` to last `l` claimant

**First-L Racing:**
- Timestamp of first `l` vote per user tracked
- If user changes FROM `l`, they forfeit claim
- Current first-L claimant shown in overlay
- On `l` victory, first-L user gets lineage tagged

### Group 2: Camera Zoom (+ -)
At start, camera assumed at zoom level 0 (int). Relative changes are negative for zoom out, positive for zoom in. Each action has own cooldown, which increases with distance from 0, while the other remains at base cooldown.

**Purpose:** Community-controlled zoom level
**Cooldowns:**
    - Seperate per direction
    - Base: 1 second
    - Multiplier: 1.1 * distance

| Char | Action |
|------|--------|
| `+` | Zoom in |
| `-` | Zoom out |

### Group 3: View Controls (0-4)

**Purpose:** Toggle in-game UI elements
**Cooldown:** Global, 10 seconds between changes (timer to show on overlay). May be conditionally variable later.

| Char | Action | Notes |
|------|--------|-------|
| `1` | Open info panel 1 | Species + stats |
| `2` | Open info panel 2 | Genes |
| `3` | Open info panel 3 | Biology |
| `4` | Open info panel 4 | Brain network |
| `0` | Close all panels | Master toggle |


### Group 5: Reserved/Future


| Char | Action | Notes |
|------|--------|-------|
| `a` | Select option A | Context-dependent |
| `b` | Select option B | Context-dependent |
| `c` | Select option C | Context-dependent |
| `d` | Select option D | Context-dependent |
| `e` | Select option E | Context-dependent |

| Char | Reserved For | Notes |
|------|--------------|-------|
| `?` | Help request | Triggers bot whisper with commands |
| `!` | Admin prefix | `!command` style for elevated functions |
| `@` | User targeting | Future: `@username` interactions |
| `#` | Hashtag/tagging | Future: `#teamname` affiliations |


---


## Design Principles Recap

1. **Single character = single action.** Minimal friction, maximum accessibility.

2. **Rate limit is a resource.** Users manage their message budget strategically.

3. **Timing matters.** First-L races, threshold windows, vote position.

4. **Thresholds prevent flickering.** Community consensus required for persistent changes.

5. **Chaos is aesthetic.** Chat flood is content, overlay cuts through noise.

6. **Extensible by design.** New command groups slot in cleanly.

7. **State is observable.** Everything needed for overlay is centrally accessible.

---

*Selection Protocol Chat UX Spec v0.1.0*