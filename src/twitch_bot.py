#!/usr/bin/env python3
"""
TwitchIO bot for Selection Protocol using EventSub.

Connects to Twitch EventSub WebSocket and parses k/l/x commands from viewers.
Passes vote data to the vote manager for tracking and resolution.
"""

import asyncio
import requests
from twitchio.ext import commands
from twitchio import eventsub, eventsub_
from datetime import datetime


class SelectionBot(commands.AutoBot):
    """
    Twitch EventSub bot for parsing vote commands (k/l/x) from chat.

    Commands:
    - k: Kill current bibite (Delete key)
    - l: Lay egg, reproduce (Insert key)
    - x: Extend, keep watching (do nothing)
    """

    def __init__(self, client_id, client_secret, bot_id, owner_id, channel_id, vote_manager=None):
        """
        Initialize the TwitchIO EventSub bot.

        Args:
            client_id: Application client ID
            client_secret: Application client secret
            bot_id: Bot user ID (numeric, from Twitch)
            owner_id: Channel owner user ID (numeric) - same as bot_id for personal bot
            channel_id: Channel ID (numeric) to monitor chat in
            vote_manager: VoteManager instance to receive votes (None for testing)
        """
        # Initialize with EventSub support
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            owner_id=owner_id,
            prefix='!',  # For future commands like !lineage
            force_subscribe=True,  # Auto-subscribe to EventSub events
        )
        self.vote_manager = vote_manager
        self.channel_id = channel_id
        self.start_time = datetime.now()
        self.votes_received = 0
        self.messages_received = 0

    async def event_ready(self):
        """Called when bot connects to Twitch EventSub."""
        print(f"\n{'='*60}")
        print(f"TwitchIO EventSub Bot Connected!")
        print(f"{'='*60}")
        print(f"Bot ID: {self.bot_id}")
        print(f"Channel ID: {self.channel_id}")
        print(f"Connected at: {self.start_time.strftime('%H:%M:%S')}")
        print(f"\nListening for commands: k (kill), l (lay), x (extend)")
        print(f"{'='*60}\n")

        # Subscribe to chat messages for our channel
        try:
            subs = [
                eventsub.ChatMessageSubscription(
                    broadcaster_user_id=self.channel_id,
                    user_id=self.bot_id
                ),
            ]
            await self.multi_subscribe(subs)
            print("✓ Subscribed to chat message events")
        except Exception as e:
            print(f"✗ Failed to subscribe to EventSub: {e}")
            raise

        # Start heartbeat task
        asyncio.create_task(self._heartbeat())

    @commands.Component.listener()
    async def event_message(self, payload: eventsub_.ChatMessage):
        """
        Handle incoming chat messages from EventSub.

        Args:
            payload: EventSub ChatMessage payload with chatter info and text
        """
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Extract username and message text from EventSub payload
        username = payload.chatter.name
        text = payload.text

        self.messages_received += 1

        # Log ALL chat messages
        print(f"[{timestamp}] {username}: {text}")

        # Parse vote commands
        text_lower = text.lower().strip()

        # Check if message is a valid vote command
        if text_lower in ['k', 'l', 'x']:
            self.votes_received += 1

            # Log vote (highlighted)
            print(f"  → VOTE: {text_lower.upper()}")

            # Pass to vote manager (if connected)
            if self.vote_manager:
                self.vote_manager.cast_vote(username, text_lower, datetime.now())
            else:
                print(f"  → No vote manager connected (skeleton mode)")

    async def event_error(self, error, data=None):
        """Handle bot errors - print details and crash."""
        print(f"\n{'='*60}")
        print(f"FATAL ERROR")
        print(f"{'='*60}")
        print(f"Error type: {type(error)}")

        # EventErrorPayload has specific attributes
        if hasattr(error, 'error'):
            print(f"\nActual error: {error.error}")
        if hasattr(error, 'exception'):
            print(f"\nException: {error.exception}")
        if hasattr(error, '__dict__'):
            print(f"\nAll error attributes:")
            for key, value in error.__dict__.items():
                print(f"  {key}: {value}")
        if data:
            print(f"\nAdditional data: {data}")

        print(f"\n{'='*60}")
        print(f"Bot cannot continue. Exiting.")
        print(f"{'='*60}\n")

        # Crash hard
        import sys
        sys.exit(1)

    async def _heartbeat(self):
        """Print periodic stats to show bot is alive."""
        while True:
            await asyncio.sleep(10)
            uptime = (datetime.now() - self.start_time).seconds
            print(f"[Heartbeat] Uptime: {uptime}s | Messages: {self.messages_received} | Votes: {self.votes_received}")

    @commands.command(name='lineage')
    async def lineage_command(self, ctx):
        """Show user's lineage stats (future implementation)."""
        username = ctx.author.name
        await ctx.send(f"@{username} Lineage tracking coming soon! 🔥")

    @commands.command(name='stats')
    async def stats_command(self, ctx):
        """Show overall voting stats (future implementation)."""
        await ctx.send(f"Stats: {self.votes_received} votes received since bot started.")


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


async def run_bot(client_id, client_secret, bot_id, owner_id, channel_id, vote_manager=None):
    """
    Run the Twitch EventSub bot.

    Args:
        client_id: Application client ID
        client_secret: Application client secret
        bot_id: Bot user ID (numeric)
        owner_id: Channel owner user ID (numeric)
        channel_id: Channel ID (numeric) to monitor
        vote_manager: VoteManager instance (optional)
    """
    bot = SelectionBot(client_id, client_secret, bot_id, owner_id, channel_id, vote_manager)
    await bot.start()


if __name__ == '__main__':
    """
    Test mode - runs bot standalone without vote manager.

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

        # Run bot without vote manager
        if test_mode:
            # Test mode: run for 30s then exit cleanly
            async def run_test():
                bot = SelectionBot(
                    twitch_config['client_id'],
                    twitch_config['client_secret'],
                    bot_id,
                    owner_id,
                    channel_id,
                    None
                )
                # Start bot in background
                bot_task = asyncio.create_task(bot.start())

                # Wait 30 seconds
                await asyncio.sleep(30)

                # Clean shutdown
                print(f"\n{'='*60}")
                print("Test complete! Shutting down...")
                print(f"{'='*60}\n")
                await bot.close()
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
                vote_manager=None
            ))
    except Exception as e:
        print(f"✗ Failed to initialize bot: {e}")
        print("\nCheck that your client_id, client_secret, and nick are correct")
        print("Get credentials from: https://dev.twitch.tv/console/apps")
        import traceback
        traceback.print_exc()
        exit(1)
