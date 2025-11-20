"""
Game controller for sending keypresses to The Bibites using xdotool.

Handles window focus and keypress automation for game control.
"""

import subprocess
import time
from .config import GAME_WINDOW_ID


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
        # Focus window first
        subprocess.run(['xdotool', 'windowfocus', str(GAME_WINDOW_ID)], check=True)
        time.sleep(0.1)  # Brief delay for focus

        # Send keypress
        subprocess.run(['xdotool', 'key', '--window', str(GAME_WINDOW_ID), key], check=True)

        if log_func:
            log_func(f"Keypress: {key}", f"Sent to window {GAME_WINDOW_ID}")
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
