# Modding Guide

**Purpose:** Essential patterns for BepInEx mod development.

---

## Why Modding?

Switched from xdotool UI automation to BepInEx modding for direct game state access. Eliminates timing workarounds, clipboard tricks, and focus stealing.

**Trade-off:** Accept game version coupling in exchange for eliminating inference-based UI automation.

**What it solves:**
- Direct organism data access (genetics, energy, position)
- Synchronous action execution (no race conditions)
- Ground truth game state (isPaused, speed, population)
- No UI interaction needed (focus, clicks, clipboard)

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
- `ManagementScripts/GUIManager.cs` - UI manager, action methods
- `UIScripts/BibiteStatsPanel.cs` - Stats panel methods (Kill, Lay, Tag)
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

# Search for public static singletons
grep -r "public static.*Instance" mod/decompiled/
```

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

## Core Patterns

### Threading Pattern (Background → Unity Main)

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
ActionResult result = null;

_gameController.KillTarget(r => {
    result = r;
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

### Source Parameter Pattern

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

**Solution:** Use `source = "base"` to match spacebar's default behavior exactly.

```csharp
// Match spacebar - both control same pause source
TimeController.Instance.TogglePauseGame("base");
```

**Extrapolation:** This "source" pattern likely extends to other game controls. When implementing new endpoints (speed, selection), check decompiled code for similar parameter patterns to avoid conflicts.

### Use Game UI Methods

**Pattern:** When game UI already has methods for actions, use them instead of reimplementing.

**Example (from #36):**
```csharp
// ✅ Use existing UI method - gets TagsManager integration, UI refresh
GUIManager.Instance.StatsPanel.KillCurrentBibite();

// ❌ Don't reimplement
body.Die();  // Missing ExplodeToMeat, egg handling, etc.
```

**Benefits:**
- Inherits game's full behavior (ExplodeToMeat on already-dead, etc.)
- Automatic UI updates
- TagsManager integration
- Less maintenance (game updates don't break us)

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
