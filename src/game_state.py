"""
Game state tracker for Selection Protocol.

Tracks stateful game commands with global cooldowns, reject counts, and metadata.
Provides structured accept/reject responses for overlay feedback.
"""

from datetime import datetime


class CommandGroup:
    """
    Tracks a group of related commands with shared global cooldown.

    Example: Info panels (1/2/3/4) share 15s cooldown - only one can change every 15s.
    First-in-wins after cooldown expires.
    Rejects selecting the current panel (prevents unwanted toggle).
    """

    def __init__(self, name, cooldown_seconds, reject_current=False):
        """
        Initialize command group.

        Args:
            name: Display name for this group
            cooldown_seconds: Seconds before next command in group can execute
            reject_current: If True, reject commands that select current value
        """
        self.name = name
        self.cooldown = cooldown_seconds
        self.reject_current = reject_current

        # Current state
        self.current = None           # Current value (e.g., '2' for info panel 2)
        self.previous = None          # Previous value

        # Execution metadata
        self.last_change = None       # datetime of last successful change
        self.last_user = None         # Username who triggered last change
        self.last_cause = None        # 'admin' or 'chat'

        # Rejection tracking
        self.rejected_count = 0       # Count since last successful change
        self.last_rejected_user = None

    def can_execute(self):
        """
        Check if group is off cooldown.

        Returns:
            bool: True if command can execute
        """
        if not self.last_change:
            return True

        elapsed = (datetime.now() - self.last_change).total_seconds()
        return elapsed >= self.cooldown

    def time_remaining(self):
        """
        Get seconds remaining on cooldown.

        Returns:
            float: Seconds until next command can execute (0 if ready)
        """
        if not self.last_change:
            return 0.0

        elapsed = (datetime.now() - self.last_change).total_seconds()
        remaining = self.cooldown - elapsed
        return max(0.0, remaining)

    def execute(self, value, user, cause='chat'):
        """
        Execute a command in this group.

        Args:
            value: New value (e.g., '2' for info panel 2)
            user: Username triggering the change
            cause: 'admin' or 'chat'

        Returns:
            dict: {
                'accepted': bool,
                'reason': str,
                'keypress': str or None,
                'cooldown_remaining': float
            }
        """
        # Check if selecting current value (unwanted toggle)
        if self.reject_current and self.current == value:
            self.rejected_count += 1
            self.last_rejected_user = user
            return {
                'accepted': False,
                'reason': 'already_selected',
                'keypress': None,
                'cooldown_remaining': 0.0
            }

        # Check cooldown
        if not self.can_execute():
            self.rejected_count += 1
            self.last_rejected_user = user
            return {
                'accepted': False,
                'reason': 'cooldown',
                'keypress': None,
                'cooldown_remaining': self.time_remaining()
            }

        # Accept the command
        self.previous = self.current
        self.current = value
        self.last_change = datetime.now()
        self.last_user = user
        self.last_cause = cause
        self.rejected_count = 0  # Reset on successful execution

        return {
            'accepted': True,
            'reason': 'executed',
            'keypress': value,
            'cooldown_remaining': 0.0
        }

    def get_state(self):
        """
        Get current state of this command group.

        Returns:
            dict: State metadata for admin panel + overlay
        """
        return {
            'name': self.name,
            'current': self.current,
            'previous': self.previous,
            'last_user': self.last_user,
            'last_cause': self.last_cause,
            'last_change': self.last_change.isoformat() if self.last_change else None,
            'rejected_count': self.rejected_count,
            'last_rejected_user': self.last_rejected_user,
            'cooldown': self.cooldown,
            'cooldown_remaining': self.time_remaining()
        }


class ZoomTracker:
    """
    Tracks zoom level with distance-based dynamic cooldown.

    Self-regulating system: The further from center, the longer the cooldown.
    Creates natural equilibrium at edge of chaos.

    Distance range: -50 (zoomed out) to +50 (zoomed in)
    Cooldown range: 1s (at center) to 120s (at limits)
    Formula: cooldown = 1 + (|distance| / 50) * 119
    """

    def __init__(self, name):
        """
        Initialize zoom tracker.

        Args:
            name: Display name for this tracker
        """
        self.name = name

        # Distance tracking
        self.distance_from_initial = 0  # -50 to +50
        self.min_distance = -50
        self.max_distance = 50

        # Cooldown scaling
        self.min_cooldown = 1.0   # At center (distance=0)
        self.max_cooldown = 120.0  # At limits (distance=±50)

        # Current state
        self.previous_distance = None

        # Execution metadata
        self.last_change = None
        self.last_user = None
        self.last_cause = None

        # Rejection tracking
        self.rejected_count = 0
        self.last_rejected_user = None

    def get_dynamic_cooldown(self):
        """
        Calculate cooldown based on current distance from initial.

        Returns:
            float: Cooldown in seconds (1-120s)
        """
        abs_distance = abs(self.distance_from_initial)
        normalized = abs_distance / 50.0  # 0.0 to 1.0
        cooldown_range = self.max_cooldown - self.min_cooldown
        return self.min_cooldown + (normalized * cooldown_range)

    def can_execute(self, direction):
        """
        Check if zoom command can execute.

        Args:
            direction: '+' (zoom in) or '-' (zoom out)

        Returns:
            tuple: (can_execute: bool, reason: str or None)
        """
        # Check distance limits
        if direction == '+' and self.distance_from_initial >= self.max_distance:
            return False, 'limit_reached'
        if direction == '-' and self.distance_from_initial <= self.min_distance:
            return False, 'limit_reached'

        # Check cooldown
        if self.last_change:
            elapsed = (datetime.now() - self.last_change).total_seconds()
            cooldown = self.get_dynamic_cooldown()
            if elapsed < cooldown:
                return False, 'cooldown'

        return True, None

    def time_remaining(self):
        """
        Get seconds remaining on cooldown.

        Returns:
            float: Seconds until next zoom can execute (0 if ready)
        """
        if not self.last_change:
            return 0.0

        elapsed = (datetime.now() - self.last_change).total_seconds()
        cooldown = self.get_dynamic_cooldown()
        remaining = cooldown - elapsed
        return max(0.0, remaining)

    def execute(self, direction, user, cause='chat'):
        """
        Execute a zoom command.

        Args:
            direction: '+' (zoom in) or '-' (zoom out)
            user: Username triggering the change
            cause: 'admin' or 'chat'

        Returns:
            dict: {
                'accepted': bool,
                'reason': str,
                'keypress': str or None,
                'cooldown_remaining': float,
                'distance': int
            }
        """
        can, reason = self.can_execute(direction)

        if not can:
            self.rejected_count += 1
            self.last_rejected_user = user
            return {
                'accepted': False,
                'reason': reason,
                'keypress': None,
                'cooldown_remaining': self.time_remaining() if reason == 'cooldown' else 0.0,
                'distance': self.distance_from_initial
            }

        # Update distance
        self.previous_distance = self.distance_from_initial
        if direction == '+':
            self.distance_from_initial += 1
            keypress = 'KP_Add'
        else:  # direction == '-'
            self.distance_from_initial -= 1
            keypress = 'KP_Subtract'

        # Record execution
        self.last_change = datetime.now()
        self.last_user = user
        self.last_cause = cause
        self.rejected_count = 0

        return {
            'accepted': True,
            'reason': 'executed',
            'keypress': keypress,
            'cooldown_remaining': 0.0,
            'distance': self.distance_from_initial
        }

    def get_state(self):
        """
        Get current state of zoom tracker.

        Returns:
            dict: State metadata for admin panel + overlay
        """
        return {
            'name': self.name,
            'distance': self.distance_from_initial,
            'previous_distance': self.previous_distance,
            'min_distance': self.min_distance,
            'max_distance': self.max_distance,
            'last_user': self.last_user,
            'last_cause': self.last_cause,
            'last_change': self.last_change.isoformat() if self.last_change else None,
            'rejected_count': self.rejected_count,
            'last_rejected_user': self.last_rejected_user,
            'dynamic_cooldown': self.get_dynamic_cooldown(),
            'cooldown_remaining': self.time_remaining()
        }


class StatefulToggle:
    """
    Tracks boolean state with explicit commands (not toggle).

    Example: UI visibility uses 'h' (hide) and 's' (show) - not a toggle.
    Rejects commands that would put it in the same state it's already in.
    """

    def __init__(self, name, cooldown_seconds, initial_state=False):
        """
        Initialize stateful toggle.

        Args:
            name: Display name for this toggle
            cooldown_seconds: Seconds before next state change
            initial_state: Initial boolean value (False = visible, True = hidden)
        """
        self.name = name
        self.cooldown = cooldown_seconds

        # Current state
        self.hidden = initial_state   # True = hidden, False = visible
        self.previous = None          # Previous boolean state

        # Execution metadata
        self.last_change = None
        self.last_user = None
        self.last_cause = None

        # Rejection tracking
        self.rejected_count = 0
        self.last_rejected_user = None

    def can_execute(self, target_hidden):
        """
        Check if state change is allowed.

        Args:
            target_hidden: Target boolean state (True = hide, False = show)

        Returns:
            tuple: (can_execute: bool, reason: str or None)
        """
        # Already in target state?
        if self.hidden == target_hidden:
            return False, 'already_in_state'

        # On cooldown?
        if self.last_change:
            elapsed = (datetime.now() - self.last_change).total_seconds()
            if elapsed < self.cooldown:
                return False, 'cooldown'

        return True, None

    def time_remaining(self):
        """
        Get seconds remaining on cooldown.

        Returns:
            float: Seconds until next state change (0 if ready)
        """
        if not self.last_change:
            return 0.0

        elapsed = (datetime.now() - self.last_change).total_seconds()
        remaining = self.cooldown - elapsed
        return max(0.0, remaining)

    def execute(self, target_hidden, user, cause='chat'):
        """
        Execute a state change.

        Args:
            target_hidden: Target boolean state (True = hide, False = show)
            user: Username triggering the change
            cause: 'admin' or 'chat'

        Returns:
            dict: {
                'accepted': bool,
                'reason': str,
                'keypress': str or None,
                'cooldown_remaining': float
            }
        """
        can, reason = self.can_execute(target_hidden)

        if not can:
            self.rejected_count += 1
            self.last_rejected_user = user
            return {
                'accepted': False,
                'reason': reason,
                'keypress': None,
                'cooldown_remaining': self.time_remaining()
            }

        # Accept the state change
        self.previous = self.hidden
        self.hidden = target_hidden
        self.last_change = datetime.now()
        self.last_user = user
        self.last_cause = cause
        self.rejected_count = 0

        return {
            'accepted': True,
            'reason': 'executed',
            'keypress': 'h',  # Game only has toggle - we send 'h' to toggle
            'cooldown_remaining': 0.0
        }

    def get_state(self):
        """
        Get current state of this toggle.

        Returns:
            dict: State metadata for admin panel + overlay
        """
        return {
            'name': self.name,
            'current': 'hidden' if self.hidden else 'visible',
            'current_bool': self.hidden,
            'previous': 'hidden' if self.previous else 'visible' if self.previous is not None else None,
            'last_user': self.last_user,
            'last_cause': self.last_cause,
            'last_change': self.last_change.isoformat() if self.last_change else None,
            'rejected_count': self.rejected_count,
            'last_rejected_user': self.last_rejected_user,
            'cooldown': self.cooldown,
            'cooldown_remaining': self.time_remaining()
        }


class GameState:
    """
    Central tracker for all stateful game commands.

    Handles:
    - Info panels (1/2/3/4) - 15s shared cooldown, rejects selecting current panel
    - Zoom (+/-) - Dynamic cooldown (1-120s) based on distance from initial
    - UI visibility (h/s) - 2s cooldown, explicit hide/show

    Self-regulating zoom system creates natural equilibrium at edge of chaos.
    """

    def __init__(self, socketio=None):
        """
        Initialize game state tracker.

        Args:
            socketio: Flask-SocketIO instance for broadcasting state updates
        """
        self.socketio = socketio

        # Command groups
        self.info_panels = CommandGroup('info_panels', cooldown_seconds=15.0, reject_current=True)

        # Zoom with distance-based dynamic cooldown
        self.zoom = ZoomTracker('zoom')

        # Stateful toggles
        self.ui = StatefulToggle('ui_visibility', cooldown_seconds=2.0, initial_state=False)

    def handle_command(self, command, user, cause='chat'):
        """
        Handle a game command with state tracking and cooldown enforcement.

        Args:
            command: Command character ('+', '-', '1', '2', '3', '4', 'h', 's')
            user: Username executing the command
            cause: 'admin' or 'chat'

        Returns:
            dict: {
                'accepted': bool,
                'reason': str,
                'keypress': str or None,
                'cooldown_remaining': float
            }
        """
        # Info panel commands
        if command in ['1', '2', '3', '4']:
            result = self.info_panels.execute(command, user, cause)

        # Zoom commands (direction-based with distance tracking)
        elif command in ['+', '-']:
            result = self.zoom.execute(command, user, cause)

        # UI visibility commands (explicit hide/show)
        elif command == 'h':  # Hide UI
            result = self.ui.execute(target_hidden=True, user=user, cause=cause)
        elif command == 's':  # Show UI
            result = self.ui.execute(target_hidden=False, user=user, cause=cause)

        else:
            return {
                'accepted': False,
                'reason': 'invalid_command',
                'keypress': None,
                'cooldown_remaining': 0.0
            }

        # Broadcast state update if we have socketio
        if self.socketio:
            self._broadcast_state()

        return result

    def get_state(self):
        """
        Get complete game state for admin panel + overlay.

        Returns:
            dict: Full state metadata
        """
        return {
            'info_panels': self.info_panels.get_state(),
            'zoom': self.zoom.get_state(),
            'ui': self.ui.get_state(),
            'timestamp': datetime.now().isoformat()
        }

    def _broadcast_state(self):
        """Broadcast game state update to all connected clients."""
        if self.socketio:
            self.socketio.emit('game_state_update', self.get_state())
