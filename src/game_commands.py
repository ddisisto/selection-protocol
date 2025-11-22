"""
Game command registry for Selection Protocol.

Defines direct game controls that viewers can trigger via chat.
These bypass the voting system and execute immediately.

NOTE: No rate limiting implemented yet - add per-user cooldowns before live deployment.
"""

# Game command definitions
# Each command has:
# - name: Display name
# - description: What it does
# - keypress: Actual keypress to send to game
# - category: Command category for organization
# - enabled: Whether command is currently available

GAME_COMMANDS = {
    # Zoom controls
    '+': {
        'name': 'Zoom In',
        'description': 'Increase zoom level',
        'keypress': 'KP_Add',
        'category': 'zoom',
        'enabled': True
    },
    '-': {
        'name': 'Zoom Out',
        'description': 'Decrease zoom level',
        'keypress': 'KP_Subtract',
        'category': 'zoom',
        'enabled': True
    },

    # Info panel selection
    '1': {
        'name': 'Info Panel 1',
        'description': 'Display info panel 1',
        'keypress': '1',
        'category': 'ui',
        'enabled': True
    },
    '2': {
        'name': 'Info Panel 2',
        'description': 'Display info panel 2',
        'keypress': '2',
        'category': 'ui',
        'enabled': True
    },
    '3': {
        'name': 'Info Panel 3',
        'description': 'Display info panel 3',
        'keypress': '3',
        'category': 'ui',
        'enabled': True
    },
    '4': {
        'name': 'Info Panel 4',
        'description': 'Display info panel 4',
        'keypress': '4',
        'category': 'ui',
        'enabled': True
    },

    # UI toggle
    'h': {
        'name': 'Hide UI',
        'description': 'Toggle UI visibility (clean view)',
        'keypress': 'h',
        'category': 'ui',
        'enabled': True
    }
}


def get_enabled_commands():
    """
    Get list of currently enabled command codes.

    Returns:
        list: Command codes (e.g., ['+', '-', '1', '2', '3', '4', 'h'])
    """
    return [code for code, cmd in GAME_COMMANDS.items() if cmd['enabled']]


def is_valid_command(code):
    """
    Check if command code is valid and enabled.

    Args:
        code: Command code (e.g., '+', '1', 'h')

    Returns:
        bool: True if valid and enabled
    """
    return code in GAME_COMMANDS and GAME_COMMANDS[code]['enabled']


def get_command_info(code):
    """
    Get full command definition.

    Args:
        code: Command code (e.g., '+')

    Returns:
        dict: Command definition or None if invalid
    """
    return GAME_COMMANDS.get(code)


def get_keypress_for_command(code):
    """
    Get the keypress to send to the game for a command.

    Args:
        code: Command code (e.g., '+')

    Returns:
        str: Keypress string for xdotool, or None if invalid
    """
    cmd = GAME_COMMANDS.get(code)
    return cmd['keypress'] if cmd and cmd['enabled'] else None
