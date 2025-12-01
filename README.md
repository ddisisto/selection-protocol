# Selection Protocol

**Democratic Evolution Experiment**

> Where democracy meets evolution through artificial life.

---

## What Is This?

Twitch chat controls evolution.

The stream runs [The Bibites](https://thebibites.com) - an artificial life simulation where organisms evolve, compete, and reproduce. Chat votes to kill or force reproduction on whatever organism is currently on screen.

But here's the hook: **whoever votes to reproduce first gets to name the lineage**. Their username tags the parent and inherits to all descendants through the game's genetics system.

It's democracy meets dynasty building. Your lineage versus theirs. Compete for naming rights, watch your bloodline spread, see your dynasty dominate the world - or get voted extinct.

Evolution by collective will.

---

## How Does It Work?

The game runs locally with a custom BepInEx mod that exposes direct control over The Bibites. The gameplay is streamed to Twitch with an overlay showing current votes.

Viewers type commands in chat to vote. A Twitch bot receives messages via EventSub and sends votes to a Flask server. The server tracks votes, determines winners, and calls the mod's HTTP API to execute actions in the game.

The first person to vote for reproduction claims naming rights. When reproduction wins, the mod tags the organism with that viewer's username before forcing it to lay an egg. The tag inherits to all offspring through the game's genetics system.

Dynasties emerge. Lineages spread or get voted extinct. Democracy shapes evolution in real time.

---

## Architecture

```
Twitch Chat → EventSub Bot → SocketIO → Flask Server → Vote Manager
                                              ↓
                                        Mod Client (HTTP)
                                              ↓
                                   BepInEx Mod (localhost:5001)
                                              ↓
                                      The Bibites (Unity)
```

### Components

**BepInEx Mod** ([mod/](mod/))
- C# plugin for The Bibites (Unity game)
- HTTP API on localhost:5001
- Direct game state access (kill, lay, tag, pause, zoom, panels)
- Eliminates UI automation, clipboard tricks, timing hacks

**Flask Server** ([src/server.py](src/server.py))
- Overlay + admin panel on http://localhost:5000
- Vote tracking, timer logic, action execution
- SocketIO broadcasts to overlay (real-time updates)
- Calls mod API for game actions

**Twitch Bot** ([src/twitch_bot.py](src/twitch_bot.py))
- EventSub integration (receives chat messages)
- OAuth flow for user access tokens
- Parses K/L/X votes, sends to Flask via SocketIO
- Chat announcements (round start/end, outcomes)

**Key Modules:**
- [src/vote_manager.py](src/vote_manager.py) - Vote tracking, timer, execution, lineage tagging
- [src/mod_client.py](src/mod_client.py) - HTTP client for mod API
- [src/game_state.py](src/game_state.py) - Command cooldowns, state tracking
- [src/actions.py](src/actions.py) - Action registry (DRY)
- [src/websocket.py](src/websocket.py) - SocketIO event handlers

### Data Flow

1. Chat votes K/L/X
2. Bot → SocketIO → Flask → Vote Manager tracks votes
3. Timer expires → Vote Manager determines winner
4. Winner executes:
   - K → `mod.kill_target()` → Mod API → Game kills organism
   - L → `mod.lay_target(tag=username)` → Mod API → Game tags + lays egg
   - X → No action
5. Round end broadcast → Overlay updates

---

## Quick Start

### Prerequisites

- [The Bibites](https://thebibites.com) (Steam or itch.io)
- BepInEx installed in game directory
- Python 3.10+

### 1. Build and Install Mod

```bash
# Clone repo
git clone <repo-url>
cd selection-protocol

# Install ILSpy (one-time, for exploring game code)
dotnet tool install -g ilspycmd

# Build mod
./build_mod.sh
# → Deploys to ~/.steam/steam/steamapps/common/The Bibites/BepInEx/plugins/

# Start game, verify mod loaded
# Check BepInEx log: cat ~/.steam/.../BepInEx/LogOutput.log
# Should see: [Info   :SelectionProtocol] Plugin loaded
# Should see: [Info   :SelectionProtocol] HTTP API started on http://localhost:5001

# Test mod API
curl http://localhost:5001/health
# → {"status":"ok"}
```

### 2. Run Overlay Server

```bash
# Setup Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run server (requires game + mod running)
python -m src.server
# → http://localhost:5000
# → Admin panel: http://localhost:5000/admin
# → Overlay (OBS source): http://localhost:5000/overlay
```

### 3. Run Twitch Bot (Optional)

```bash
# One-time: Configure Twitch OAuth
cp config.yaml.example config.yaml
# Edit config.yaml with your Twitch app credentials from:
# https://dev.twitch.tv/console/apps

# Run bot (connects to Flask, then Twitch EventSub)
python -m src.twitch_bot --test  # 30s test mode
python -m src.twitch_bot          # daemon mode (runs forever)

# Browser opens for authorization on first run
# Token cached to .twitch_token for future runs
```

**Troubleshooting:**
- **"Token user mismatch":** Log out of Twitch in browser, log in as bot account (not channel owner), delete `.twitch_token`, re-run bot
- **Mod API connection failed:** Ensure game is running with mod loaded (check BepInEx log)
- **Other issues:** Check `config.yaml` has correct `client_id`/`client_secret`

---

## Development

### Workflow

All work starts with an issue. All commits reference an issue.

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Issue creation principles (explanatory over prescriptive, scope boundaries)
- Commit format (minimal, traceable)
- Session flow (issue → implement → close)

See [CLAUDE.md](CLAUDE.md) for:
- Project methodology (fail-fast, DRY, clean code)
- Work patterns (TodoWrite, parallel tools, testing approach)
- Architecture patterns (action registry, design tokens, server-authoritative)

### Modding

See [docs/MODDING.md](docs/MODDING.md) for:
- Threading pattern (background → Unity main thread)
- Source parameter pattern (pause state management)
- Decompile/build workflow
- Game UI integration (use existing methods, don't reimplement)

### Testing

Manual testing during development (server hot-reloads, user tests while game runs). No premature abstraction - wait for patterns to emerge.

---

## Documentation

- [docs/VOTING_RULES.md](docs/VOTING_RULES.md) - Vote mechanics, tie-breaking, edge cases
- [docs/CHAT_UX.md](docs/CHAT_UX.md) - Chat announcements, formatting, timing
- [docs/MODDING.md](docs/MODDING.md) - BepInEx mod development patterns
- [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md) - Agent-driven workflow (optional pattern)
- [docs/archive/](docs/archive/) - Historical planning docs, handover notes

---

## Philosophy

**Process Over Outcomes**
Build systematic methodologies, not one-off analyses.

**Scientific Experiment**
Depersonalized presentation, terminal aesthetic, transparent mechanics.

**Let Them Find It**
Organic discovery, word of mouth. Build something worth discovering.

**Fail-Fast**
Strict validation, clear error messages. No fallbacks to hardcoded values. Better to crash with explanation than silently do wrong thing.

**Democracy at Any Scale**
1 viewer or 1000. System works regardless.

---

## Credits

**Concept and Implementation:** Daniel + Claude (Sonnet 4.5)

**Game:** [The Bibites](https://thebibites.com) by Leo Caussan

---

> DEMOCRACY ONLINE
> SELECTION PROTOCOL: OPERATIONAL
