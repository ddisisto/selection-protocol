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

    def __init__(self, token, channel, nick, vote_manager=None):
        """
        Initialize the TwitchIO bot.

        Args:
            token: OAuth token (with 'oauth:' prefix)
            channel: Twitch channel name to join
            nick: Bot's username
            vote_manager: VoteManager instance to receive votes (None for testing)
        """
        super().__init__(
            token=token,
            prefix='!',  # For future commands like !lineage
            initial_channels=[channel]
        )
        self.vote_manager = vote_manager
        self.channel_name = channel
        self.start_time = datetime.now()
        self.votes_received = 0

    async def event_ready(self):
        """Called when bot connects to Twitch IRC."""
        print(f"\n{'='*60}")
        print(f"TwitchIO Bot Connected!")
        print(f"{'='*60}")
        print(f"Bot username: {self.nick}")
        print(f"Joined channel: #{self.channel_name}")
        print(f"Connected at: {self.start_time.strftime('%H:%M:%S')}")
        print(f"\nListening for commands: k (kill), l (lay), x (extend)")
        print(f"{'='*60}\n")

    async def event_message(self, message):
        """
        Handle incoming chat messages.

        Parses k/l/x commands and passes them to vote manager.
        Ignores bot's own messages.
        """
        # Ignore messages from the bot itself
        if message.echo:
            return

        # Handle bot commands (like !lineage) - delegates to commands framework
        await self.handle_commands(message)

        # Parse vote commands
        content = message.content.lower().strip()
        username = message.author.name

        # Check if message is a valid vote command
        if content in ['k', 'l', 'x']:
            self.votes_received += 1
            timestamp = datetime.now()

            # Log vote
            print(f"[{timestamp.strftime('%H:%M:%S')}] Vote from {username}: {content.upper()}")

            # Pass to vote manager (if connected)
            if self.vote_manager:
                self.vote_manager.cast_vote(username, content, timestamp)
            else:
                print(f"  → No vote manager connected (skeleton mode)")

    async def event_error(self, error, data=None):
        """Handle bot errors."""
        print(f"Bot error: {error}")
        if data:
            print(f"  Data: {data}")

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


async def run_bot(token, channel, nick, vote_manager=None):
    """
    Run the Twitch bot.

    Args:
        token: OAuth token (with 'oauth:' prefix)
        channel: Channel to join
        nick: Bot username
        vote_manager: VoteManager instance (optional)
    """
    bot = SelectionBot(token, channel, nick, vote_manager)
    await bot.start()


if __name__ == '__main__':
    """
    Test mode - runs bot standalone without vote manager.

    Requires config.yaml with Twitch credentials.
    """
    import yaml
    from pathlib import Path

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
        print("       nick: 'your_bot_username'")
        print()
        exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    twitch_config = config['twitch']

    print("Starting TwitchIO bot in TEST MODE (no vote manager)")
    print("Fetching OAuth token using client credentials...")

    # Get token automatically from client_id/client_secret
    try:
        token = get_app_access_token(
            twitch_config['client_id'],
            twitch_config['client_secret']
        )
        print(f"✓ OAuth token obtained")
        print(f"\nType k, l, or x in chat to test command parsing\n")

        # Run bot without vote manager (test mode)
        asyncio.run(run_bot(
            token=f"oauth:{token}",
            channel=twitch_config['channel'],
            nick=twitch_config['nick'],
            vote_manager=None
        ))
    except Exception as e:
        print(f"✗ Failed to get OAuth token: {e}")
        print("\nCheck that your client_id and client_secret are correct")
        print("Get them from: https://dev.twitch.tv/console/apps")
        exit(1)
