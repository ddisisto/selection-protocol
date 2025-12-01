# Modding Approach - Planning Doc

**Status:** Active - Pause control implemented (#20), pattern established
**Related:** Issue #2 (Architecture Decision)

---

## Executive Summary

Switch from xdotool UI automation to BepInEx modding for The Bibites integration. Provides direct game state access, eliminates timing workarounds, and creates cleaner API contract between game and server.

**Trade-off:** Accept game version coupling in exchange for eliminating inference-based UI automation.

---

## Key Knowledge

### The Bibites Modding Ecosystem

**Official Support:**
- Game explicitly supports modding via BepInEx framework
- Wiki documentation: https://the-bibites.fandom.com/wiki/Modding_with_BepInEx_(Tutorial)
- Active Discord community with modding support channels
- Linux-compatible (Proton/Wine tested by community)

**Existing Mods:**
- Vanilla Expanded Modpack - Multiple simultaneous mods working
- Constance Mod - Gene manipulation (proves genetic data access)
- Neurons Plus, Senses Plus - Neural network access
- Community Mod Manager (TBMM) - Installation automation

**Frameworks:**
- **BepInEx** (Recommended) - Plugin system, multiple mods, Harmony patching
- **dnSpy replacement** (Alternative) - Single mod, direct DLL modification

### Technical Architecture

**HTTP API Pattern (proven by VRisingServerApiPlugin):**
```
BepInEx Plugin
  └─> HttpListener (localhost:XXXX)
       └─> Background thread (HTTP requests)
            └─> Command queue
                 └─> Unity main thread (Update loop)
```

**Critical Constraint:**
- HttpListener runs on background thread
- Unity API calls MUST be on main thread
- Pattern: Queue commands, dequeue in Update()

**Game Paths (Linux/Proton):**
```
Install:   ~/.steam/steam/steamapps/common/The Bibites/
Savefiles: ~/.steam/steam/steamapps/compatdata/2736860/pfx/drive_c/users/steamuser/
           AppData/LocalLow/The Bibites/The Bibites/Savefiles/
```

---

## What Modding Solves

### Eliminates Current Workarounds
- ✅ Clipboard "stuffing trick" (read paste verification)
- ✅ Retry loops for UI state detection
- ✅ Focus stealing side effects
- ✅ Timing-dependent operations (Proton delays)
- ✅ Inference-based state tracking

### Enables New Capabilities
- ✅ Ground truth game state (isPaused, speed, population)
- ✅ Synchronous action execution (no race conditions)
- ✅ Direct organism data access (genetics, energy, position)
- ✅ Game event stream (births, deaths) → overlay
- ✅ Validation before actions (can't lay if not adult)

### Resolves Blocked Issues
- #3 (Timing reliability) - Synchronous API calls
- #4 (Observable state) - Direct state exposure
- #5 (Input focus) - No UI interaction needed

---

## Testing Workflow Impact

**Current (xdotool):**
- Server changes → Flask hot-reload → instant test ✅
- Game as black box, no restarts needed ✅

**With modding:**
- **Server changes** (90% of work) → Flask hot-reload → instant test ✅
- **Mod changes** (10% of work) → Build script → Game restart → ~25s iteration

**Key Insight:** Once API stable, iteration speed same as current. Only differs during initial mod development.

**Automation Potential:**
```bash
# build_mod.sh
dotnet build -c Release
cp bin/Release/SelectionProtocol.dll ~/.steam/.../BepInEx/plugins/
pkill -f "The Bibites.exe"
# Server relaunches game, polls mod API until ready
```

---

## Code Organization

**Monorepo - 4-file architecture:**
```
selection-protocol/
├── src/              # Python server (existing)
├── mod/              # C# BepInEx plugin
│   ├── Plugin.cs           # BepInEx entry, command queue (81 lines)
│   ├── HttpApi.cs          # HTTP routing layer (107 lines)
│   ├── GameController.cs   # Unity game state bridge (79 lines)
│   ├── ApiHandlers.cs      # Endpoint implementations (112 lines)
│   ├── PluginInfo.cs       # Version constants (9 lines)
│   ├── SelectionProtocol.csproj
│   └── decompiled/         # Decompiled game code (gitignored)
├── build_mod.sh      # Compile + deploy automation
├── decompile_dll.sh  # Extract game code for exploration
└── docs/
    └── MODDING_PLAN.md (this file)
```

**Architecture Philosophy:**
- **Separation of concerns:** Each file <150 lines, single responsibility
- **Plugin.cs:** BepInEx lifecycle, command queue (background → main thread)
- **HttpApi.cs:** HTTP infrastructure only, routes to handlers
- **GameController.cs:** Unity game state access, queues commands
- **ApiHandlers.cs:** HTTP endpoint logic, uses ManualResetEvent for callbacks
- **Scalable:** Easy to add endpoints without bloating any single file

**Rationale:**
- Single clone for contributors
- Coordinated versioning (server ↔ mod API contract)
- Git history shows full context
- File size targets prevent complexity creep

---

## Development Workflow

### Decompiling Game Code

To explore game state structures or find new APIs:

```bash
# One-time setup: Install ILSpy CLI tool
dotnet tool install -g ilspycmd

# Decompile BibitesAssembly.dll to mod/decompiled/
./decompile_dll.sh
```

**Output location:** `mod/decompiled/` (gitignored, not committed)

**Key files decompiled:**
- `ManagementScripts/TimeController.cs` - Pause state, simulation speed
- `ManagementScripts/UserControl.cs` - Organism selection
- `SimulationScripts/BibiteScripts/BibiteGenes.cs` - Genetics, tagging
- `SimulationScripts/BibiteScripts/BibiteBody.cs` - Energy, health, state

**Search tips:**
```bash
# Find all references to "pause"
grep -r "pause" mod/decompiled/ -i

# Find class by name
find mod/decompiled/ -name "*Manager*.cs"

# Search for public static fields (likely singletons)
grep -r "public static.*Instance" mod/decompiled/
```

**Workflow:**
1. Run `./decompile_dll.sh` when exploring new game features
2. Search decompiled code for relevant structures
3. Document findings (class names, field access, methods)
4. Implement in mod using discovered APIs
5. Re-run decompile script after game updates

### Building and Deploying Mod

```bash
# Build + deploy to game directory
./build_mod.sh

# Manually test
# 1. Restart The Bibites
# 2. Check BepInEx log: cat ~/.steam/.../BepInEx/LogOutput.log
# 3. Test API: curl http://localhost:5001/health
```

---

## Implementation Learnings

### Threading Pattern (Proven Working)

**Problem:** HttpListener runs on background thread, Unity API requires main thread.

**Solution:** Command queue with ManualResetEvent for synchronous responses.

```csharp
// Plugin.cs - Main thread (Unity Update loop)
private Queue<Action> _commandQueue = new Queue<Action>();
private void Update() {
    lock (_queueLock) {
        while (_commandQueue.Count > 0) {
            _commandQueue.Dequeue().Invoke();  // Execute on main thread
        }
    }
}

// ApiHandlers.cs - Background thread (HTTP request)
var resetEvent = new ManualResetEvent(false);
bool result = false;

_gameController.GetPauseState(state => {
    result = state;
    resetEvent.Set();  // Signal completion
});

if (resetEvent.WaitOne(5000)) {  // Wait up to 5s
    return result;
}
```

**Key insights:**
- Background thread enqueues command → Main thread executes → Callback fires → HTTP responds
- ManualResetEvent blocks HTTP thread until main thread completes
- 5s timeout prevents stuck requests
- Exception handling in Update() prevents one bad command from breaking queue

### Game Control: Source Parameter Pattern

**Discovery:** `TimeController.TogglePauseGame(string source)` uses pause source stacking.

**How it works:**
```csharp
public void TogglePauseGame(string source = "base", bool isUnpause = false)
{
    PauseSource pauseSource = Pauses.FirstOrDefault(p => p.Source == source);
    if (pauseSource != null) {
        // Source exists → remove it (unpause this source's contribution)
        Pauses.Remove(pauseSource);
    } else if (!isUnpause) {
        // Source missing → add it (pause with this source)
        Pauses.Add(new PauseSource { Source = source });
    }
}
```

**Critical insight:** Multiple pause sources can stack! Game paused if ANY source in list.

**Example conflict scenario:**
1. User hits spacebar → adds "base" source
2. API calls with "selection-protocol" → adds second source
3. Spacebar again → removes "base", game still paused ("selection-protocol" remains)
4. API and spacebar now desynchronized, stuck pause state

**Solution:** Use `source = "base"` to match spacebar's default behavior exactly.

```csharp
// Match spacebar - both control same pause source
TimeController.Instance.TogglePauseGame("base");
```

**Extrapolation:** This "source" pattern likely extends to other game controls. When implementing new endpoints (speed, selection), check decompiled code for similar parameter patterns to avoid conflicts with built-in controls.

### File Size Discipline

**Target:** Each file <150 lines to prevent complexity creep.

**Current status (Issue #20 complete):**
- Plugin.cs: 81 lines ✅
- HttpApi.cs: 107 lines ✅
- GameController.cs: 79 lines ✅
- ApiHandlers.cs: 112 lines ✅

**Benefits proven:**
- Easy to navigate (entire file fits on screen)
- Clear responsibilities (no "god objects")
- Adding pause control didn't bloat any file beyond target
- Pattern scales: speed/selection/actions will follow same structure

---

## Risk Assessment

### Acceptable Risks
**Game updates break mod:**
- BepInEx Harmony provides version resilience
- Community pattern: mods updated within days
- Mitigation: Keep xdotool code archived as fallback

**Viewer trust concerns:**
- Open-source mod proves chat controls real
- Stream BepInEx console showing mod load
- More transparent than invisible xdotool

### Manageable Complexity
**Threading (background ↔ Unity main):**
- Well-documented pattern
- Example code available (VRisingServerApiPlugin)

**.NET version targeting:**
- Unity uses .NET Framework 4.7.2
- Documented in BepInEx guides

---

## References

### Setup & Tools
- **BepInEx docs:** https://docs.bepinex.dev/
- **The Bibites wiki:** https://the-bibites.fandom.com/wiki/Modding_with_BepInEx_(Tutorial)
- **AvaloniaILSpy** (decompiler): https://github.com/icsharpcode/AvaloniaILSpy
- **BepInEx templates:** `dotnet new install BepInEx.Templates::2.0.0-be.4`

### Example Code
- **Unity HttpListener:** https://gist.github.com/amimaro/10e879ccb54b2cacae4b81abea455b10
- **VRisingServerApiPlugin:** https://thunderstore.io/c/v-rising/p/jays/VRisingServerApiPlugin/
- **Existing Bibites mods:** https://github.com/YBKy/The-Bibites-Vanilla-Expanded-Modpack

### Community
- **The Bibites Discord:** https://thebibites.itch.io/the-bibites (invite link)
- Modding help-forum channel

---

## Decision Criteria (from Issue #2)

1. **Peak complexity?** ✅ Speed field workaround suggests more to come
2. **Simplification potential?** ✅ Eliminates 80% of workarounds
3. **Viewer trust?** ✅ Open-source mod more transparent than hidden automation
4. **Maintenance burden?** ✅ Lower long-term (no inference, no timing hacks)
5. **Generality?** ⚠️ Couples to The Bibites (acceptable trade-off)

---

## Implementation Status

**✅ Phase 0: Viability PoC (Issue #17)**
- Install BepInEx in game directory
- Create minimal "Hello World" plugin
- Implement single HTTP endpoint: `GET /health`
- Verify callable from Python server
- **Result:** ✅ SUCCESSFUL - BepInEx works on Linux/Proton

**✅ Phase 1: Pause Control (Issue #20)**
- Refactor to 4-file architecture
- Implement command queue pattern (background → Unity main thread)
- GET /game/pause - Read pause state
- POST /game/pause - Toggle pause
- **Result:** ✅ COMPLETE - Pattern proven, scales to future endpoints

**🎯 Next Endpoints:**
- Speed control (GET/POST /game/speed)
- Organism selection (GET/POST /game/selection)
- Action execution (K/L/X endpoints)

**Future Work:**
- Direct lineage tagging (replace xdotool clipboard hack)
- Game event stream (births, deaths) → overlay
- Observable game state (population, timer, etc.)
- Deprecate xdotool completely

---

> "Process over outcomes. Build systems, not one-offs."
> "Fail-fast: Prototype before committing."
