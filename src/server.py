#!/usr/bin/env python3
"""
Main Flask application and server entry point.

Twitch Plays God overlay server for The Bibites.
Provides a web-based overlay showing vote counts for K (Kill) vs L (Lay).
Designed to be added as a Browser Source in OBS with "lighten" blend mode.
Full-page layout with black background (#000000) for clean compositing.

Includes left-side admin control panel for testing and game automation.
"""

from flask import Flask, render_template
from flask_socketio import SocketIO
from datetime import datetime

from .websocket import setup_socketio_handlers
from .vote_manager import VoteManager
from .game_state import GameState
from .mod_client import get_mod_client, ModUnavailableError, ModError

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bibites-twitch-overlay-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Admin state
admin_state = {
    'auto_increment': False,
    'auto_resolve': False,
    'twitch_bot_active': False,
    'timer_duration': 60,  # Default 60s vote cycles
    'camera_mode': 'unknown',
    'last_action': None,
    'last_action_time': None,
    'connected_clients': 0,
    'action_log': [],
    'time_remaining': 60,
    'timer_paused': False
}


def log_action(action, details=""):
    """Log an admin action with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"{timestamp} - {action}"
    if details:
        log_entry += f": {details}"
    admin_state['action_log'].insert(0, log_entry)
    admin_state['action_log'] = admin_state['action_log'][:10]  # Keep last 10
    admin_state['last_action'] = action
    admin_state['last_action_time'] = timestamp
    print(log_entry)


# Initialize game state (owns command state, cooldowns, tracking)
game_state = GameState(socketio)

# Initialize vote manager (owns vote state)
vote_manager = VoteManager(socketio, log_action)

# Setup WebSocket handlers
broadcast_states = setup_socketio_handlers(socketio, admin_state, log_action, vote_manager, game_state)


# Background timer task
def timer_background_task():
    """
    Background task that ticks the vote timer every second.

    Runs continuously, calling vote_manager.tick() to decrement timer
    and check for expiry/execution.
    """
    import time
    while True:
        time.sleep(1)
        vote_manager.tick()


# Start background timer when socketio is ready
@socketio.on('connect')
def handle_first_connect():
    """Start background timer on first client connection."""
    if not hasattr(handle_first_connect, 'timer_started'):
        socketio.start_background_task(timer_background_task)
        handle_first_connect.timer_started = True
        print("Background timer task started")


@app.route('/')
def index():
    """Serve the overlay page."""
    return render_template('index.html')


@app.route('/overlay')
def overlay():
    """Serve the overlay (alias for root, OBS compatibility)."""
    return render_template('overlay_only.html')


# Bot integration endpoints

@socketio.on('bot_connected')
def handle_bot_connected(data):
    """
    Handle bot connection status.

    Args:
        data: {bot_id: str, bot_username: str, timestamp: str}
    """
    bot_username = data.get('bot_username')
    timestamp = data.get('timestamp')

    admin_state['twitch_bot_active'] = True
    log_action("Twitch bot connected", f"@{bot_username}")
    print(f"\n{'='*60}")
    print(f"✓ Twitch bot connected: @{bot_username}")
    print(f"  Ready to receive chat input from viewers")
    print(f"{'='*60}\n")


@socketio.on('chat_input')
def handle_chat_input(data):
    """
    Route single-char chat input to appropriate handler (unified interface).

    Args:
        data: {username: str, input: str, timestamp: str}

    Returns:
        {accepted: bool, type: str, reason: str, ...}
    """
    username = data.get('username')
    chat_input = data.get('input')
    timestamp_str = data.get('timestamp')

    # Parse timestamp if provided
    timestamp = None
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.now()

    # Route to vote manager (k/l/x)
    if chat_input in vote_manager.get_enabled_actions():
        success = vote_manager.cast_vote(username, chat_input, timestamp)
        return {
            'accepted': success,
            'type': 'vote',
            'input': chat_input
        }

    # Route to game state (+/-/0-4)
    if chat_input in ['+', '-', '0', '1', '2', '3', '4']:
        result = game_state.handle_command(chat_input, username, cause='chat')

        # Execute mod API action if command was accepted
        if result['accepted']:
            mod_action = result.get('mod_action')
            if mod_action:
                try:
                    mod = get_mod_client()
                    if mod_action == 'zoom_in':
                        mod.zoom('in')
                    elif mod_action == 'zoom_out':
                        mod.zoom('out')
                    elif mod_action.startswith('panel_'):
                        panel = int(mod_action.split('_')[1])
                        mod.set_info_panel(panel)
                except ModError as e:
                    log_action(f"Game command FAILED: {chat_input}", f"From {username} - {e}")

        return {
            'accepted': result['accepted'],
            'type': 'command',
            'reason': result.get('reason', 'executed' if result['accepted'] else 'rejected'),
            'cooldown_remaining': result.get('cooldown_remaining', 0)
        }

    # Invalid input
    return {
        'accepted': False,
        'type': 'invalid',
        'reason': 'unknown_input'
    }




if __name__ == '__main__':
    print("=" * 60)
    print("Selection Protocol - Overlay Server")
    print("=" * 60)

    # Verify mod API connection (fail fast if not available)
    try:
        print("\nVerifying mod API connection...")
        mod = get_mod_client()
        print("✓ Mod API connected")
    except ModUnavailableError as e:
        print(f"\n✗ ERROR: {e}")
        print("\nServer startup aborted. Please ensure:")
        print("  1. The Bibites is running")
        print("  2. BepInEx mod is loaded")
        print("  3. Mod API is listening on http://localhost:5001")
        print("\n")
        exit(1)

    print("\nOverlay URL: http://localhost:5000")
    print("\nAdd this URL as a Browser Source in OBS:")
    print("  1. Add new Browser Source")
    print("  2. URL: http://localhost:5000")
    print("  3. Width: 1920, Height: 1080 (or your canvas size)")
    print("  4. Blend Mode: Lighten (in OBS transform settings)")
    print("  5. Crop/resize as needed in OBS")
    print("\nVote Manager initialized")
    print(f"Enabled actions: {vote_manager.get_enabled_actions()}")
    print("\nWaiting for Twitch bot to connect...")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
