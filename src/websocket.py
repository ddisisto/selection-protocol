"""
WebSocket event handlers for Flask-SocketIO.

Handles all real-time communication between clients and server including:
- Client connection/disconnection
- Vote updates and timer controls
- Admin keypress commands
- Cooldown state synchronization
"""

from flask_socketio import emit
from .cooldowns import start_cooldown, check_cooldown, get_cooldown_state_dict
from .game_controller import send_keypress


def setup_socketio_handlers(socketio, vote_state, admin_state, log_action):
    """
    Register all SocketIO event handlers.

    Args:
        socketio: Flask-SocketIO instance
        vote_state: Global vote state dictionary
        admin_state: Global admin state dictionary
        log_action: Logging function for admin actions
    """

    def broadcast_states():
        """Broadcast both vote and admin states to all clients."""
        socketio.emit('vote_update', vote_state)
        socketio.emit('admin_state_update', {
            **admin_state,
            'k_votes': vote_state['k_votes'],
            'l_votes': vote_state['i_votes']
        })

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        admin_state['connected_clients'] += 1
        print(f"Client connected to overlay (total: {admin_state['connected_clients']})")
        log_action("Client connected", f"Total: {admin_state['connected_clients']}")

        # Send current states to newly connected client
        emit('vote_update', vote_state)
        emit('admin_state_update', {
            **admin_state,
            'k_votes': vote_state['k_votes'],
            'l_votes': vote_state['i_votes']
        })
        emit('cooldown_update', get_cooldown_state_dict())

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
        vote_state['total_votes'] = vote_state['k_votes'] + vote_state['i_votes']
        log_action("K +1", f"K={vote_state['k_votes']}, L={vote_state['i_votes']}")
        broadcast_states()

    @socketio.on('admin_sub_k')
    def handle_admin_sub_k():
        """Handle admin K -1 button."""
        if vote_state['k_votes'] > 0:
            vote_state['k_votes'] -= 1
            vote_state['total_votes'] = vote_state['k_votes'] + vote_state['i_votes']
            log_action("K -1", f"K={vote_state['k_votes']}, L={vote_state['i_votes']}")
            broadcast_states()

    @socketio.on('admin_add_l')
    def handle_admin_add_l():
        """Handle admin L +1 button."""
        vote_state['i_votes'] += 1
        vote_state['total_votes'] = vote_state['k_votes'] + vote_state['i_votes']
        log_action("L +1", f"K={vote_state['k_votes']}, L={vote_state['i_votes']}")
        broadcast_states()

    @socketio.on('admin_sub_l')
    def handle_admin_sub_l():
        """Handle admin L -1 button."""
        if vote_state['i_votes'] > 0:
            vote_state['i_votes'] -= 1
            vote_state['total_votes'] = vote_state['k_votes'] + vote_state['i_votes']
            log_action("L -1", f"K={vote_state['k_votes']}, L={vote_state['i_votes']}")
            broadcast_states()

    @socketio.on('admin_reset')
    def handle_admin_reset():
        """Handle admin reset button."""
        vote_state['k_votes'] = 0
        vote_state['i_votes'] = 0
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
            vote_state['i_votes'] += 1
            log_action("Random vote", "Added L")
        vote_state['total_votes'] = vote_state['k_votes'] + vote_state['i_votes']
        broadcast_states()

    @socketio.on('admin_send_keypress')
    def handle_admin_send_keypress(data):
        """Handle admin keypress to game with cooldown enforcement."""
        key = data.get('key', '')
        cooldown_group = data.get('cooldown_group', None)

        # Check cooldown if group is specified
        if cooldown_group:
            remaining = check_cooldown(cooldown_group)
            if remaining > 0:
                result = {
                    'success': False,
                    'error': f'Cooldown active: {int(remaining)}s remaining',
                    'key': key
                }
                emit('keypress_result', result)
                return

        # Send the keypress
        result = send_keypress(key, log_action)

        # Start cooldown if keypress succeeded
        if result['success'] and cooldown_group:
            start_cooldown(cooldown_group, log_action)

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

        # Broadcast updated states including cooldowns
        broadcast_states()
        socketio.emit('cooldown_update', get_cooldown_state_dict())

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
        if vote_state['k_votes'] > vote_state['i_votes']:
            winner = 'K (Kill)'
            send_keypress('Delete', log_action)
        elif vote_state['i_votes'] > vote_state['k_votes']:
            winner = 'L (Lay)'
            send_keypress('i', log_action)
        else:
            winner = 'Tie - no action'

        log_action("Triggered manually", f"Winner: {winner}")
        # Reset votes after triggering
        vote_state['k_votes'] = 0
        vote_state['i_votes'] = 0
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

    @socketio.on('get_cooldown_state')
    def handle_get_cooldown_state():
        """Handle request for current cooldown state."""
        emit('cooldown_update', get_cooldown_state_dict())

    return broadcast_states
