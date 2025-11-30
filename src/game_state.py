"""
Game state tracker for Selection Protocol.

Tracks stateful game commands with global cooldowns, reject counts, and metadata.
Provides structured accept/reject responses for overlay feedback.
Provides context managers for forced state control (lineage tagging, etc).
"""

from datetime import datetime
from contextlib import contextmanager
from . import game_controller


class CommandBase:
    """
    Base class for command trackers with shared metadata and rejection tracking.

    Subclasses implement:
    - can_execute() - Validation logic
    - time_remaining() - Cooldown calculation
    - execute() - Command execution (can use _record_execution() and _record_rejection())
    - get_state() - Extend _get_base_metadata() with command-specific state
    """

    def __init__(self, name):
        """
        Initialize base command tracker.

        Args:
            name: Display name for this command/group
        """
        self.name = name

        # Execution metadata (shared across all commands)
        self.last_change = None       # datetime of last successful change
        self.last_user = None         # Username who triggered last change
        self.last_cause = None        # 'admin' or 'chat'

        # Rejection tracking (shared across all commands)
        self.rejected_count = 0       # Count since last successful change
        self.last_rejected_user = None

    def _record_execution(self, user, cause='chat'):
        """
        Record successful execution metadata.

        Args:
            user: Username triggering the change
            cause: 'admin' or 'chat'
        """
        self.last_change = datetime.now()
        self.last_user = user
        self.last_cause = cause
        self.rejected_count = 0  # Reset on successful execution

    def _record_rejection(self, user):
        """
        Record rejection metadata.

        Args:
            user: Username whose command was rejected
        """
        self.rejected_count += 1
        self.last_rejected_user = user

    def _get_base_metadata(self):
        """
        Get base metadata dict for get_state().

        Returns:
            dict: Base metadata (name, timing, rejection counts)
        """
        return {
            'name': self.name,
            'last_user': self.last_user,
            'last_cause': self.last_cause,
            'last_change': self.last_change.isoformat() if self.last_change else None,
            'rejected_count': self.rejected_count,
            'last_rejected_user': self.last_rejected_user
        }

    def can_execute(self, *args, **kwargs):
        """Subclass must implement validation logic."""
        raise NotImplementedError

    def time_remaining(self, *args, **kwargs):
        """Subclass must implement cooldown calculation."""
        raise NotImplementedError

    def execute(self, *args, **kwargs):
        """Subclass must implement command execution."""
        raise NotImplementedError

    def get_state(self):
        """Subclass must implement state retrieval."""
        raise NotImplementedError


class ZoomTracker(CommandBase):
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
        super().__init__(name)

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
        self.last_direction = None  # Track last direction for cooldown

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
            self._record_rejection(user)
            return {
                'accepted': False,
                'reason': reason,
                'mod_action': None,
                'cooldown_remaining': self.time_remaining(direction) if reason == 'cooldown' else 0.0,
                'distance': self.distance_from_initial
            }

        # Update distance
        self.previous_distance = self.distance_from_initial
        if direction == '+':
            self.distance_from_initial += 1
            mod_action = 'zoom_in'
        else:  # direction == '-'
            self.distance_from_initial -= 1
            mod_action = 'zoom_out'

        # Record execution
        self._record_execution(user, cause)
        self.last_direction = direction  # Track direction for next cooldown check

        # Log zoom change with cooldown info
        cooldown_in = self.get_dynamic_cooldown('+')
        cooldown_out = self.get_dynamic_cooldown('-')
        print(f"[ZOOM] Distance: {self.distance_from_initial:+3d} | "
              f"Next cooldowns: IN={cooldown_in:6.2f}s, OUT={cooldown_out:6.2f}s | "
              f"User: {user}")

        return {
            'accepted': True,
            'reason': 'executed',
            'mod_action': mod_action,
            'cooldown_remaining': 0.0,
            'distance': self.distance_from_initial
        }

    def get_state(self):
        """
        Get current state of zoom tracker.

        Returns:
            dict: State metadata for admin panel + overlay
        """
        state = self._get_base_metadata()
        state.update({
            'distance': self.distance_from_initial,
            'previous_distance': self.previous_distance,
            'min_distance': self.min_distance,
            'max_distance': self.max_distance,
            'last_direction': self.last_direction,
            'cooldown_in': self.get_dynamic_cooldown('+'),  # Zoom in cooldown
            'cooldown_out': self.get_dynamic_cooldown('-'),  # Zoom out cooldown
            'cooldown_remaining': self.time_remaining()
        })
        return state


class InfoPanelGroup(CommandBase):
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
        super().__init__(name)
        self.cooldown = cooldown_seconds

        # State tracking
        self.current = None          # Current value (0-4), None = unknown/initial
        self.last_non_zero = None    # Last selected panel (1-4)
        self.previous = None         # Previous value

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
            cause: 'admin', 'chat', or 'system'

        Returns:
            dict: {
                'accepted': bool,
                'reason': str,
                'keypress': str or list of str (for multi-step),
                'cooldown_remaining': float
            }
        """
        # Check cooldown ONLY for non-system calls
        # System calls (lineage tagging, etc) bypass cooldown
        if cause != 'system':
            if not self.can_execute():
                self._record_rejection(user)
                return {
                    'accepted': False,
                    'reason': 'cooldown',
                    'mod_action': None,
                    'cooldown_remaining': self.time_remaining()
                }

        # Determine if currently hidden (current == 0 or current == '0')
        is_hidden = (self.current == '0' or self.current == 0)

        # Handle '0' command (hide UI)
        if value == '0':
            # Already hidden?
            if is_hidden:
                self._record_rejection(user)
                return {
                    'accepted': False,
                    'reason': 'already_hidden',
                    'mod_action': None,
                    'cooldown_remaining': 0.0
                }

            # Hide UI
            self.previous = self.current
            self.current = '0'
            self._record_execution(user, cause)

            return {
                'accepted': True,
                'reason': 'executed',
                'mod_action': 'panel_0',
                'cooldown_remaining': 0.0
            }

        # Handle 1-4 commands (show panel)
        if value in ['1', '2', '3', '4']:
            # Mod API handles panel switching directly - no multi-step needed
            # Already selected check
            if not is_hidden and value == self.current:
                self._record_rejection(user)
                return {
                    'accepted': False,
                    'reason': 'already_selected',
                    'mod_action': None,
                    'cooldown_remaining': 0.0
                }

            # Update state
            self.previous = self.current
            self.current = value
            self.last_non_zero = value
            self._record_execution(user, cause)

            return {
                'accepted': True,
                'reason': 'executed',
                'mod_action': f'panel_{value}',
                'cooldown_remaining': 0.0
            }

        # Invalid value
        return {
            'accepted': False,
            'reason': 'invalid_value',
            'mod_action': None,
            'cooldown_remaining': 0.0
        }

    def get_state(self):
        """
        Get current state of info panel group.

        Returns:
            dict: State metadata for admin panel + overlay
        """
        state = self._get_base_metadata()
        state.update({
            'current': self.current,
            'last_non_zero': self.last_non_zero,
            'previous': self.previous,
            'cooldown': self.cooldown,
            'cooldown_remaining': self.time_remaining()
        })
        return state

    @contextmanager
    def override(self, panel):
        """
        Context manager for forcing panel view with restoration.

        Determines keypresses needed but doesn't send them.
        Yields (setup_keys, restore_fn) where restore_fn() returns restoration keys.

        Args:
            panel: Target panel ('1', '2', '3', '4', or '0')

        Yields:
            tuple: (list of setup keypresses, callable returning restore keypresses)

        Example:
            with info_panels.override('1') as (setup_keys, get_restore_keys):
                # Send setup_keys via game_controller
                # Do work...
                # Send get_restore_keys() via game_controller
        """
        original = self.current

        # Get setup keypresses (bypass cooldown with cause='system')
        setup_keys = self._get_override_keys(panel)

        # Closure for restoration
        def get_restore_keys():
            if original and original != panel:
                return self._get_override_keys(original)
            return []

        yield (setup_keys, get_restore_keys)

    def _get_override_keys(self, panel):
        """
        Get keypresses for panel override (system-level, bypass cooldown).

        Args:
            panel: Target panel value

        Returns:
            list: Keypresses to send (empty if already at target)
        """
        if self.current == panel:
            return []  # Already at target

        # Use execute() with cause='system' to bypass cooldown
        result = self.execute(panel, user='SYSTEM', cause='system')
        kp = result.get('keypress')

        # Normalize to list
        if isinstance(kp, list):
            return kp
        elif kp:
            return [kp]
        return []


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
                'mod_action': None,
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

    # ============================================================
    # CONTEXT MANAGERS FOR FORCED STATE CONTROL
    # ============================================================

    @contextmanager
    def paused(self, log_func=None):
        """
        Pause game, yield, unpause on exit.

        Uses game_controller.io for keypresses.

        Args:
            log_func: Optional logging function

        Yields:
            None

        Example:
            with game_state.paused():
                # Game is paused
                # Do work...
                pass
            # Game unpaused automatically
        """
        with game_controller.io() as io:
            io.keypress('space', log_func)

        try:
            yield
        finally:
            with game_controller.io() as io:
                io.keypress('space', log_func)

    @contextmanager
    def panel_view(self, panel, log_func=None):
        """
        Force info panel view, restore on exit.

        Uses InfoPanelGroup.override() for logic, sends keys via game_controller.
        Bypasses cooldowns (system-level access).

        Args:
            panel: Target panel ('1', '2', '3', '4', or '0')
            log_func: Optional logging function

        Yields:
            None

        Example:
            with game_state.panel_view('1'):
                # Panel 1 is now active (forced)
                # Do work...
                pass
            # Original panel restored automatically
        """
        with self.info_panels.override(panel) as (setup_keys, get_restore_keys):
            # Send setup keypresses
            if setup_keys:
                with game_controller.io() as io:
                    for key in setup_keys:
                        io.keypress(key, log_func)

            try:
                yield
            finally:
                # Restore original state
                restore_keys = get_restore_keys()
                if restore_keys:
                    with game_controller.io() as io:
                        for key in restore_keys:
                            io.keypress(key, log_func)

    @contextmanager
    def tagging_context(self, log_func=None):
        """
        Combined context for lineage tagging.

        Pauses game and forces info panel '1' view.
        Restores all state on exit.

        Args:
            log_func: Optional logging function

        Yields:
            None

        Example:
            with game_state.tagging_context():
                with game_controller.io() as io:
                    io.click(225, 225)
                    # ... tagging sequence
        """
        with self.paused(log_func):
            with self.panel_view('1', log_func):
                yield
