#!/usr/bin/env python3
"""
TwitchIO bot for Selection Protocol.

Connects to Twitch IRC chat and parses k/l/x commands from viewers.
Passes vote data to the vote manager for tracking and resolution.
"""

import asyncio
import requests
from twitchio.ext import commands
from datetime import datetime


class SelectionBot(commands.Bot):
    """
    Twitch IRC bot for parsing vote commands (k/l/x) from chat.

    Commands:
    - k: Kill current bibite (Delete key)
    - l: Lay egg, reproduce (Insert key)
    - x: Extend, keep watching (do nothing)
    """

    def __init__(self, token, channel, nick, client_id, client_secret, bot_id, vote_manager=None):
        """
        Initialize the TwitchIO bot.

        Args:
            token: OAuth token (with 'oauth:' prefix)
            channel: Twitch channel name to join
            nick: Bot's username
            client_id: Application client ID
            client_secret: Application client secret
            bot_id: Bot user ID (numeric, from Twitch)
            vote_manager: VoteManager instance to receive votes (None for testing)
        """
        # Initialize with IRC capabilities
        super().__init__(
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            prefix='!',  # For future commands like !lineage
            initial_channels=[channel],
            # Enable IRC tags and membership for proper message receiving
            capabilities=["tags", "membership", "commands"]
        )
        self.vote_manager = vote_manager
        self.channel_name = channel
        self.start_time = datetime.now()
        self.votes_received = 0
        self.messages_received = 0

    async def event_ready(self):
        """Called when bot connects to Twitch IRC."""
        print(f"\n{'='*60}")
        print(f"TwitchIO Bot Connected!")
        print(f"{'='*60}")
        print(f"Joined channel: #{self.channel_name}")
        print(f"Connected at: {self.start_time.strftime('%H:%M:%S')}")
        print(f"\nListening for commands: k (kill), l (lay), x (extend)")
        print(f"{'='*60}\n")

        # Send a startup message to chat (skip for now, focus on receiving)
        # TODO: Fix sending messages once receiving works
        print(f"(Skipping startup message for now, will fix once receiving works)")

        # Start heartbeat task
        import asyncio
        asyncio.create_task(self._heartbeat())

    async def event_message(self, message):
        """
        Handle incoming chat messages.

        Parses k/l/x commands and passes them to vote manager.
        Ignores bot's own messages.
        """
        # Debug: log that we received ANY message at all
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Ignore messages from the bot itself
        if message.echo:
            print(f"[{timestamp}] (ignored bot's own message)")
            return

        self.messages_received += 1
        username = message.author.name if message.author else "Unknown"
        content = message.content

        # Log ALL chat messages
        print(f"[{timestamp}] {username}: {content}")

        # Handle bot commands (like !lineage) - delegates to commands framework
        await self.handle_commands(message)

        # Parse vote commands
        content_lower = content.lower().strip()

        # Check if message is a valid vote command
        if content_lower in ['k', 'l', 'x']:
            self.votes_received += 1

            # Log vote (highlighted)
            print(f"  → VOTE: {content_lower.upper()}")

            # Pass to vote manager (if connected)
            if self.vote_manager:
                self.vote_manager.cast_vote(username, content_lower, datetime.now())
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
        import asyncio
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


def get_app_access_token(client_id, client_secret):
    """
    Get app access token using client credentials flow.

    Args:
        client_id: Your application's client ID
        client_secret: Your application's client secret

    Returns:
        OAuth token string (without 'oauth:' prefix)
    """
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    response = requests.post(url, params=params)
    response.raise_for_status()

    data = response.json()
    return data["access_token"]


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


async def run_bot(token, channel, nick, client_id, client_secret, bot_id, vote_manager=None):
    """
    Run the Twitch bot.

    Args:
        token: OAuth token (with 'oauth:' prefix)
        channel: Channel to join
        nick: Bot username
        client_id: Application client ID
        client_secret: Application client secret
        bot_id: Bot user ID (numeric)
        vote_manager: VoteManager instance (optional)
    """
    bot = SelectionBot(token, channel, nick, client_id, client_secret, bot_id, vote_manager)
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
    print(f"Starting TwitchIO bot in {mode_str}")
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

        # Auto-fetch bot_id from username
        bot_id = get_user_id(
            twitch_config['nick'],
            twitch_config['client_id'],
            token
        )
        print(f"✓ Bot ID obtained: {bot_id} (for user: {twitch_config['nick']})")

        if test_mode:
            print(f"\nTest mode: Will run for 30 seconds then exit")
        print(f"\nType k, l, or x in chat to test command parsing\n")

        # Run bot without vote manager
        if test_mode:
            # Test mode: run for 30s then exit cleanly
            async def run_test():
                bot = SelectionBot(
                    f"oauth:{token}",
                    twitch_config['channel'],
                    twitch_config['nick'],
                    twitch_config['client_id'],
                    twitch_config['client_secret'],
                    bot_id,
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
                token=f"oauth:{token}",
                channel=twitch_config['channel'],
                nick=twitch_config['nick'],
                client_id=twitch_config['client_id'],
                client_secret=twitch_config['client_secret'],
                bot_id=bot_id,
                vote_manager=None
            ))
    except Exception as e:
        print(f"✗ Failed to initialize bot: {e}")
        print("\nCheck that your client_id, client_secret, and nick are correct")
        print("Get credentials from: https://dev.twitch.tv/console/apps")
        exit(1)
