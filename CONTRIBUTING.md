# Contributing to Selection Protocol

**Purpose:** Development workflow standards for consistent, traceable work.

---

## Issue-Driven Development

All work starts with an issue. No commits without an issue reference.

### Core Principles

**Explanatory Over Prescriptive**
- Focus on WHY (problem, root cause) not HOW (implementation)
- Success criteria over recipes
- Reasoning chain over solution details

**Scope Boundaries Are Sacred**
- State what's in/out explicitly
- Link dependencies and related issues
- Never work around missing scope - create dependency issue instead

**Block Early, Block Often**
- Missing dependency → Create issue, label `blocked`, link it
- Under-specified → Label `needs-discussion`
- Needs refactor → Create refactor issue first, don't work around

**Use Labels as System Feedback**
- Can't label it `ready`? Make the blocker explicit

### Issue Template

Adapt as needed - minimal is fine for simple fixes:

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

### Labels

- `needs-discussion` - Under-specified, needs breakdown
- `blocked` - Waiting on dependency (link it)
- `ready` - Can be implemented
- `deferred` - Good idea, wrong time

### Anti-Patterns

❌ "Add time.sleep(0.2) after all clicks" (prescriptive implementation)
✅ "Improve game automation reliability" (problem statement)

❌ "While we're here, also refactor X" (scope creep)
✅ "Fix Y. Created #A for X refactor." (separate concerns)

❌ "We need to do X" (missing reasoning)
✅ "Problem Y because Z. X solves Y by addressing Z." (reasoning chain)

**Remember:** Issues are discussion artifacts, not task lists. Start rough, refine through comments. Block early - the issue system is feedback.

---

## Commit Standards

**All commits must reference an issue number.**

### Format

```
Brief description of change (#N)

[Optional 1-2 sentence context if title unclear]

Closes #N (if this commit completes the issue)
```

### Examples

**Single commit (minimal):**
```
Fix OAuth token refresh on 401 errors (#14)

Closes #14
```

**Single commit (with context):**
```
Add refresh retry logic to _send_chat_message (#14)

Bot was losing send permissions after token expiry. Retry with refreshed token on 401.

Closes #14
```

**Multi-commit sequence:**
```
Add refresh_access_token import (#14)
```
```
Implement 401 retry with token refresh (#14)
```
```
Complete OAuth refresh implementation (#14)

Closes #14
```

**Ad-hoc trivial fix:**
```
Fix typo in README (#16)

Closes #16
```

### Rationale

**Code details belong in the code** (implementation)
**Discussion belongs in issues** (reasoning, alternatives, trade-offs)
**Commits link the two** (traceability)

No code snippets, line numbers, or verbose implementation details in commit messages. If it's important, put it in:
- Issue comments (for discussion/decisions)
- Code comments (for implementation notes)
- Commit title + issue link (for traceability)

### Multi-Commit Workflow

When an issue requires multiple commits:
- **Early commits:** Reference issue `(#N)` but don't close
- **Final commit:** Add `Closes #N` to auto-close issue

### Ad-Hoc Issues

For trivial fixes, create minimal issue on-the-fly:

```bash
# Create issue
gh issue create --title "Fix typo in README" --body "Spotted in Quick Start" --label bug
# Returns #16

# Commit with reference
git commit -m "Fix typo in README (#16)"

# Close immediately
gh issue close 16
```

---

## Session Flow

1. **Start:** `gh issue list` - See what's available
2. **Point at issue:** Choose one (any state: `needs-discussion`, `blocked`, `ready`)
3. **Assess state:**
   - `needs-discussion` → Refine, break down, spec
   - `blocked` → Work on blocker or create new dependency
   - `ready` → Implement
4. **Work:** Make changes, commit with issue reference
5. **Update:** Link commits in issue, close when complete

**Issue scope = session scope.** Scope creep? Create new issue.

---

## Code Standards

(Future: style guide, testing patterns, etc.)

---

**Process over outcomes. Build systems, not one-offs.**
