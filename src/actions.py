"""
Action registry for Selection Protocol.

Defines all available actions (vote commands) and their properties.
Single source of truth - bot fetches enabled actions from Flask at startup.
"""

# Action definitions
# Each action has:
# - name: Display name
# - description: What it does
# - keypress: Game keypress to trigger (None if vote-only)
# - cooldown_group: Cooldown group for keypress (None if no keypress)
# - enabled: Whether action is currently available
# - phase: Which phase this action becomes available

ACTIONS = {
    'k': {
        'name': 'Kill',
        'description': 'Execute current organism (Delete key)',
        'keypress': 'Delete',
        'cooldown_group': 'primary',
        'enabled': True,
        'phase': 1
    },
    'l': {
        'name': 'Lay',
        'description': 'Force reproduction (Insert key)',
        'keypress': 'Insert',
        'cooldown_group': 'primary',
        'enabled': True,
        'phase': 1
    },
    'x': {
        'name': 'Extend',
        'description': 'Keep watching current organism (no action)',
        'keypress': None,  # No keypress, just continue observing
        'cooldown_group': None,
        'enabled': True,
        'phase': 1
    },

    # Future actions (Phase 2+):
    # 'z': {
    #     'name': 'Zoom',
    #     'description': 'Adjust zoom level',
    #     'keypress': 'KP_Plus',  # Could cycle through zoom levels
    #     'cooldown_group': 'zoom',
    #     'enabled': False,
    #     'phase': 2
    # },
    # 'c': {
    #     'name': 'Camera',
    #     'description': 'Change camera mode (Generation/Oldest/Random)',
    #     'keypress': 'ctrl+g',  # Could cycle through modes
    #     'cooldown_group': 'camera',
    #     'enabled': False,
    #     'phase': 2
    # },
    # 's': {
    #     'name': 'Speed',
    #     'description': 'Adjust simulation speed',
    #     'keypress': None,  # Game doesn't have speed control yet
    #     'cooldown_group': None,
    #     'enabled': False,
    #     'phase': 3
    # }
}


def get_enabled_actions():
    """
    Get list of currently enabled action codes.

    Returns:
        list: Action codes (e.g., ['k', 'l', 'x'])
    """
    return [code for code, action in ACTIONS.items() if action['enabled']]


def is_valid_action(code):
    """
    Check if action code is valid and enabled.

    Args:
        code: Action code (e.g., 'k', 'l', 'x')

    Returns:
        bool: True if valid and enabled
    """
    return code in ACTIONS and ACTIONS[code]['enabled']


def get_action_info(code):
    """
    Get full action definition.

    Args:
        code: Action code (e.g., 'k')

    Returns:
        dict: Action definition or None if invalid
    """
    return ACTIONS.get(code)
