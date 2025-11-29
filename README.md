# Selection Protocol

**Democratic Evolution Experiment**

> Where democracy meets natural selection through artificial life.

## What Is This?

Selection Protocol is a Twitch streaming experiment where chat votes every ~60 seconds on the fate of individual organisms in [The Bibites](https://thebibites.com) artificial life simulation:

- **K** (Kill) - Execute current organism
- **L** (Lay) - Force reproduction
- **X** (Extend) - Keep watching

**The Hook:** Winning L voters claim lineage naming rights. Their username tags the parent, inheriting to all descendants through the game's built-in genetics system.

## Current Status

**✅ Phase 1 Complete:**
- Overlay server (Flask + SocketIO) with admin panel
- Keypress automation (xdotool → The Bibites)
- OAuth authorization code flow (user access tokens)
- Token caching and refresh logic
- TwitchIO EventSub bot (receives chat messages, parses commands)
- Vote system (k/l/x) with first-L claimant logic
- Dynamic timer (30-120s, entropy-based, elapsed-time tracking)
- Automated vote execution (timer expires → winner executes)
- Game commands (+/- zoom, 0-4 info panels)
- Self-regulating cooldown system (distance-based, prevents extremes)
- SocketIO integration (bot ↔ Flask ↔ vote_manager ↔ game_state)
- Window auto-discovery (fail-fast validation)
- Vote display in overlay (real-time counts, timer, first-L claimant)
- Chat announcements (round start/end, outcomes, colored by context)

**✅ Phase 2 Core:**
- **Lineage tagging system** - First L voter's username tags parent organism
  - Automated sequence: pause → click tag field → verify → paste → confirm
  - Clipboard verification (stuffing trick ensures field read, not clipboard)
  - Context managers for game state control (pause, panel override)
  - Exclusive IO pattern prevents concurrent access
  - Fail-open: tag errors logged but don't block L execution
- **Overlay redesign** - 3-column layout with game state widgets
  - Command log with aging animation and real-time vote tracking
  - Info panel 2x2 grid with active highlighting
  - Zoom widget showing distance + directional cooldowns
  - Full-width footer ticker for round lifecycle events

**🚧 Phase 2 Remaining:**
- [Overlay functionality improvements](https://github.com/ddisisto/selection-protocol/issues/6) - Edge cases, missing data displays
- [Game integration reliability](https://github.com/ddisisto/selection-protocol/issues/2) - Architecture decision (automation vs modding)
  - Blocked issues: [#3 Timing](https://github.com/ddisisto/selection-protocol/issues/3), [#4 Observable state](https://github.com/ddisisto/selection-protocol/issues/4), [#5 Input focus](https://github.com/ddisisto/selection-protocol/issues/5)

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd selection-protocol
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1. Run overlay server (admin panel + OBS source)
python -m src.server
# → http://localhost:5000

# 2. Configure Twitch OAuth (first time only)
cp config.yaml.example config.yaml
# Edit config.yaml with your Twitch app credentials from:
# https://dev.twitch.tv/console/apps

# 3. Run Twitch bot (connects to Flask, then Twitch EventSub)
python -m src.twitch_bot --test  # 30s test mode
python -m src.twitch_bot          # daemon mode (runs forever)
# Browser opens for authorization on first run
# Token cached to .twitch_token for future runs

# Bot startup sequence:
# 1. Connects to Flask (exits if Flask not running)
# 2. Fetches enabled actions (k/l/x)
# 3. Connects to Twitch EventSub
# 4. Announces to chat
# 5. Receives votes → sends to Flask → vote_manager tracks them
```

## Documentation

- **[docs/](docs/)** - Voting rules, chat UX specs, setup guides

## The Mechanics

### One person, one vote
Latest vote replaces previous. No weight manipulation.

### First L gets naming rights
Until they switch away. Creates strategic tension.

### Majority wins, ties default to X
K or L needs >33% AND majority. Ties result in no action.

### Democracy at any scale
Works with 1 viewer or 1000. Empty stream = autonomous evolution.

## Philosophy

**Process Over Outcomes** - Build systematic methodologies, not one-off analyses.

**Scientific Experiment** - Depersonalized presentation, terminal aesthetic, transparent mechanics.

**Let Them Find It** - Organic discovery, word of mouth, build something worth discovering.

## License

TBD

## Architecture

```
Twitch Chat → EventSub Bot → SocketIO → Flask Server → Vote Manager → Overlay
                                              ↓
                                         Admin Panel → xdotool → The Bibites
```

**Key Components:**
- **Action Registry** ([src/actions.py](src/actions.py)) - Vote command definitions (k/l/x)
- **Game Commands** ([src/game_commands.py](src/game_commands.py)) - Direct commands (+/-/0-4)
- **Vote Manager** ([src/vote_manager.py](src/vote_manager.py)) - Vote tracking, timer, execution, lineage tagging
- **Game State** ([src/game_state.py](src/game_state.py)) - Command cooldowns, context managers for forced state
- **EventSub Bot** ([src/twitch_bot.py](src/twitch_bot.py)) - Twitch chat integration
- **Flask Server** ([src/server.py](src/server.py)) - Overlay + admin panel + SocketIO
- **Game Controller** ([src/game_controller.py](src/game_controller.py)) - Exclusive IO, xdotool automation, lineage tagging

## Credits

Concept and implementation: Daniel + Claude (Sonnet 4.5)
Game: [The Bibites](https://thebibites.com) by Leo Caussan

---

> DEMOCRACY ONLINE
> LINEAGE TAGGING: OPERATIONAL
> SELECTION PROTOCOL: ACTIVE

🔥
