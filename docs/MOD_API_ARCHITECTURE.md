# Mod API Architecture Design

**Issue:** #23 - Design mod API integration architecture
**Branch:** feature/mod-api-architecture-23
**Status:** Design complete, ready for implementation

---

## Executive Summary

Complete architectural redesign of Python ↔ game integration. Single Python module (`mod_client.py`) provides clean game-semantic interface. All xdotool complexity eliminated. Mod API handles execution details (pause/tag/validate/execute/unpause) in C# where it belongs.

**Key win:** Never say "keypress", "clipboard", or "click" again. Just `mod.kill_target()` and `mod.lay_target(lineage_tag='username')`.

---

## Core Design Principles

### 1. Two Primitives: Target and World

**Target** - The currently focused Bibite (camera subject, vote recipient)
- Actions: `kill_target()`, `lay_target(tag)`, `extend_target()`
- Observable: lineage tag, species, age, energy, can_kill, can_lay

**World** - Simulation environment state
- State: paused, speed (future), view settings
- Controls: `set_pause_state()`, `zoom()`, `set_info_panel()`

**Rationale:** Game semantics, not UI automation. We act on game objects, not windows.

### 2. Single Python Interface

**ONLY `src/mod_client.py` imports requests.**

All other Python modules use clean, Pythonic methods:
```python
from .mod_client import get_mod_client

mod = get_mod_client()
result = mod.kill_target()
result = mod.lay_target(lineage_tag='TwitchUser123')
```

**Rationale:** Single responsibility. Mod communication isolated in one place. Easy to mock for testing. Clear API boundary.

### 3. Fail-Fast Everywhere

**Mod unavailable = crash on startup:**
```python
mod = ModClient()  # Raises ModUnavailableError if mod not responding
```

**Action failures propagate:**
```python
result = mod.kill_target()
if not result.success:
    log_error(result.message)
```

**Rationale:** Project philosophy. Don't fall back to hardcoded values. Make failures visible immediately.

### 4. Complexity Lives in C#

**Python says WHAT, mod says HOW:**

```python
# Python: Simple, declarative
mod.lay_target(lineage_tag='TwitchUser123')
```

```csharp
// C#: Handles all complexity
public void LayTarget(string lineageTag, Action<ActionResult> callback)
{
    EnqueueCommand(() =>
    {
        var target = UserControl.Instance.GetCurrentTarget();

        // Validate
        if (target == null || !target.CanReproduce()) {
            callback(ActionResult.Failure("Cannot reproduce"));
            return;
        }

        // Pause
        bool wasPaused = TimeController.paused;
        if (!wasPaused) TimeController.Instance.TogglePauseGame("base");

        // Tag (direct field access, no clipboard)
        target.genes.lineageTag = lineageTag;

        // Execute
        target.Reproduce();

        // Unpause
        if (!wasPaused) TimeController.Instance.TogglePauseGame("base");

        callback(ActionResult.Success("lay"));
    });
}
```

**Rationale:** C# has full game access. Atomic operations. Better validation. No network round-trips for multi-step sequences.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ vote_manager.py                                             │
│ - Vote tracking, winner determination                       │
│ - Calls: mod.kill_target(), mod.lay_target(tag)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ mod_client.py (SINGLE INTERFACE)                            │
│ - Pythonic methods, game semantics only                     │
│ - Hides REST/JSON, provides clean exceptions                │
│ - ONLY place "import requests" appears                      │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│ mod/ApiHandlers.cs                                          │
│ - HTTP endpoint handlers                                    │
│ - Routes: /target/*, /world/*                               │
│ - Uses ManualResetEvent for sync responses                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ mod/GameController.cs                                       │
│ - Unity game state bridge                                   │
│ - Command queue (background → main thread)                  │
│ - Direct Unity API calls (no keypresses)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Unity Game Internals                                        │
│ - UserControl.Instance.GetCurrentTarget()                   │
│ - bibite.Kill(), bibite.Reproduce()                         │
│ - TimeController.paused, bibite.genes.lineageTag            │
└─────────────────────────────────────────────────────────────┘
```

---

## API Design (Final)

### Python API (mod_client.py)

**Target Actions:**
```python
def get_target_info() -> Optional[TargetInfo]
    """Get info about currently focused Bibite."""

def kill_target() -> ActionResult
    """Execute kill on current target."""

def lay_target(lineage_tag: str) -> ActionResult
    """Execute lay with lineage tag (mod handles pause/tag/execute/unpause)."""

def extend_target() -> ActionResult
    """Extend observation (no-op)."""
```

**World Controls:**
```python
def get_pause_state() -> bool
    """Get current pause state."""

def set_pause_state(paused: bool) -> None
    """Set pause state."""

def zoom(direction: str) -> None
    """Zoom in/out. Direction: 'in' or 'out'."""

def set_info_panel(panel: int) -> None
    """Set info panel (0=hide, 1-4=show panel)."""
```

**Data Types:**
```python
@dataclass
class TargetInfo:
    bibite_id: int
    lineage_tag: str
    species: str
    age: float
    energy: float
    can_kill: bool
    can_lay: bool

@dataclass
class ActionResult:
    success: bool
    action: str
    message: Optional[str] = None
```

**Exceptions:**
```python
class ModError(Exception)
    """Base exception for mod communication failures."""

class ModUnavailableError(ModError)
    """Mod not responding (game not running or mod not loaded)."""

class ActionValidationError(ModError)
    """Action cannot be executed (e.g., target can't lay)."""
```

### C# API Endpoints (mod/ApiHandlers.cs)

**Target Actions:**
```
POST /target/info
    → GetTargetInfo()
    ← {bibite_id, lineage_tag, species, age, energy, can_kill, can_lay} | null

POST /target/kill
    → HandleKillTarget()
    ← {success, action: "kill", message?}

POST /target/lay
    Body: {lineage_tag: str}
    → HandleLayTarget(lineage_tag)
    ← {success, action: "lay", message?}
```

**World Controls:**
```
GET  /world/pause
    → HandleGetPause()
    ← {paused: bool}

POST /world/pause
    Body: {paused: bool}
    → HandleSetPause(paused)
    ← {success: bool}

POST /world/zoom
    Body: {direction: "in" | "out"}
    → HandleZoom(direction)
    ← {success: bool}

POST /world/info_panel
    Body: {panel: 0-4}
    → HandleInfoPanel(panel)
    ← {success: bool}
```

---

## C# Implementation Sketch

### mod/GameController.cs - New Methods

```csharp
// Target info retrieval
public void GetTargetInfo(Action<TargetInfo> callback)
{
    EnqueueCommand(() =>
    {
        var target = UserControl.Instance.GetCurrentTarget();
        if (target == null) {
            callback(null);
            return;
        }

        var info = new TargetInfo {
            bibite_id = target.GetInstanceID(),
            lineage_tag = target.genes.lineageTag,
            species = target.genes.species,
            age = target.age,
            energy = target.body.energy,
            can_kill = true,  // Always can kill
            can_lay = target.CanReproduce()  // Age, energy checks
        };

        callback(info);
    });
}

// Kill action (direct, no keypress)
public void KillTarget(Action<ActionResult> callback)
{
    EnqueueCommand(() =>
    {
        var target = UserControl.Instance.GetCurrentTarget();
        if (target == null) {
            callback(new ActionResult {
                success = false,
                action = "kill",
                message = "No target selected"
            });
            return;
        }

        // Direct method call - no keypress, no UI
        target.Kill();

        callback(new ActionResult {
            success = true,
            action = "kill"
        });
    });
}

// Lay action with lineage tag (atomic operation)
public void LayTarget(string lineageTag, Action<ActionResult> callback)
{
    EnqueueCommand(() =>
    {
        var target = UserControl.Instance.GetCurrentTarget();

        // Validate
        if (target == null) {
            callback(new ActionResult {
                success = false,
                action = "lay",
                message = "No target selected"
            });
            return;
        }

        if (!target.CanReproduce()) {
            callback(new ActionResult {
                success = false,
                action = "lay",
                message = "Target cannot reproduce (age/energy)"
            });
            return;
        }

        // Pause
        bool wasPaused = TimeController.paused;
        if (!wasPaused) {
            TimeController.Instance.TogglePauseGame("base");
        }

        // Tag (direct field access - no clipboard, no UI)
        target.genes.lineageTag = lineageTag;

        // Execute
        target.Reproduce();

        // Unpause
        if (!wasPaused) {
            TimeController.Instance.TogglePauseGame("base");
        }

        callback(new ActionResult {
            success = true,
            action = "lay"
        });
    });
}

// Zoom control (maps to internal zoom methods)
public void Zoom(string direction, Action<bool> callback)
{
    EnqueueCommand(() =>
    {
        // TODO: Find actual zoom methods in decompiled code
        // Likely: CameraController.Instance.ZoomIn() / ZoomOut()
        // Or: UserControl.Instance.HandleZoom(direction)

        if (direction == "in") {
            // Call game's zoom in method
            callback(true);
        } else if (direction == "out") {
            // Call game's zoom out method
            callback(true);
        } else {
            callback(false);
        }
    });
}

// Info panel control (maps to UI visibility)
public void SetInfoPanel(int panel, Action<bool> callback)
{
    EnqueueCommand(() =>
    {
        // TODO: Find actual UI panel methods in decompiled code
        // Likely: UIController.Instance.SetActivePanel(panel)
        // Or: UserControl.Instance.HandleInfoPanelKey(panel)

        callback(true);
    });
}
```

### mod/ApiHandlers.cs - New Endpoints

```csharp
// Add to HandleRequest() routing
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/target/info")
{
    _handlers.HandleGetTargetInfo(response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/target/kill")
{
    _handlers.HandleKillTarget(response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/target/lay")
{
    _handlers.HandleLayTarget(request, response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/world/zoom")
{
    _handlers.HandleZoom(request, response);
}
else if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/world/info_panel")
{
    _handlers.HandleInfoPanel(request, response);
}

// Handler implementations
public void HandleGetTargetInfo(HttpListenerResponse response)
{
    var resetEvent = new ManualResetEvent(false);
    TargetInfo targetInfo = null;

    _gameController.GetTargetInfo(info =>
    {
        targetInfo = info;
        resetEvent.Set();
    });

    if (resetEvent.WaitOne(5000))
    {
        if (targetInfo == null) {
            SendJsonResponse(response, "null", 200);
        } else {
            var json = SerializeTargetInfo(targetInfo);
            SendJsonResponse(response, json, 200);
        }
    }
    else
    {
        SendJsonResponse(response, "{\"error\":\"Timeout\"}", 504);
    }
}

public void HandleKillTarget(HttpListenerResponse response)
{
    var resetEvent = new ManualResetEvent(false);
    ActionResult result = null;

    _gameController.KillTarget(r =>
    {
        result = r;
        resetEvent.Set();
    });

    if (resetEvent.WaitOne(5000))
    {
        var json = SerializeActionResult(result);
        SendJsonResponse(response, json, 200);
    }
    else
    {
        SendJsonResponse(response, "{\"error\":\"Timeout\"}", 504);
    }
}

public void HandleLayTarget(HttpListenerRequest request, HttpListenerResponse response)
{
    // Parse request body
    var body = ReadRequestBody(request);
    var lineageTag = ParseLineageTag(body);

    var resetEvent = new ManualResetEvent(false);
    ActionResult result = null;

    _gameController.LayTarget(lineageTag, r =>
    {
        result = r;
        resetEvent.Set();
    });

    if (resetEvent.WaitOne(5000))
    {
        var json = SerializeActionResult(result);
        SendJsonResponse(response, json, 200);
    }
    else
    {
        SendJsonResponse(response, "{\"error\":\"Timeout\"}", 504);
    }
}
```

---

## Python Migration Examples

### Before (vote_manager.py)

```python
def _execute_winner(self):
    """Execute the winning action and reset for next round."""
    winner = self.get_winner()
    counts = self.get_vote_counts()

    if winner == 'k':
        self.log_action("Winner: K", "Sending Delete keypress")
        result = send_keypress('Delete', self.log_action)
        if result['success']:
            print("✓ EXECUTED: Delete keypress (K wins)")
        else:
            print(f"✗ FAILED: Delete keypress - {result.get('error', 'Unknown error')}")

    elif winner == 'l':
        claimant = self.first_l_claimant or "Unknown"

        # Lineage tagging (complex, 9-step sequence)
        if claimant and self.game_state:
            try:
                apply_lineage_tag(
                    username=claimant,
                    game_state=self.game_state,
                    log_func=self.log_action
                )
                print(f"✓ TAGGED: Lineage tagged with '{claimant}'")
            except TagVerificationError as e:
                self.log_action("Tag verification FAILED", str(e))
                print(f"✗ TAG FAILED: {e}")
            except Exception as e:
                self.log_action("Tagging error", str(e))
                print(f"✗ TAGGING ERROR: {e}")

        # Execute L action
        self.log_action("Winner: L", f"Sending Insert keypress (Claimant: {claimant})")
        result = send_keypress('Insert', self.log_action)
        if result['success']:
            print(f"✓ EXECUTED: Insert keypress (L wins, claimant: {claimant})")
        else:
            print(f"✗ FAILED: Insert keypress - {result.get('error', 'Unknown error')}")
    else:
        # X wins or tie
        self.log_action("Winner: X", "No action (extend)")
        print("→ No action (X wins)")

    # Emit round_end, reset votes
    self.socketio.emit('round_end', {...})
    self.reset_votes()
```

### After (vote_manager.py)

```python
def _execute_winner(self):
    """Execute the winning action via mod API."""
    winner = self.get_winner()
    mod = get_mod_client()

    try:
        if winner == 'k':
            result = mod.kill_target()
            self.log_action("Winner: K", "Kill executed")
            if result.success:
                print("✓ EXECUTED: Kill (K wins)")
            else:
                print(f"✗ FAILED: Kill - {result.message}")

        elif winner == 'l':
            claimant = self.first_l_claimant or "Unknown"
            result = mod.lay_target(lineage_tag=claimant)
            self.log_action("Winner: L", f"Lay executed (tagged: {claimant})")
            if result.success:
                print(f"✓ EXECUTED: Lay (L wins, claimant: {claimant})")
            else:
                print(f"✗ FAILED: Lay - {result.message}")

        else:  # winner == 'x'
            result = mod.extend_target()
            self.log_action("Winner: X", "Extend (no action)")
            print("→ EXECUTED: Extend (X wins)")

        if not result.success:
            self.log_action("Action FAILED", result.message or "Unknown error")

    except ModError as e:
        self.log_action("Mod error", str(e))
        print(f"✗ MOD ERROR: {e}")
        # Fail-open: log and continue

    # Emit round_end, reset votes
    self.socketio.emit('round_end', {...})
    self.reset_votes()
```

**Eliminated:**
- 100+ lines of lineage tagging complexity (game_controller.py)
- Clipboard verification "stuffing trick"
- Context managers for pause/panel state
- Click coordinate configuration
- xdotool dependency
- All keypress mappings

**Gained:**
- Clean, readable code
- Atomic operations (C# handles pause/tag/execute/unpause)
- Better error messages (validation in C#)
- Testability (mock mod_client easily)

---

## Migration Strategy (Clean Break)

**Issue #22 breakdown:**

1. **#22-1: Implement mod target actions**
   - Add `GetTargetInfo()`, `KillTarget()`, `LayTarget()` to GameController.cs
   - Add `/target/*` endpoints to ApiHandlers.cs
   - Find Unity methods in decompiled code (UserControl, Bibite classes)
   - Test with curl/python REPL

2. **#22-2: Implement mod world controls**
   - Add `Zoom()`, `SetInfoPanel()` to GameController.cs
   - Add `/world/zoom`, `/world/info_panel` endpoints
   - Find Unity methods in decompiled code
   - Test with curl/python REPL

3. **#22-3: Create mod_client.py**
   - ✅ Already written (in this branch)
   - Add to requirements.txt: `requests>=2.31.0`
   - Update server.py startup: call `get_mod_client()` early (fail-fast)

4. **#22-4: Migrate vote_manager to mod_client**
   - Replace `send_keypress()` calls with `mod.kill_target()`, `mod.lay_target()`
   - Remove `apply_lineage_tag()` import and calls
   - Remove `game_state` dependency (no longer needed for tagging context)
   - Test vote execution flow end-to-end

5. **#22-5: Migrate game commands to mod_client**
   - Update server.py chat_input handler: zoom/panel via mod_client
   - Remove game_state.handle_command() calls (replaced by mod API)
   - Test chat commands (+/-/0-4) via Twitch bot

6. **#22-6: Delete xdotool code**
   - Delete `src/game_controller.py` (entire file)
   - Delete `src/game_state.py` (entire file)
   - Update imports across codebase
   - Remove xdotool from system dependencies docs
   - Update README.md setup instructions

**Deploy as atomic unit:** All sub-issues merged together, deployed once. Intermediate states not production-ready.

---

## Open Questions (Need Clarification)

### 1. Unity Method Names

**Assumption made:**
- `UserControl.Instance.GetCurrentTarget()` → Bibite
- `bibite.Kill()` → Execute kill
- `bibite.Reproduce()` → Execute lay
- `bibite.CanReproduce()` → Validate lay eligibility

**TODO:** Verify actual method/property names in decompiled code:
```bash
grep -r "GetCurrentTarget\|SelectedBibite\|CurrentTarget" mod/decompiled/
grep -r "class.*Kill\|Kill()" mod/decompiled/
grep -r "Reproduce\|LayEgg" mod/decompiled/
```

### 2. Zoom/Panel Unity Methods

**Need to find:**
- How zoom in/out is handled internally
- How info panel visibility is controlled
- Whether we can call methods directly or need to simulate keypresses

**Search patterns:**
```bash
grep -r "Zoom\|zoom" mod/decompiled/ | grep -i "void\|method\|public"
grep -r "InfoPanel\|Panel\|UI.*Visibility" mod/decompiled/
grep -r "class UserControl" mod/decompiled/ -A 200
```

### 3. Validation Logic Detail

**Question:** Should C# validate all preconditions and return detailed errors?

**Example for lay:**
- Age too young? → `{success: false, message: "Too young (age < 10s)"}`
- Energy too low? → `{success: false, message: "Insufficient energy (< 50)"}`
- Already pregnant? → `{success: false, message: "Already reproducing"}`

**Or:** Just attempt, let Unity handle failure, return generic error?

**Leaning toward:** Detailed validation. Better error messages, better UX.

### 4. Target Selection State

**Question:** When we call `GetCurrentTarget()`, what if no target is selected?

**Assumption:** Returns null, we handle gracefully.

**But consider:** Should we auto-select nearest/oldest/random if no target? Or strict "no target = error"?

**Leaning toward:** Strict. If no target selected, action fails. Let chat/admin handle selection separately (future feature).

### 5. Process Control Integration

**You mentioned:** New issue for Python controlling game launch.

**Question:** Should mod_client have game lifecycle methods?

**Option A:** Keep in mod_client
```python
mod.launch_game()
mod.restart_game()
mod.shutdown_game()
```

**Option B:** Separate module
```python
from .game_process import GameProcess
game = GameProcess()
game.launch()
game.wait_for_mod()  # Blocks until mod API responds
```

**Leaning toward:** Option B. Process control is different concern than game API.

---

## Testing Strategy

### Unit Tests (Python)

**Mock mod_client easily:**
```python
from unittest.mock import Mock

def test_vote_execution():
    mock_mod = Mock()
    mock_mod.kill_target.return_value = ActionResult(success=True, action='kill')

    # Inject mock
    vote_manager._mod_client = mock_mod
    vote_manager._execute_winner()

    mock_mod.kill_target.assert_called_once()
```

### Integration Tests (Mod API)

**Test endpoints directly:**
```bash
# Start game with mod loaded
# Terminal 1: Watch BepInEx log
tail -f ~/.steam/.../BepInEx/LogOutput.log

# Terminal 2: Test endpoints
curl http://localhost:5001/health
curl -X POST http://localhost:5001/target/info
curl -X POST http://localhost:5001/target/kill
curl -X POST http://localhost:5001/target/lay -H "Content-Type: application/json" -d '{"lineage_tag": "TestUser"}'
```

### End-to-End Tests (Vote Flow)

**Manual test sequence:**
1. Start game, load mod
2. Start Python server (verifies mod available)
3. Start Twitch bot
4. Cast votes in chat (k/l/x)
5. Wait for timer expiry
6. Verify action executed in game
7. Check overlay displays correct state

---

## File Size Discipline (Maintained)

**Current mod files:**
- Plugin.cs: 81 lines ✅
- HttpApi.cs: 107 lines ✅
- GameController.cs: 79 lines → **~200 lines** after target/world methods
- ApiHandlers.cs: 112 lines → **~250 lines** after new endpoints

**Projected growth acceptable:**
- GameController.cs stays focused (Unity bridge only)
- ApiHandlers.cs stays focused (HTTP handlers only)
- Each <300 lines, still readable
- Consider splitting if >400 lines

**Python files:**
- mod_client.py: ~260 lines ✅ (single responsibility)
- vote_manager.py: 588 lines → **~450 lines** after simplification ✅
- game_controller.py: DELETED
- game_state.py: DELETED

**Net complexity reduction despite new code.**

---

## Benefits Summary

### Eliminated Complexity

**Python side:**
- ❌ game_controller.py (474 lines) - DELETED
- ❌ game_state.py (708 lines) - DELETED
- ❌ xdotool subprocess calls
- ❌ Clipboard verification "stuffing trick"
- ❌ Context managers for pause/panel state
- ❌ Window focus stealing
- ❌ Click coordinate configuration
- ❌ Timing-dependent operations
- ❌ Retry loops for UI state

**Total:** ~1200 lines of complexity eliminated

### Gained Capabilities

**Python side:**
- ✅ Clean, testable API (mod_client.py)
- ✅ Game-semantic operations (kill/lay, not Delete/Insert)
- ✅ Better error messages (C# validation)
- ✅ Easy mocking for tests
- ✅ Single failure point (mod unavailable = clear error)

**C# side:**
- ✅ Direct game state access
- ✅ Atomic operations (pause/tag/execute/unpause in one call)
- ✅ Better validation (check age/energy before lay)
- ✅ No UI automation workarounds
- ✅ Future: Observable state, event streams

**Total:** ~260 lines of clean, focused code

### Maintenance Wins

**Before:**
- Change lineage tagging → touch 4 files (game_controller, game_state, vote_manager, config.yaml)
- UI coordinates hard to maintain (game resolution changes break it)
- Timing issues require trial-and-error (Proton delays unpredictable)
- Error debugging requires log correlation across xdotool/clipboard/game

**After:**
- Change lineage tagging → touch 1 file (GameController.cs)
- No UI coordinates at all
- No timing issues (synchronous API calls)
- Error debugging clear (mod logs show exact failure point)

---

## Next Steps (Implementation)

1. **Decompile game code** (find Unity method names)
   ```bash
   ./decompile_dll.sh
   grep -r "UserControl\|Bibite\|Kill\|Reproduce" mod/decompiled/
   ```

2. **Implement mod endpoints** (#22-1, #22-2)
   - Add methods to GameController.cs
   - Add routes to HttpApi.cs
   - Add handlers to ApiHandlers.cs
   - Test with curl

3. **Integrate mod_client.py** (#22-3)
   - Add to requirements.txt
   - Update server.py startup
   - Test connection verification

4. **Migrate vote_manager** (#22-4)
   - Replace send_keypress() calls
   - Remove lineage tagging complexity
   - Test vote flow end-to-end

5. **Migrate game commands** (#22-5)
   - Update chat_input handler
   - Remove game_state dependency
   - Test zoom/panel commands

6. **Delete xdotool code** (#22-6)
   - Delete files
   - Update docs
   - Celebrate clean architecture

---

## Philosophical Alignment

**From CLAUDE.md:**
- ✅ "Fail-fast validation" - Mod unavailable = crash
- ✅ "No fallbacks to hardcoded values" - No xdotool fallback
- ✅ "DRY - eliminate duplication" - Single mod_client interface
- ✅ "Single source of truth" - Game semantics live in C#
- ✅ "Extract patterns" - Target/World primitives
- ✅ "Concise communication" - Clean API, no verbosity

**From CONTRIBUTING.md:**
- ✅ "Explanatory over prescriptive" - This doc focuses on WHY
- ✅ "Scope boundaries sacred" - Clear Python/C# responsibilities
- ✅ "Block early, block often" - Open questions documented

**From MODDING_PLAN.md:**
- ✅ "File size discipline" - All files <300 lines
- ✅ "Separation of concerns" - Each layer single responsibility
- ✅ "Source parameter pattern" - Pause uses "base" source
- ✅ "Threading pattern" - Command queue maintained

---

## Final Thoughts

This architecture represents the **ideal end state** for Python ↔ game integration. It's:

- **Simple** - One interface, clear semantics
- **Testable** - Easy to mock, clear failure modes
- **Maintainable** - Changes localized, no ripple effects
- **Extensible** - Add endpoints without redesign
- **Correct** - Game logic in game layer, orchestration in Python

The migration is aggressive (delete ~1200 lines, add ~260), but the result is **objectively better** in every dimension:
- Fewer lines
- Clearer intent
- Better errors
- Easier testing
- No workarounds

**Rip the bandaid. Ship it.**

---

> "Process over outcomes. Build systems, not one-off hacks."
> "Fail-fast: Prototype before committing. (We prototyped pause control. Pattern proven.)"
> "Never say 'keypress', 'clipboard', or 'click' again."

**DEMOCRACY ONLINE**
**MOD API: DESIGNED**
**SELECTION PROTOCOL: READY TO SHIP**
