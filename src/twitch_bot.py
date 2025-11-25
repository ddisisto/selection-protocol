#!/usr/bin/env python3
"""
TwitchIO bot entry point for Selection Protocol.

Connects to Twitch EventSub and routes parsed chat input to Flask server.
"""

import asyncio
import requests
from datetime import datetime

# Import bot components from package
from .bot import ChatInputBot, parse_chat_input, log_chat_input


def get_user_id(username, client_id, token):
    """
    Get numeric user ID from username using Twitch API.

    Args:
        username: Twitch username
        client_id: Application client ID
        token: OAuth access token (without 'oauth:' prefix)

    Returns:
        Numeric user ID string
    """
    url = f"https://api.twitch.tv/helix/users?login={username}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    if not data.get("data"):
        raise ValueError(f"User '{username}' not found")

    return data["data"][0]["id"]


async def run_bot(client_id, client_secret, bot_id, owner_id, channel_id, access_token, bot_username, flask_url="http://localhost:5000"):
    """
    Run the Twitch EventSub bot.

    Startup sequence:
    1. Connect to Flask (exit if fail)
    2. Connect to Twitch EventSub (exit if fail)
    3. Report readiness
    4. Announce to chat

    Args:
        client_id: Application client ID
        client_secret: Application client secret
        bot_id: Bot user ID (numeric)
        owner_id: Channel owner user ID (numeric)
        channel_id: Channel ID (numeric) to monitor
        access_token: User access token for sending messages
        bot_username: Bot's Twitch username
        flask_url: Flask server URL
    """
    bot = ChatInputBot(client_id, client_secret, bot_id, owner_id, channel_id, access_token, bot_username, flask_url)

    # Step 1: Connect to Flask (MUST succeed)
    await bot.connect_to_flask()

    # Step 2: Connect to Twitch EventSub
    await bot.start()


if __name__ == '__main__':
    """
    Run bot standalone.

    Requires config.yaml with Twitch credentials.

    Usage:
        python -m src.twitch_bot          # Run forever (daemon mode)
        python -m src.twitch_bot --test   # Run for 30s then exit (test mode)
    """
    import yaml
    import sys
    from pathlib import Path

    # Check for test mode
    test_mode = '--test' in sys.argv or '--one-shot' in sys.argv

    # Load config
    config_path = Path(__file__).parent.parent / 'config.yaml'

    if not config_path.exists():
        print("Error: config.yaml not found!")
        print("\nSetup steps:")
        print("  1. Register app at https://dev.twitch.tv/console/apps")
        print("  2. Copy config.yaml.example to config.yaml")
        print("  3. Fill in your client_id and client_secret")
        print()
        print("     twitch:")
        print("       client_id: 'your_client_id_here'")
        print("       client_secret: 'your_client_secret_here'")
        print("       channel: 'your_channel_name'")
        print("       nick: 'your_channel_name'  # Same as channel for now")
        print()
        exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    twitch_config = config['twitch']

    mode_str = "TEST MODE (30s then exit)" if test_mode else "DAEMON MODE (runs forever)"
    print(f"Starting TwitchIO EventSub bot in {mode_str}")
    print("Getting user access token...")

    # Get user access token (from cache or OAuth flow)
    try:
        from .oauth_flow import get_token
        token = get_token(
            twitch_config['client_id'],
            twitch_config['client_secret']
        )

        if not token:
            print("✗ Failed to get access token")
            exit(1)

        print(f"✓ User access token obtained")

        # Auto-fetch bot_id and channel_id from usernames
        bot_id = get_user_id(
            twitch_config['nick'],
            twitch_config['client_id'],
            token
        )
        print(f"✓ Bot ID obtained: {bot_id} (for user: {twitch_config['nick']})")

        channel_id = get_user_id(
            twitch_config['channel'],
            twitch_config['client_id'],
            token
        )
        print(f"✓ Channel ID obtained: {channel_id} (for channel: {twitch_config['channel']})")

        # For personal bot, owner_id = bot_id
        owner_id = bot_id

        if test_mode:
            print(f"\nTest mode: Will run for 30 seconds then exit")
        print(f"\nType k, l, or x in chat to test command parsing\n")

        # Run bot
        if test_mode:
            # Test mode: run for 30s then exit cleanly
            async def run_test():
                bot = ChatInputBot(
                    twitch_config['client_id'],
                    twitch_config['client_secret'],
                    bot_id,
                    owner_id,
                    channel_id,
                    token,
                    twitch_config['nick'],
                    'http://localhost:5000'
                )

                # Step 1: Connect to Flask (MUST succeed)
                await bot.connect_to_flask()

                # Step 2: Start Twitch bot in background
                bot_task = asyncio.create_task(bot.start())

                # Wait 30 seconds
                await asyncio.sleep(30)

                # Clean shutdown
                print(f"\n{'='*60}")
                print("Test complete! Shutting down...")
                print(f"{'='*60}\n")
                await bot.close()
                if bot.sio:
                    await bot.sio.disconnect()
                bot_task.cancel()

            asyncio.run(run_test())
        else:
            # Daemon mode: run forever
            asyncio.run(run_bot(
                client_id=twitch_config['client_id'],
                client_secret=twitch_config['client_secret'],
                bot_id=bot_id,
                owner_id=owner_id,
                channel_id=channel_id,
                access_token=token,
                bot_username=twitch_config['nick'],
                flask_url='http://localhost:5000'
            ))
    except Exception as e:
        print(f"✗ Failed to initialize bot: {e}")
        print("\nCheck that your client_id, client_secret, and nick are correct")
        print("Get credentials from: https://dev.twitch.tv/console/apps")
        import traceback
        traceback.print_exc()
        exit(1)
