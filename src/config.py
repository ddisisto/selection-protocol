"""
Configuration values for the Twitch Plays God overlay server.

Contains cooldown durations and other configuration constants.

Note: Game window ID is auto-discovered at runtime via game_controller.discover_game_window()
"""

# Cooldown durations in seconds
COOLDOWN_DURATIONS = {
    'primary': 15,   # Kill (Delete), Lay (Insert) - shared cooldown
    'camera': 10,    # Ctrl+G/O/R - shared cooldown
    'zoom_in': 5,    # KP+ - individual cooldown
    'zoom_out': 5,   # KP- - individual cooldown
    'extend': 30     # x - individual cooldown
}
