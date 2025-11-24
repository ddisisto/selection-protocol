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

    Distance range: -15 (zoomed out) to +15 (zoomed in)
    Cooldown: Separate per direction
        - Moving toward center: 1s (always)
        - Moving away from center: 1.0 * 1.464^|distance| (exponential)
    Formula reaches 120s at distance 14 (moving to 15).
    """

    def __init__(self, name):
        """
        Initialize zoom tracker.

        Args:
            name: Display name for this tracker
        """
        self.name = name

        # Distance tracking
        self.distance_from_initial = 0  # -15 to +15
        self.min_distance = -15
        self.max_distance = 15

        # Cooldown scaling
        self.base_cooldown = 1.0       # Moving toward center
        self.exponential_base = 1.464  # Multiplier for exponential growth
        self.max_cooldown = 120.0      # Reached at distance 14→15

        # Current state
        self.previous_distance = None

        # Execution metadata
        self.last_change = None
        self.last_user = None
        self.last_cause = None
        self.last_direction = None  # Track last direction for cooldown

        # Rejection tracking
        self.rejected_count = 0
        self.last_rejected_user = None

    def get_dynamic_cooldown(self, direction):
        """
        Calculate cooldown based on direction and current distance.

        Args:
            direction: '+' (zoom in) or '-' (zoom out)

        Returns:
            float: Cooldown in seconds (1-120s)
        """
        # Determine if moving toward or away from center
        if self.distance_from_initial == 0:
            # At center, all moves are away
            moving_away = True
        elif self.distance_from_initial > 0:
            # Zoomed in (positive distance)
            moving_away = (direction == '+')  # + moves further in
        else:
            # Zoomed out (negative distance)
            moving_away = (direction == '-')  # - moves further out

        # Moving toward center = base cooldown (1s)
        if not moving_away:
            return self.base_cooldown

        # Moving away = exponential scaling based on current distance
        abs_distance = abs(self.distance_from_initial)
        cooldown = self.base_cooldown * (self.exponential_base ** abs_distance)

        # Cap at max_cooldown for practical UX
        return min(cooldown, self.max_cooldown)

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

        # Check cooldown (based on requested direction)
        if self.last_change:
            elapsed = (datetime.now() - self.last_change).total_seconds()
            cooldown = self.get_dynamic_cooldown(direction)
            if elapsed < cooldown:
                return False, 'cooldown'

        return True, None

    def time_remaining(self, direction=None):
        """
        Get seconds remaining on cooldown.

        Args:
            direction: Direction to check cooldown for (uses last_direction if None)

        Returns:
            float: Seconds until next zoom can execute (0 if ready)
        """
        if not self.last_change or not self.last_direction:
            return 0.0

        # Use provided direction or fall back to last direction
        check_direction = direction or self.last_direction

        elapsed = (datetime.now() - self.last_change).total_seconds()
        cooldown = self.get_dynamic_cooldown(check_direction)
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
                'cooldown_remaining': self.time_remaining(direction) if reason == 'cooldown' else 0.0,
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
        self.last_direction = direction  # Track direction for next cooldown check
        self.rejected_count = 0

        # Log zoom change with cooldown info
        cooldown_in = self.get_dynamic_cooldown('+')
        cooldown_out = self.get_dynamic_cooldown('-')
        print(f"[ZOOM] Distance: {self.distance_from_initial:+3d} | "
              f"Next cooldowns: IN={cooldown_in:6.2f}s, OUT={cooldown_out:6.2f}s | "
              f"User: {user}")

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
            'last_direction': self.last_direction,
            'last_change': self.last_change.isoformat() if self.last_change else None,
            'rejected_count': self.rejected_count,
            'last_rejected_user': self.last_rejected_user,
            'cooldown_in': self.get_dynamic_cooldown('+'),  # Zoom in cooldown
            'cooldown_out': self.get_dynamic_cooldown('-'),  # Zoom out cooldown
            'cooldown_remaining': self.time_remaining()
        }


class InfoPanelGroup:
    """
    Tracks info panel selection with hide/show logic.

    Commands: 0 (hide all), 1-4 (show panel)
    State: current (0-4), last_non_zero (1-4)

    Logic:
    - 0: If not hidden, send 'h', set current=0
    - 1-4:
      - If hidden: send 'h', then send number only if ≠ last_non_zero
      - If visible: send number only if ≠ current
      - Update current and last_non_zero

    Cooldown: Shared across entire group (0-4)
    """

    def __init__(self, name, cooldown_seconds):
        """
        Initialize info panel group.

        Args:
            name: Display name for this group
            cooldown_seconds: Seconds before next command can execute
        """
        self.name = name
        self.cooldown = cooldown_seconds

        # State tracking
        self.current = None          # Current value (0-4), None = unknown/initial
        self.last_non_zero = None    # Last selected panel (1-4)
        self.previous = None         # Previous value

        # Execution metadata
        self.last_change = None
        self.last_user = None
        self.last_cause = None

        # Rejection tracking
        self.rejected_count = 0
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
        Execute an info panel command (0-4).

        Args:
            value: Target value ('0'-'4')
            user: Username triggering the change
            cause: 'admin' or 'chat'

        Returns:
            dict: {
                'accepted': bool,
                'reason': str,
                'keypress': str or list of str (for multi-step),
                'cooldown_remaining': float
            }
        """
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

        # Determine if currently hidden (current == 0 or current == '0')
        is_hidden = (self.current == '0' or self.current == 0)

        # Handle '0' command (hide UI)
        if value == '0':
            # Already hidden?
            if is_hidden:
                self.rejected_count += 1
                self.last_rejected_user = user
                return {
                    'accepted': False,
                    'reason': 'already_hidden',
                    'keypress': None,
                    'cooldown_remaining': 0.0
                }

            # Hide UI
            self.previous = self.current
            self.current = '0'
            self.last_change = datetime.now()
            self.last_user = user
            self.last_cause = cause
            self.rejected_count = 0

            return {
                'accepted': True,
                'reason': 'executed',
                'keypress': 'h',  # Send hide keypress
                'cooldown_remaining': 0.0
            }

        # Handle 1-4 commands (show panel)
        if value in ['1', '2', '3', '4']:
            keypresses = []

            # If hidden, need to show UI first
            if is_hidden:
                keypresses.append('h')  # Unhide

                # Then send number only if different from last_non_zero
                if value != self.last_non_zero:
                    keypresses.append(value)
            else:
                # Already visible, send number only if different from current
                if value == self.current:
                    self.rejected_count += 1
                    self.last_rejected_user = user
                    return {
                        'accepted': False,
                        'reason': 'already_selected',
                        'keypress': None,
                        'cooldown_remaining': 0.0
                    }

                keypresses.append(value)

            # Update state
            self.previous = self.current
            self.current = value
            self.last_non_zero = value
            self.last_change = datetime.now()
            self.last_user = user
            self.last_cause = cause
            self.rejected_count = 0

            # Return single keypress or list
            return {
                'accepted': True,
                'reason': 'executed',
                'keypress': keypresses[0] if len(keypresses) == 1 else keypresses,
                'cooldown_remaining': 0.0
            }

        # Invalid value
        return {
            'accepted': False,
            'reason': 'invalid_value',
            'keypress': None,
            'cooldown_remaining': 0.0
        }

    def get_state(self):
        """
        Get current state of info panel group.

        Returns:
            dict: State metadata for admin panel + overlay
        """
        return {
            'name': self.name,
            'current': self.current,
            'last_non_zero': self.last_non_zero,
            'previous': self.previous,
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
    - Info panels (0-4) - 10s shared cooldown, 0=hide, 1-4=show panel with smart state tracking
    - Zoom (+/-) - Range ±15, directional cooldown: toward center=1s, away=exponential (1.0*1.464^distance, 120s at edge)

    Self-regulating zoom system creates natural equilibrium at edge of chaos.
    """

    def __init__(self, socketio=None):
        """
        Initialize game state tracker.

        Args:
            socketio: Flask-SocketIO instance for broadcasting state updates
        """
        self.socketio = socketio

        # Info panels (0-4 with hide/show logic)
        self.info_panels = InfoPanelGroup('info_panels', cooldown_seconds=10.0)

        # Zoom with distance-based dynamic cooldown
        self.zoom = ZoomTracker('zoom')

    def handle_command(self, command, user, cause='chat'):
        """
        Handle a game command with state tracking and cooldown enforcement.

        Args:
            command: Command character ('+', '-', '0', '1', '2', '3', '4')
            user: Username executing the command
            cause: 'admin' or 'chat'

        Returns:
            dict: {
                'accepted': bool,
                'reason': str,
                'keypress': str or list of str (multi-step),
                'cooldown_remaining': float
            }
        """
        # Info panel commands (0-4)
        if command in ['0', '1', '2', '3', '4']:
            result = self.info_panels.execute(command, user, cause)

        # Zoom commands (direction-based with distance tracking)
        elif command in ['+', '-']:
            result = self.zoom.execute(command, user, cause)

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
            'timestamp': datetime.now().isoformat()
        }

    def _broadcast_state(self):
        """Broadcast game state update to all connected clients."""
        if self.socketio:
            self.socketio.emit('game_state_update', self.get_state())
