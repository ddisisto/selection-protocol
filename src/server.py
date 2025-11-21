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

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bibites-twitch-overlay-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Vote state (will be updated by Twitch bot in future)
vote_state = {
    'k_votes': 0,
    'l_votes': 0,
    'total_votes': 0,
    'time_remaining': 30,
    'voting_active': False,
    'timer_paused': False
}

# Admin state
admin_state = {
    'auto_increment': False,
    'auto_resolve': False,
    'twitch_bot_active': False,
    'timer_duration': 30,
    'camera_mode': 'unknown',
    'last_action': None,
    'last_action_time': None,
    'connected_clients': 0,
    'action_log': []
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


# Setup WebSocket handlers
broadcast_states = setup_socketio_handlers(socketio, vote_state, admin_state, log_action)


@app.route('/')
def overlay():
    """Serve the overlay HTML page."""
    return render_template_string(OVERLAY_TEMPLATE)


def update_votes(k_votes, l_votes, time_remaining=30, voting_active=True):
    """Update vote counts and broadcast to all connected clients."""
    vote_state['k_votes'] = k_votes
    vote_state['l_votes'] = l_votes
    vote_state['total_votes'] = k_votes + l_votes
    vote_state['time_remaining'] = time_remaining
    vote_state['voting_active'] = voting_active
    socketio.emit('vote_update', vote_state)
    print(f"Votes updated: K={k_votes}, L={l_votes}, Time={time_remaining}s")


if __name__ == '__main__':
    print("=" * 60)
    print("Twitch Plays God Overlay Server")
    print("=" * 60)
    print("\nOverlay URL: http://localhost:5000")
    print("\nAdd this URL as a Browser Source in OBS:")
    print("  1. Add new Browser Source")
    print("  2. URL: http://localhost:5000")
    print("  3. Width: 1920, Height: 1080 (or your canvas size)")
    print("  4. Blend Mode: Lighten (in OBS transform settings)")
    print("  5. Crop/resize as needed in OBS")
    print("\nServer starting...")
    print("=" * 60)

    # Start with demo data
    vote_state['k_votes'] = 12
    vote_state['l_votes'] = 8
    vote_state['total_votes'] = 20
    vote_state['time_remaining'] = 25
    vote_state['voting_active'] = True

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
