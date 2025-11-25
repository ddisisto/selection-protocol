"""
Consolidated logging for chat input processing.

Logs single line per message showing parse + server response.
"""

from datetime import datetime


def log_chat_input(username, raw_message, parsed_input, response):
    """
    Log single consolidated line showing chat input processing result.

    Format: [HH:MM:SS] username: "raw_message" → parsed (type:X, accepted:Y, ...)

    Args:
        username: Twitch username
        raw_message: Raw chat message
        parsed_input: Parsed single char or None
        response: Server response dict with type, accepted, reason, etc.
    """
    timestamp = datetime.now().strftime('%H:%M:%S')

    if parsed_input is None:
        # Not a command, don't log (too verbose)
        return

    # Build response details
    type_str = response.get('type', 'unknown')
    accepted = response.get('accepted', False)
    reason = response.get('reason', '')
    cooldown = response.get('cooldown_remaining', 0)

    # Format: [12:34:56] alice: "k boring" → k (type:vote, accepted:true)
    details = f"type:{type_str}, accepted:{accepted}"
    if reason:
        details += f", reason:{reason}"
    if cooldown > 0:
        details += f", remaining:{cooldown:.1f}s"

    print(f'[{timestamp}] {username}: "{raw_message}" → {parsed_input} ({details})')
