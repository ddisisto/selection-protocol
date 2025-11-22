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
- TwitchIO EventSub bot (receives chat messages)
- Action registry (extensible k/l/x system)
- Vote manager (tracks votes, first-L claimant logic)
- SocketIO integration (bot ↔ Flask communication)
- End-to-end vote flow (chat → bot → Flask → vote manager)

**🚧 In Progress:**
- Vote display in overlay (vote_manager ready, HTML needs update)

**❌ Phase 2 (Not Started):**
- Automated vote execution (Phase 2)
- Lineage tagging system (Phase 3)
- Community features (Phase 4)

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

- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** - Full technical specification
- **[CONTEXT.md](CONTEXT.md)** - Development history and design decisions
- **[docs/](docs/)** - Additional documentation

## The Mechanics

### One person, one vote
Latest vote replaces previous. No weight manipulation.

### First L gets naming rights
Until they switch away. Creates strategic tension.

### Ties open 10s window
Single L vote steals lineage and breaks tie.

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
- **Action Registry** ([src/actions.py](src/actions.py)) - Extensible action definitions
- **Vote Manager** ([src/vote_manager.py](src/vote_manager.py)) - Vote tracking + first-L logic
- **EventSub Bot** ([src/twitch_bot.py](src/twitch_bot.py)) - Twitch chat integration
- **Flask Server** ([src/server.py](src/server.py)) - Overlay + admin panel + SocketIO
- **Game Controller** ([src/game_controller.py](src/game_controller.py)) - xdotool automation

## Credits

Concept and implementation: Daniel + Claude (Sonnet 4.5)
Game: [The Bibites](https://thebibites.com) by Leo Caussan

---

> DEMOCRACY ONLINE
> VOTE TRACKING: OPERATIONAL
> SELECTION PROTOCOL: INITIALIZED

🔥
