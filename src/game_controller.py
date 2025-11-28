"""
Game controller for sending keypresses to The Bibites using xdotool.

Handles window focus and keypress automation for game control.
Provides exclusive IO access via context managers.
"""

import subprocess
import time
import yaml
from pathlib import Path
from contextlib import contextmanager

# Global window ID (discovered at runtime)
_GAME_WINDOW_ID = None

# Global IO lock (simple flag, no threading anticipated)
_io_in_use = False


def discover_game_window():
    """
    Auto-discover The Bibites window ID.

    Reads window title from config.yaml and searches for matching window.
    Fails fast if not found or multiple windows exist.

    Returns:
        int: Window ID

    Raises:
        RuntimeError: If window not found or multiple windows found
    """
    # Load window title from config
    config_path = Path(__file__).parent.parent / 'config.yaml'
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        window_title = config['game']['window_title']
    except FileNotFoundError:
        raise RuntimeError(
            f"Config file not found: {config_path}\n"
            "Copy config.yaml.example to config.yaml and configure it."
        )
    except KeyError as e:
        raise RuntimeError(f"Missing config key: {e}")

    try:
        result = subprocess.run(
            ['xdotool', 'search', '--name', window_title],
            capture_output=True,
            text=True,
            check=True
        )

        window_ids = result.stdout.strip().split('\n')
        window_ids = [wid for wid in window_ids if wid]  # Filter empty strings

        if len(window_ids) == 0:
            raise RuntimeError(
                f"Game window not found: '{window_title}'\n"
                "Please ensure the game is running before starting the server."
            )

        if len(window_ids) > 1:
            raise RuntimeError(
                f"Multiple game windows found ({len(window_ids)}). "
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

    DEPRECATED: Use `with io() as io: io.keypress(key)` instead.
    Kept for backward compatibility during migration.

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


# ============================================================
# EXCLUSIVE IO CONTEXT MANAGER PATTERN
# ============================================================

class GameIO:
    """
    Provides game IO methods within exclusive access context.

    All xdotool interactions should go through this class.
    Instantiated by io() context manager only.
    """

    def __init__(self):
        """Initialize GameIO. Should only be called by io() context manager."""
        pass

    def keypress(self, key, log_func=None):
        """
        Send keypress to game window.

        Args:
            key: Key to send (e.g., 'Delete', 'Insert', 'ctrl+g')
            log_func: Optional logging function

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

    def click(self, x, y, log_func=None):
        """
        Click at window-relative coordinates.

        Args:
            x: X coordinate (window-relative)
            y: Y coordinate (window-relative)
            log_func: Optional logging function

        Returns:
            dict: Result with 'success' boolean and optional 'error' message
        """
        try:
            window_id = get_game_window_id()

            # Focus window first
            subprocess.run(['xdotool', 'windowfocus', str(window_id)], check=True)
            time.sleep(0.1)

            # Move mouse and click (window-relative)
            subprocess.run(['xdotool', 'mousemove', '--window', str(window_id), str(x), str(y)], check=True)
            time.sleep(0.05)
            subprocess.run(['xdotool', 'click', '--window', str(window_id), '1'], check=True)

            if log_func:
                log_func(f"Click: ({x}, {y})", f"Window {window_id}")
            return {'success': True, 'x': x, 'y': y}
        except subprocess.CalledProcessError as e:
            error_msg = f"xdotool click failed: {e}"
            if log_func:
                log_func(f"Click FAILED: ({x}, {y})", error_msg)
            return {'success': False, 'error': error_msg}
        except FileNotFoundError:
            error_msg = "xdotool not found"
            if log_func:
                log_func(f"Click FAILED: ({x}, {y})", error_msg)
            return {'success': False, 'error': error_msg}
        except RuntimeError as e:
            error_msg = str(e)
            if log_func:
                log_func(f"Click FAILED: ({x}, {y})", error_msg)
            return {'success': False, 'error': error_msg}

    def read_clipboard(self, log_func=None):
        """
        Read text from system clipboard.

        Args:
            log_func: Optional logging function

        Returns:
            str: Clipboard contents (empty string if clipboard is empty or on error)
        """
        try:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True,
                check=False  # Don't raise on empty clipboard
            )
            content = result.stdout
            if log_func:
                log_func("Clipboard read", f"Length: {len(content)} chars")
            return content
        except FileNotFoundError:
            if log_func:
                log_func("Clipboard read FAILED", "xclip not found")
            return ""
        except Exception as e:
            if log_func:
                log_func("Clipboard read FAILED", str(e))
            return ""

    def write_clipboard(self, text, log_func=None):
        """
        Write text to system clipboard.

        Args:
            text: Text to write to clipboard
            log_func: Optional logging function

        Returns:
            dict: Result with 'success' boolean and optional 'error' message
        """
        try:
            subprocess.run(
                ['xclip', '-selection', 'clipboard'],
                input=text,
                text=True,
                check=True
            )
            if log_func:
                log_func("Clipboard write", f"'{text}' ({len(text)} chars)")
            return {'success': True, 'text': text}
        except FileNotFoundError:
            error_msg = "xclip not found"
            if log_func:
                log_func("Clipboard write FAILED", error_msg)
            return {'success': False, 'error': error_msg}
        except subprocess.CalledProcessError as e:
            error_msg = f"xclip failed: {e}"
            if log_func:
                log_func("Clipboard write FAILED", error_msg)
            return {'success': False, 'error': error_msg}


@contextmanager
def io():
    """
    Acquire exclusive game IO access.

    Provides GameIO object for keypress, click, and clipboard operations.
    Prevents concurrent IO to game window.

    Raises:
        RuntimeError: If IO already in use (concurrent access)

    Yields:
        GameIO: Object with keypress/click/clipboard methods

    Example:
        with io() as io:
            io.keypress('space')
            io.click(225, 225)
            text = io.read_clipboard()
    """
    global _io_in_use

    if _io_in_use:
        raise RuntimeError("Game IO already in use (concurrent access)")

    _io_in_use = True
    try:
        yield GameIO()
    finally:
        _io_in_use = False
