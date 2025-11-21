#!/usr/bin/env python3
"""
Main Flask application and server entry point.

Twitch Plays God overlay server for The Bibites.
Provides a web-based overlay showing vote counts for K (Kill) vs L (Lay).
Designed to be added as a Browser Source in OBS with "lighten" blend mode.
Full-page layout with black background (#000000) for clean compositing.

Includes left-side admin control panel for testing and game automation.
"""

from flask import Flask, render_template_string
from flask_socketio import SocketIO
from datetime import datetime

from .overlay import OVERLAY_TEMPLATE
from .websocket import setup_socketio_handlers
from .vote_manager import VoteManager

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


# Initialize vote manager (owns vote state)
vote_manager = VoteManager(socketio, log_action)

# Setup WebSocket handlers (legacy vote_state for backward compat with admin panel)
vote_state = {}  # Deprecated - vote_manager owns state now
broadcast_states = setup_socketio_handlers(socketio, vote_state, admin_state, log_action)


@app.route('/')
def overlay():
    """Serve the overlay HTML page."""
    return render_template_string(OVERLAY_TEMPLATE)


# Bot integration endpoints

@socketio.on('get_actions')
def handle_get_actions():
    """
    Return list of enabled action codes for bot.

    Bot calls this on startup to know which commands to accept.
    """
    actions = vote_manager.get_enabled_actions()
    print(f"Bot requested actions: {actions}")
    return actions


@socketio.on('vote_cast')
def handle_vote_cast(data):
    """
    Handle vote from Twitch bot.

    Args:
        data: {username: str, vote: str, timestamp: str}
    """
    username = data.get('username')
    vote = data.get('vote')
    timestamp_str = data.get('timestamp')

    # Parse timestamp if provided
    timestamp = None
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except:
            timestamp = datetime.now()

    # Record vote
    success = vote_manager.cast_vote(username, vote, timestamp)

    if success:
        print(f"Vote recorded: {username} → {vote.upper()}")
    else:
        print(f"Invalid vote ignored: {username} → {vote}")

    return {'success': success}


if __name__ == '__main__':
    print("=" * 60)
    print("Selection Protocol - Overlay Server")
    print("=" * 60)
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
