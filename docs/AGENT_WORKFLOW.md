# Agent-Driven Workflow

**Purpose:** Context management pattern for complex, well-scoped work.

**When to load this doc:** Session evaluates own context budget, scope clarity, and alignment depth. Use this pattern when conditions align.

---

## Pattern Overview

Delegate implementation to Task agents while main session conserves context for coordination.

**Main session:** High-level coordination, strategic alignment, issue creation
**Task agents:** Deep implementation, file reading/writing, testing, documentation

**Results:** Permanent in issues (comments, close messages), no context cost to retrieve

---

## When To Use

**Use agent-driven workflow when ALL true:**
- ✅ Deep alignment established (user + session agree on architecture/approach)
- ✅ Work is complex/multi-step (3+ files, research → implement → test chain)
- ✅ Scope clearly defined (fits CONTRIBUTING.md issue template)
- ✅ Context budget constrained (main session >60% used)
- ✅ No `needs-discussion` label active in context hierarchy

**Use direct implementation when ANY true:**
- ❌ Alignment unclear (need discussion first)
- ❌ Work is trivial (single file, <20 lines changed)
- ❌ Scope is fuzzy (exploration, discovery)
- ❌ High interactivity needed (rapid user back-and-forth)
- ❌ Context budget healthy (<50%, no delegation needed)

---

## The Pattern

### Phase 1: Establish Deep Alignment

**Objective:** User and session agree on architecture/approach before implementation.

1. **Discuss broadly** - No assumptions, explore options
2. **Propose architecture** - Session suggests approach, user confirms/refines
3. **Document design** - Create design doc (e.g., `docs/ARCHITECTURE.md`)
4. **Merge non-breaking** - Establish target state, doesn't break current code
5. **Verify alignment** - Both parties confident in direction

**Output:** Design doc merged to main, shared understanding established

---

### Phase 2: Break Down Work

**Objective:** Create granular issues with sacred scope boundaries.

1. **Identify sub-tasks** - Break work into independent units
2. **Create issues** - One per sub-task, CONTRIBUTING.md discipline:
   - Explanatory problem statement (WHY, not HOW)
   - Explicit scope boundaries (in/out)
   - Success criteria (not implementation steps)
   - Dependencies (blocks/blocked-by)
3. **Label appropriately:**
   - `ready` - Can be implemented now
   - `blocked` - Waiting on dependency (link it)
   - `needs-discussion` - Scope unclear, needs human input
4. **Order dependencies** - Create chain: #A → #B → #C

**Output:** Stack of ready issues, clear dependency order

---

### Phase 3: Spawn Agents

**Objective:** Delegate implementation to Task agents with full context.

**Main session (you):**
```
Use Task tool:
- subagent_type: "general-purpose"
- description: "Execute #N [brief title]"
- prompt:
  """
  Execute issue #N: [title]

  **Your task:**
  [1-5 concrete steps based on issue scope]

  **Reference:**
  - Issue #N: [github url]
  - Design doc: docs/ARCHITECTURE.md
  - Current code: src/file.py lines X-Y

  **Success criteria:**
  [Copy from issue]

  **Report back:**
  - What files you changed
  - What you tested
  - Any issues encountered
  - Whether it's ready to commit
  """
```

**Agent receives:**
- Full project context (all prior conversation)
- Specific issue scope (clear boundaries)
- Success criteria (knows when done)

**Agent executes:**
- Reads files, searches code
- Implements changes
- Tests functionality
- Documents in issue comments
- Returns final report

**Output:** Agent report with implementation details

---

### Phase 4: Coordinate Flow

**Objective:** Validate results, create next issue, maintain momentum.

**Main session (you):**
1. **Validate agent report** - Check files changed, test results
2. **Commit changes** - Reference issue in commit message
3. **Close issue** - Add agent findings to close comment
4. **Create next issue** - If chain continues (#B after #A complete)
5. **Repeat Phase 3** - Spawn next agent

**If agent reports scope issues:**
- Agent labels issue `needs-discussion`
- Agent explains what's unclear in issue comment
- **Stop chain** - User (human) decides next move
- This is the **escape valve** - prevents misalignment

**Output:** Chain progresses, or stops for human input

---

## Key Principles

### 1. Deep Alignment First
**Never spawn agents without alignment.**

- User and session must agree on architecture/approach
- Document alignment in design doc or issue discussion
- Alignment answers: "What are we building and why?"
- No agent spawning until this is solid

**Escape valve:** If alignment unclear during execution, agent labels `needs-discussion`

---

### 2. Sacred Scope Boundaries
**Issue scope = agent scope. Period.**

- Explicit in/out boundaries (CONTRIBUTING.md style)
- If agent discovers scope creep → create new issue, don't expand
- If scope unclear → label `needs-discussion`, wait for human
- "While we're here" is forbidden (separate issue instead)

**Escape valve:** Agent refuses to expand scope, creates follow-up issue reference

---

### 3. Human Is Final Arbiter
**User (human) makes all strategic decisions.**

- Agent finds scope unclear → labels `needs-discussion`, waits
- Agent discovers architectural conflict → labels `needs-discussion`, explains
- Main session uncertain → asks user, doesn't guess
- User overrides any agent/session recommendation

**Escape valve:** `needs-discussion` label blocks agent spawning

---

### 4. Context Budget Conservation
**Main session conserves, agents burn.**

- Main session: High-level only (coordination, validation, issue creation)
- Agents: Deep details (grep, file reading, implementation)
- Results in issues: Permanent record, no re-reading cost
- Context resets per agent: Each agent has fresh 200k budget

**Benefit:** Main session can coordinate 5+ issues without exhausting budget

---

### 5. Issue-Driven Everything
**All work through issues. No exceptions.**

- CONTRIBUTING.md already mandates this (we're extending it)
- Issues are coordination units for agents
- Issue comments are results documentation
- Closed issues are searchable knowledge base
- Commits reference issues (traceability)

**Benefit:** Future sessions can grep issue history, no context load needed

---

## Anti-Patterns

**❌ Spawning agents before alignment**
- Result: Agent implements wrong thing, wastes budget
- Fix: Establish alignment first (Phase 1)

**❌ Vague issue scope**
- Result: Agent labels `needs-discussion`, blocks chain
- Fix: Write clear scope boundaries before spawning

**❌ Ignoring `needs-discussion` label**
- Result: Misalignment propagates, rework needed
- Fix: Stop chain, get user input, realign

**❌ Main session doing implementation**
- Result: Context budget exhausted, can't coordinate
- Fix: Delegate to agents, stay high-level

**❌ Agent expanding scope**
- Result: Scope creep, unpredictable results
- Fix: Agent creates follow-up issue, doesn't expand

**❌ Spawning agents for trivial tasks**
- Result: Overhead exceeds benefit, slower than direct
- Fix: Use direct implementation for simple tasks

---

## Example: Issue #23 (Mod API Architecture)

**What we did (successful pattern):**

### Phase 1: Alignment
- User: "Review mod API architecture"
- Session: Discussed broadly, no assumptions
- Session: Proposed HTTP-based architecture
- User: Confirmed, refined details
- Output: `docs/MOD_API_ARCHITECTURE.md` merged to main

### Phase 2: Breakdown
- Created #27: Find Unity API methods (research)
- Created #28: Implement C# mod endpoints (implement)
- Created #29: Integrate Python server (integrate)
- Labeled all `ready`, dependency chain: #27 → #28 → #29

### Phase 3: Execution
- Spawned agent for #27 → decompiled game, found methods, documented in issue
- Spawned agent for #28 → wrote C# code, tested endpoints, closed issue
- Spawned agent for #29 → migrated Python code, tested integration, closed issue

### Phase 4: Results
- All 3 issues completed successfully
- Main session conserved context (stayed ~60% throughout)
- Results documented in issue comments (permanent record)
- Chain completed in single session

**Why it worked:**
- ✅ Deep alignment first (architecture agreed before implementation)
- ✅ Clear scope boundaries (each issue well-defined)
- ✅ Context budget managed (agents burned budget, session coordinated)
- ✅ No `needs-discussion` blocking (all issues ready)
- ✅ Results captured in issues (searchable, permanent)

---

## Success Metrics

**Healthy agent-driven workflow shows:**
- Main session context budget stays <70%
- Issues close with detailed findings in comments
- No scope creep (agents respect boundaries)
- Fast iteration (spawn → execute → validate → next)
- Permanent documentation (future sessions reference issues)

**Unhealthy workflow shows:**
- Main session context exhausted (should have delegated sooner)
- Issues labeled `needs-discussion` mid-chain (alignment was weak)
- Scope expansion (agent or session ignored boundaries)
- Rework needed (misalignment propagated)
- Lost knowledge (results not captured in issues)

---

## When NOT To Use

**Direct implementation is better when:**

1. **Trivial tasks** - Single file, <20 lines, obvious fix
   - Example: Fix typo, adjust constant, add log statement
   - Overhead of spawning agent exceeds benefit

2. **Fuzzy exploration** - Don't know what we're looking for yet
   - Example: "How does lineage tagging work?" (discovery)
   - Agent needs clear goal; exploration is iterative

3. **High interactivity** - Rapid back-and-forth with user
   - Example: Debugging live issue, user testing each change
   - Agent can't interact mid-execution

4. **Unclear alignment** - Architecture/approach still being discussed
   - Example: "Should we use HTTP or gRPC?" (decision pending)
   - Establish alignment first, then delegate

5. **Healthy context budget** - Main session <50% used
   - No need to conserve context yet
   - Direct implementation is faster for simple tasks

---

## Escape Valves (Built-In Safety)

### 1. `needs-discussion` Label
- **Purpose:** Signal that issue scope is unclear or incorrect
- **Who uses:** Agent or main session
- **Effect:** Blocks agent spawning, requires human decision
- **Resolution:** User (human) clarifies scope, removes label

### 2. Agent Report
- **Purpose:** Agent documents findings, flags issues
- **Format:** "What changed, what tested, any problems, ready to commit?"
- **Effect:** Main session validates before committing
- **Resolution:** If issues found, create follow-up issue or realign

### 3. User Override
- **Purpose:** Human makes final call on any decision
- **Authority:** User can override agent/session recommendation
- **Effect:** Agent/session defers to user strategic judgment
- **Resolution:** User provides direction, work continues

### 4. Scope Boundary Enforcement
- **Purpose:** Prevent scope creep during execution
- **Effect:** Agent creates follow-up issue instead of expanding
- **Resolution:** User decides whether follow-up is needed

---

## Quick Decision Tree

```
Is work complex (3+ files OR multi-step)?
├─ No → Direct implementation
└─ Yes
    └─ Is alignment deep (architecture agreed)?
        ├─ No → Establish alignment first
        └─ Yes
            └─ Is scope clear (fits CONTRIBUTING.md)?
                ├─ No → Refine scope first
                └─ Yes
                    └─ Any `needs-discussion` labels in context?
                        ├─ Yes → Resolve first, don't spawn
                        └─ No → ✅ USE AGENT-DRIVEN WORKFLOW
```

---

## Integration with CONTRIBUTING.md

**This pattern extends (not replaces) CONTRIBUTING.md issue workflow:**

- CONTRIBUTING.md: All work starts with issues (universal principle)
- AGENT_WORKFLOW.md: How to delegate issue execution to agents (optional pattern)

**When session loads CONTRIBUTING.md:** Always (core methodology)
**When session loads AGENT_WORKFLOW.md:** Only when conditions met (complexity + alignment + scope clarity)

**Relationship:**
- Issues created per CONTRIBUTING.md standards (explanatory, scoped, labeled)
- Agent execution follows AGENT_WORKFLOW.md pattern (spawn, coordinate, validate)
- Results documented per CONTRIBUTING.md (issue comments, close messages)

---

> "Process over outcomes. Build systems, not one-offs."
> "This workflow IS the system for complex work."

**AGENT-DRIVEN WORKFLOW: DOCUMENTED**
**CONTEXT MANAGEMENT: SYSTEMATIC**
**ESCAPE VALVES: STRONG**
