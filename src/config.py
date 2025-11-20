"""
Configuration values for the Twitch Plays God overlay server.

Contains game window settings, cooldown durations, and other configuration constants.
"""

# Game window configuration
GAME_WINDOW_ID = 132120577

# Cooldown durations in seconds
COOLDOWN_DURATIONS = {
    'primary': 15,   # Kill (Delete), Lay (Insert) - shared cooldown
    'camera': 10,    # Ctrl+G/O/R - shared cooldown
    'zoom_in': 5,    # KP+ - individual cooldown
    'zoom_out': 5,   # KP- - individual cooldown
    'extend': 30     # x - individual cooldown
}
