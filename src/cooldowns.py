"""
Cooldown state management and functions.

Tracks active cooldowns for game actions and provides functions to check/start cooldowns.
Cooldowns prevent spam and ensure balanced gameplay.
"""

import time
from .config import COOLDOWN_DURATIONS

# Cooldown state - tracks active cooldowns and expiry times
cooldown_state = {
    'primary': {'active': False, 'expires_at': 0},  # Kill, Lay (15s shared)
    'camera': {'active': False, 'expires_at': 0},   # Ctrl+G/O/R (10s shared)
    'zoom_in': {'active': False, 'expires_at': 0},  # KP+ (5s individual)
    'zoom_out': {'active': False, 'expires_at': 0}, # KP- (5s individual)
    'extend': {'active': False, 'expires_at': 0}    # x (30s individual)
}


def start_cooldown(group, log_func=None):
    """
    Start a cooldown for the given group.

    Args:
        group: Cooldown group name ('primary', 'camera', 'zoom_in', 'zoom_out', 'extend')
        log_func: Optional logging function to call with action details
    """
    cooldown_state[group]['active'] = True
    cooldown_state[group]['expires_at'] = time.time() + COOLDOWN_DURATIONS[group]
    if log_func:
        log_func(f"Cooldown started", f"{group} ({COOLDOWN_DURATIONS[group]}s)")


def check_cooldown(group):
    """
    Check if a cooldown is active. Returns remaining time or 0 if ready.

    Args:
        group: Cooldown group name to check

    Returns:
        float: Remaining time in seconds, or 0 if cooldown is not active
    """
    if not cooldown_state[group]['active']:
        return 0

    remaining = cooldown_state[group]['expires_at'] - time.time()
    if remaining <= 0:
        # Cooldown expired, clear it
        cooldown_state[group]['active'] = False
        cooldown_state[group]['expires_at'] = 0
        return 0

    return remaining


def get_cooldown_state_dict():
    """
    Get current cooldown state with remaining times for all groups.

    Automatically expires any cooldowns that have passed and returns clean state.

    Returns:
        dict: Cooldown state for each group with 'active' and 'remaining' fields
    """
    current_time = time.time()
    state = {}
    for group in cooldown_state:
        if cooldown_state[group]['active']:
            remaining = max(0, cooldown_state[group]['expires_at'] - current_time)
            if remaining <= 0:
                cooldown_state[group]['active'] = False
                cooldown_state[group]['expires_at'] = 0
            state[group] = {
                'active': remaining > 0,
                'remaining': int(remaining) if remaining > 0 else 0
            }
        else:
            state[group] = {'active': False, 'remaining': 0}
    return state
