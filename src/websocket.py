"""
WebSocket event handlers for Flask-SocketIO.

Handles all real-time communication between clients and server including:
- Client connection/disconnection
- Vote updates and timer controls
- Admin keypress commands (direct, no cooldowns)
"""

from flask_socketio import emit
from .game_controller import send_keypress


def setup_socketio_handlers(socketio, admin_state, log_action, vote_manager=None, game_state=None):
    """
    Register all SocketIO event handlers.

    Args:
        socketio: Flask-SocketIO instance
        admin_state: Global admin state dictionary
        log_action: Logging function for admin actions
        vote_manager: VoteManager instance for vote tracking
        game_state: GameState instance for command tracking and cooldowns
    """

    def broadcast_states():
        """Broadcast admin state to all clients."""
        # Note: vote_manager handles vote_update broadcasts directly
        socketio.emit('admin_state_update', admin_state)

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        admin_state['connected_clients'] += 1
        print(f"Client connected to overlay (total: {admin_state['connected_clients']})")
        log_action("Client connected", f"Total: {admin_state['connected_clients']}")

        # Send current states to newly connected client
        emit('admin_state_update', admin_state)

        # Send current game state if available
        if game_state:
            emit('game_state_update', game_state.get_state())

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        admin_state['connected_clients'] = max(0, admin_state['connected_clients'] - 1)
        print(f"Client disconnected from overlay (remaining: {admin_state['connected_clients']})")
        log_action("Client disconnected", f"Remaining: {admin_state['connected_clients']}")


    @socketio.on('admin_send_keypress')
    def handle_admin_send_keypress(data):
        """Handle admin keypress to game (direct, no cooldowns)."""
        key = data.get('key', '')

        # Send the keypress directly
        result = send_keypress(key, log_action)

        # Update camera mode if it's a camera control
        if key in ['ctrl+g', 'ctrl+o', 'ctrl+r']:
            if key == 'ctrl+g':
                admin_state['camera_mode'] = 'Generation'
            elif key == 'ctrl+o':
                admin_state['camera_mode'] = 'Oldest'
            elif key == 'ctrl+r':
                admin_state['camera_mode'] = 'Random'

        # Send result back to client
        emit('keypress_result', result)

        # Broadcast updated states
        broadcast_states()

    # ============================================================
    # ADMIN TESTING HANDLERS (vote_manager-based)
    # ============================================================

    @socketio.on('admin_add_vote')
    def handle_admin_add_vote(data):
        """Handle admin test vote addition (+)."""
        if not vote_manager:
            return
        vote_type = data.get('vote_type', '').lower()
        if vote_type in ['k', 'l', 'x']:
            test_username = vote_manager.add_test_vote(vote_type)
            log_action(f"Test vote added: {vote_type.upper()}", test_username)

    @socketio.on('admin_remove_vote')
    def handle_admin_remove_vote(data):
        """Handle admin vote removal (-)."""
        if not vote_manager:
            return
        vote_type = data.get('vote_type', '').lower()
        if vote_type in ['k', 'l', 'x']:
            success = vote_manager.remove_last_vote(vote_type)
            if not success:
                log_action(f"Remove {vote_type.upper()} vote", "No votes to remove")

    @socketio.on('admin_force_execute')
    def handle_admin_force_execute(data):
        """Handle admin force execution (K/L/X caps buttons)."""
        if not vote_manager:
            return
        action = data.get('action', '').lower()
        if action in ['k', 'l', 'x']:
            vote_manager.force_execute_action(action)

    # ============================================================
    # GAME COMMAND HANDLERS (from Twitch chat)
    # ============================================================

    @socketio.on('game_command')
    def handle_game_command(data):
        """
        Handle game commands from Twitch chat (+/-/0/1/2/3/4).

        Uses game_state for cooldown enforcement and state tracking.
        Sends structured accept/reject responses for overlay feedback.

        Args:
            data: Dict with 'username', 'command', 'keypress', 'timestamp'
        """
        username = data.get('username', 'Unknown')
        command = data.get('command', '')

        # Use game_state if available for validation and tracking
        if game_state:
            # Validate and track command through game_state
            result = game_state.handle_command(command, username, cause='chat')

            if result['accepted']:
                # Execute the keypress(es) - may be single or multi-step
                keypresses = result['keypress']
                if not isinstance(keypresses, list):
                    keypresses = [keypresses]

                # Execute each keypress sequentially
                all_success = True
                for keypress in keypresses:
                    exec_result = send_keypress(keypress, log_action)
                    if not exec_result['success']:
                        all_success = False
                        log_action(f"Game command FAILED: {command}", f"From {username} - {exec_result.get('error', 'Unknown')}")
                        break

                if all_success:
                    keypress_str = ', '.join(keypresses) if len(keypresses) > 1 else keypresses[0]
                    log_action(f"Game command: {command}", f"From {username} (keypress: {keypress_str})")
            else:
                # Command rejected (cooldown or already in state)
                reason = result['reason']
                cooldown_remaining = result.get('cooldown_remaining', 0)

                if reason == 'cooldown':
                    log_action(f"Game command REJECTED: {command}", f"From {username} - on cooldown ({cooldown_remaining:.1f}s)")
                elif reason == 'already_in_state':
                    log_action(f"Game command REJECTED: {command}", f"From {username} - already in target state")
                elif reason == 'already_selected':
                    log_action(f"Game command REJECTED: {command}", f"From {username} - panel already selected")
                elif reason == 'already_hidden':
                    log_action(f"Game command REJECTED: {command}", f"From {username} - UI already hidden")
                elif reason == 'limit_reached':
                    log_action(f"Game command REJECTED: {command}", f"From {username} - zoom limit reached")
                else:
                    log_action(f"Game command REJECTED: {command}", f"From {username} - {reason}")

        else:
            # Fallback: No game_state, execute directly (backward compatibility)
            keypress = data.get('keypress', '')
            result = send_keypress(keypress, log_action)

            if result['success']:
                log_action(f"Game command: {command}", f"From {username} (keypress: {keypress})")
            else:
                log_action(f"Game command FAILED: {command}", f"From {username} - {result.get('error', 'Unknown error')}")

    @socketio.on('get_game_state')
    def handle_get_game_state():
        """Handle request for current game state (for admin panel queries)."""
        if game_state:
            return game_state.get_state()
        return {}

    return broadcast_states
