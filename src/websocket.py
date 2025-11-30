"""
WebSocket event handlers for Flask-SocketIO.

Handles all real-time communication between clients and server including:
- Client connection/disconnection
- Vote updates (broadcast by vote_manager)
"""

from flask_socketio import emit


def setup_socketio_handlers(socketio, admin_state, log_action, vote_manager=None, game_state=None):
    """
    Register all SocketIO event handlers.

    Args:
        socketio: Flask-SocketIO instance
        admin_state: Global admin state dictionary
        log_action: Logging function for admin actions
        vote_manager: VoteManager instance for vote tracking (unused, kept for compatibility)
        game_state: GameState instance (unused, kept for compatibility)
    """

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        admin_state['connected_clients'] += 1
        print(f"Client connected to overlay (total: {admin_state['connected_clients']})")
        log_action("Client connected", f"Total: {admin_state['connected_clients']}")

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        admin_state['connected_clients'] = max(0, admin_state['connected_clients'] - 1)
        print(f"Client disconnected from overlay (remaining: {admin_state['connected_clients']})")
        log_action("Client disconnected", f"Remaining: {admin_state['connected_clients']}")
