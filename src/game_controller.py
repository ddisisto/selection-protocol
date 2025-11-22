"""
Game controller for sending keypresses to The Bibites using xdotool.

Handles window focus and keypress automation for game control.
"""

import subprocess
import time

# Global window ID (discovered at runtime)
_GAME_WINDOW_ID = None


def discover_game_window():
    """
    Auto-discover The Bibites window ID.

    Searches for window with name "The Bibites".
    Fails fast if not found or multiple windows exist.

    Returns:
        int: Window ID

    Raises:
        RuntimeError: If window not found or multiple windows found
    """
    try:
        result = subprocess.run(
            ['xdotool', 'search', '--name', 'The Bibites'],
            capture_output=True,
            text=True,
            check=True
        )

        window_ids = result.stdout.strip().split('\n')
        window_ids = [wid for wid in window_ids if wid]  # Filter empty strings

        if len(window_ids) == 0:
            raise RuntimeError(
                "The Bibites window not found. "
                "Please ensure the game is running before starting the server."
            )

        if len(window_ids) > 1:
            raise RuntimeError(
                f"Multiple Bibites windows found ({len(window_ids)}). "
                f"Please close duplicate windows. IDs: {', '.join(window_ids)}"
            )

        window_id = int(window_ids[0])

        # Verify we can get the window name
        verify_result = subprocess.run(
            ['xdotool', 'getwindowname', str(window_id)],
            capture_output=True,
            text=True,
            check=True
        )

        window_name = verify_result.stdout.strip()
        print(f"✓ Discovered game window: '{window_name}' (ID: {window_id})")

        return window_id

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"xdotool error during window discovery: {e}")
    except FileNotFoundError:
        raise RuntimeError("xdotool not found. Please install xdotool.")


def set_game_window_id(window_id):
    """Set the game window ID (called at server startup)."""
    global _GAME_WINDOW_ID
    _GAME_WINDOW_ID = window_id


def get_game_window_id():
    """Get the current game window ID."""
    if _GAME_WINDOW_ID is None:
        raise RuntimeError("Game window ID not set. Call discover_game_window() first.")
    return _GAME_WINDOW_ID


def send_keypress(key, log_func=None):
    """
    Send keypress to game window using xdotool.

    Args:
        key: Key to send (e.g., 'Delete', 'Insert', 'ctrl+g')
        log_func: Optional logging function to call with action details

    Returns:
        dict: Result with 'success' boolean and optional 'error' message
    """
    try:
        window_id = get_game_window_id()

        # Focus window first
        subprocess.run(['xdotool', 'windowfocus', str(window_id)], check=True)
        time.sleep(0.1)  # Brief delay for focus

        # Send keypress
        subprocess.run(['xdotool', 'key', '--window', str(window_id), key], check=True)

        if log_func:
            log_func(f"Keypress: {key}", f"Sent to window {window_id}")
        return {'success': True, 'key': key}
    except subprocess.CalledProcessError as e:
        error_msg = f"xdotool failed: {e}"
        if log_func:
            log_func(f"Keypress FAILED: {key}", error_msg)
        return {'success': False, 'error': error_msg}
    except FileNotFoundError:
        error_msg = "xdotool not found"
        if log_func:
            log_func(f"Keypress FAILED: {key}", error_msg)
        return {'success': False, 'error': error_msg}
    except RuntimeError as e:
        error_msg = str(e)
        if log_func:
            log_func(f"Keypress FAILED: {key}", error_msg)
        return {'success': False, 'error': error_msg}
