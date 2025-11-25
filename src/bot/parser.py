"""
Chat input parser for Selection Protocol.

Extracts single-character commands from Twitch chat messages.
"""


def parse_chat_input(message):
    """
    Parse first word from message following CHAT_UX.md spec.

    Extracts FIRST valid command character(s) before word boundary.
    Everything after first whitespace is commentary (ignored).

    Rules:
    - First word must be all repetitions of ONE character (case-insensitive)
    - Returns normalized lowercase char if valid
    - Returns None if invalid

    Examples:
        "k" → 'k'
        "k boring kill it" → 'k'
        "kkKkK! IT MUST DIE" → 'k'
        "l first!" → 'l'
        "+ zoom in" → '+'
        "I think k" → None (first char is 'i', not valid command)
        "let it live" → None (first word has multiple different chars)

    Args:
        message: Raw chat message

    Returns:
        str or None: Normalized command char or None if invalid
    """
    if not message:
        return None

    # Split by whitespace, take first word
    first_word = message.split()[0] if message.split() else message

    # Remove all non-alphanumeric except +/- (valid command chars)
    # This handles "kkK!" → "kkK"
    cleaned = ''.join(c for c in first_word if c.isalnum() or c in ['+', '-'])

    if not cleaned:
        return None

    # Check if all characters are the same (case-insensitive)
    normalized = cleaned.lower()
    if len(set(normalized)) == 1:
        return normalized[0]

    return None
