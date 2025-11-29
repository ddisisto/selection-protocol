# Issue Creation Guide

**Purpose:** Issues explain problems and reasoning, not prescriptive implementation.

## Core Principles

**Explanatory Over Prescriptive**
- Focus on WHY (problem, root cause) not HOW (implementation)
- Success criteria over recipes
- Reasoning chain over solution details

**Scope Boundaries Are Sacred**
- State what's in/out explicitly
- Link dependencies and related issues
- Never work around missing scope - create dependency issue instead

**Block Early, Block Often**
- Missing dependency → Create issue, label `blocked`, link
- Under-specified → Label `needs-discussion`
- Needs refactor → Create refactor issue first, don't work around

**Use Labels as System Feedback**
- Can't label it `ready`? Make the blocker explicit.

## Simple Template (Adapt as Needed)

```markdown
## Problem
[What's broken/missing and why it matters]

## Scope
**In:** [What this delivers]
**Out:** [What this doesn't - link related issues]

## Approach (if known)
[High-level strategy + reasoning, or "needs discussion"]

## Dependencies
- Blocks: #X
- Blocked by: #Y
- Related: #Z
```

## Labels

- `needs-discussion` - Under-specified, needs breakdown
- `blocked` - Waiting on dependency (link it)
- `ready` - Can be implemented
- `deferred` - Good idea, wrong time

## Anti-Patterns

❌ "Add time.sleep(0.2) after all clicks" (prescriptive implementation)
✅ "Improve game automation reliability" (problem statement)

❌ "While we're here, also refactor X" (scope creep)
✅ "Fix Y. Created #A for X refactor." (separate concerns)

❌ "We need to do X" (missing reasoning)
✅ "Problem Y because Z. X solves Y by addressing Z." (reasoning chain)

---

**Issues are discussion artifacts, not task lists.**
**Start rough, refine through comments.**
**Block early - the issue system is feedback.**
