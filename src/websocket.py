"""
WebSocket event handlers for Flask-SocketIO.

Handles all real-time communication between clients and server including:
- Client connection/disconnection
- Vote updates and timer controls
- Admin keypress commands (direct, no cooldowns)
"""

from flask_socketio import emit
from .game_controller import send_keypress


def setup_socketio_handlers(socketio, vote_state, admin_state, log_action, vote_manager=None):
    """
    Register all SocketIO event handlers.

    Args:
        socketio: Flask-SocketIO instance
        vote_state: Global vote state dictionary (deprecated)
        admin_state: Global admin state dictionary
        log_action: Logging function for admin actions
        vote_manager: VoteManager instance (new, replaces vote_state)
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

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        admin_state['connected_clients'] = max(0, admin_state['connected_clients'] - 1)
        print(f"Client disconnected from overlay (remaining: {admin_state['connected_clients']})")
        log_action("Client disconnected", f"Remaining: {admin_state['connected_clients']}")

    @socketio.on('admin_add_k')
    def handle_admin_add_k():
        """Handle admin K +1 button."""
        vote_state['k_votes'] += 1
        vote_state['total_votes'] = vote_state['k_votes'] + vote_state['l_votes']
        log_action("K +1", f"K={vote_state['k_votes']}, L={vote_state['l_votes']}")
        broadcast_states()

    @socketio.on('admin_sub_k')
    def handle_admin_sub_k():
        """Handle admin K -1 button."""
        if vote_state['k_votes'] > 0:
            vote_state['k_votes'] -= 1
            vote_state['total_votes'] = vote_state['k_votes'] + vote_state['l_votes']
            log_action("K -1", f"K={vote_state['k_votes']}, L={vote_state['l_votes']}")
            broadcast_states()

    @socketio.on('admin_add_l')
    def handle_admin_add_l():
        """Handle admin L +1 button."""
        vote_state['l_votes'] += 1
        vote_state['total_votes'] = vote_state['k_votes'] + vote_state['l_votes']
        log_action("L +1", f"K={vote_state['k_votes']}, L={vote_state['l_votes']}")
        broadcast_states()

    @socketio.on('admin_sub_l')
    def handle_admin_sub_l():
        """Handle admin L -1 button."""
        if vote_state['l_votes'] > 0:
            vote_state['l_votes'] -= 1
            vote_state['total_votes'] = vote_state['k_votes'] + vote_state['l_votes']
            log_action("L -1", f"K={vote_state['k_votes']}, L={vote_state['l_votes']}")
            broadcast_states()

    @socketio.on('admin_reset')
    def handle_admin_reset():
        """Handle admin reset button."""
        vote_state['k_votes'] = 0
        vote_state['l_votes'] = 0
        vote_state['total_votes'] = 0
        log_action("Reset votes", "K=0, L=0")
        broadcast_states()

    @socketio.on('admin_random_vote')
    def handle_admin_random_vote():
        """Handle admin random vote button."""
        import random
        if random.random() < 0.5:
            vote_state['k_votes'] += 1
            log_action("Random vote", "Added K")
        else:
            vote_state['l_votes'] += 1
            log_action("Random vote", "Added L")
        vote_state['total_votes'] = vote_state['k_votes'] + vote_state['l_votes']
        broadcast_states()

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

    @socketio.on('admin_pause_timer')
    def handle_admin_pause_timer():
        """Handle admin pause timer button."""
        vote_state['timer_paused'] = True
        log_action("Timer paused")
        broadcast_states()

    @socketio.on('admin_resume_timer')
    def handle_admin_resume_timer():
        """Handle admin resume timer button."""
        vote_state['timer_paused'] = False
        log_action("Timer resumed")
        broadcast_states()

    @socketio.on('admin_trigger_now')
    def handle_admin_trigger_now():
        """Handle admin trigger now button."""
        # Determine winner
        if vote_state['k_votes'] > vote_state['l_votes']:
            winner = 'K (Kill)'
            send_keypress('Delete', log_action)
        elif vote_state['l_votes'] > vote_state['k_votes']:
            winner = 'L (Lay)'
            send_keypress('Insert', log_action)
        else:
            winner = 'Tie - no action'

        log_action("Triggered manually", f"Winner: {winner}")
        # Reset votes after triggering
        vote_state['k_votes'] = 0
        vote_state['l_votes'] = 0
        vote_state['total_votes'] = 0
        vote_state['time_remaining'] = admin_state['timer_duration']
        broadcast_states()

    @socketio.on('admin_reset_timer')
    def handle_admin_reset_timer(data):
        """Handle admin reset timer button."""
        duration = data.get('duration', 30)
        admin_state['timer_duration'] = duration
        vote_state['time_remaining'] = duration
        log_action("Timer reset", f"{duration}s")
        broadcast_states()

    @socketio.on('admin_toggle_setting')
    def handle_admin_toggle_setting(data):
        """Handle admin automation setting toggles."""
        setting = data.get('setting')
        value = data.get('value', False)

        if setting in admin_state:
            admin_state[setting] = value
            log_action(f"Setting: {setting}", f"{'Enabled' if value else 'Disabled'}")
            broadcast_states()

    # ============================================================
    # NEW ADMIN TESTING HANDLERS (vote_manager-based)
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

    return broadcast_states
