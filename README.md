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

**✅ Complete:**
- Overlay server (Flask + SocketIO) with admin panel
- Keypress automation (xdotool → The Bibites)
- OAuth authorization code flow (user access tokens)
- Token caching and refresh logic

**🚧 In Progress:**
- TwitchIO EventSub bot rewrite (IRC → EventSub WebSocket)

**❌ Not Started:**
- Vote manager (count k/l/x, first-L tracking)
- Vote display in overlay
- Automated execution (Phase 2)

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

# 3. Run Twitch bot (EventSub - in development)
python -m src.twitch_bot --test  # 30s test mode
# Browser opens for authorization on first run
# Token cached to .twitch_token for future runs
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

## Credits

Concept and implementation: Daniel + Claude (Sonnet 4.5)  
Game: [The Bibites](https://thebibites.com) by Leore Avidar

---

> DEMOCRACY ONLINE  
> LINEAGE INHERITANCE: READY  
> SELECTION PROTOCOL: INITIALIZED

🔥
