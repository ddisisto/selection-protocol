#!/usr/bin/env python3
"""
TwitchIO bot for Selection Protocol using EventSub.

Connects to Twitch EventSub WebSocket and parses k/l/x commands from viewers.
Passes vote data to the vote manager for tracking and resolution.
"""

import asyncio
import requests
import socketio
from twitchio.ext import commands
from twitchio import eventsub, eventsub_
from datetime import datetime
import sys


def parse_first_word(message):
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


class SelectionBot(commands.AutoBot):
    """
    Twitch EventSub bot for parsing vote commands (k/l/x) from chat.

    Commands:
    - k: Kill current bibite (Delete key)
    - l: Lay egg, reproduce (Insert key)
    - x: Extend, keep watching (do nothing)
    """

    def __init__(self, client_id, client_secret, bot_id, owner_id, channel_id, access_token, bot_username, flask_url="http://localhost:5000"):
        """
        Initialize the TwitchIO EventSub bot.

        Args:
            client_id: Application client ID
            client_secret: Application client secret
            bot_id: Bot user ID (numeric, from Twitch)
            owner_id: Channel owner user ID (numeric) - same as bot_id for personal bot
            channel_id: Channel ID (numeric) to monitor chat in
            access_token: User access token for sending messages
            bot_username: Bot's Twitch username (for filtering own messages)
            flask_url: Flask server URL for SocketIO connection
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
        self.channel_id = channel_id
        self.start_time = datetime.now()
        self.votes_received = 0
        self.messages_received = 0
        # Store for chat message sending and filtering
        self._client_id = client_id
        self._access_token = access_token
        self._bot_username = bot_username.lower()
        self._flask_url = flask_url

        # SocketIO client (will be initialized in connect_to_flask)
        self.sio = None
        self.valid_actions = set()
        self.game_commands_received = 0

    def _validate_token(self):
        """
        Validate access token and check scopes.

        Exits if token user doesn't match bot user (common auth mistake).
        """
        try:
            url = "https://id.twitch.tv/oauth2/validate"
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            token_user_id = data.get('user_id')
            token_login = data.get('login')

            print("\n" + "=" * 60)
            print("Token Validation")
            print("=" * 60)
            print(f"Token User ID: {token_user_id}")
            print(f"Token Login: {token_login}")
            print(f"Bot ID (expected): {self.bot_id}")
            print(f"Bot Username: {self._bot_username}")
            print(f"Expires in: {data.get('expires_in')}s")
            print(f"Scopes: {', '.join(data.get('scopes', []))}")

            # Check if token user matches bot user (CRITICAL)
            if str(token_user_id) != str(self.bot_id):
                print(f"\n{'='*60}")
                print("✗ FATAL: Token user mismatch")
                print(f"{'='*60}")
                print(f"\nToken belongs to: {token_login} (ID: {token_user_id})")
                print(f"But bot expects: {self._bot_username} (ID: {self.bot_id})")
                print(f"\nTo fix:")
                print(f"  1. Log OUT of Twitch in your browser")
                print(f"  2. Log IN as: {self._bot_username}")
                print(f"  3. Delete .twitch_token")
                print(f"  4. Run bot again to re-authorize")
                print(f"\nThe token MUST be authorized by the bot account, not the channel owner.")
                print(f"{'='*60}\n")
                sys.exit(1)

            # Check required scopes
            required = ['chat:read', 'chat:edit', 'user:read:chat', 'user:write:chat', 'user:bot', 'channel:bot']
            actual = set(data.get('scopes', []))
            missing = [s for s in required if s not in actual]

            if missing:
                print(f"\n{'='*60}")
                print("✗ FATAL: Missing required scopes")
                print(f"{'='*60}")
                print(f"\nMissing: {', '.join(missing)}")
                print(f"\nDelete .twitch_token and re-authorize to get all scopes")
                print(f"{'='*60}\n")
                sys.exit(1)

            print(f"\n✓ Token valid and matches bot user")
            print(f"✓ All required scopes present")
            print("=" * 60 + "\n")

        except Exception as e:
            print(f"\n✗ Token validation failed: {e}")
            print(f"  Token may be invalid or expired\n")
            sys.exit(1)

    async def connect_to_flask(self):
        """
        Connect to Flask server via SocketIO and fetch enabled actions.

        This MUST succeed before connecting to Twitch.
        Exits immediately if connection fails.
        """
        print("=" * 60)
        print("Connecting to Flask server...")
        print("=" * 60)

        try:
            # Create async SocketIO client
            self.sio = socketio.AsyncClient()

            # Connect to Flask
            print(f"Connecting to {self._flask_url}...")
            await self.sio.connect(self._flask_url)
            print("✓ Connected to Flask server")

            # Fetch enabled actions
            print("Fetching enabled actions...")
            actions = await self.sio.call('get_actions', timeout=5)
            self.valid_actions = set(actions)
            print(f"✓ Loaded {len(self.valid_actions)} valid actions: {sorted(self.valid_actions)}")

            # Register event handlers for vote_manager events
            self._register_vote_events()

            # Send bot connection status
            await self.sio.emit('bot_connected', {
                'bot_id': self.bot_id,
                'bot_username': self._bot_username,
                'timestamp': datetime.now().isoformat()
            })
            print("✓ Bot status sent to Flask")

            # Validate token and check scopes
            self._validate_token()

            print("=" * 60)
            return True

        except Exception as e:
            print(f"\n✗ FATAL: Failed to connect to Flask server")
            print(f"  Error: {e}")
            print(f"  Make sure Flask server is running at {self._flask_url}")
            print(f"  Start it with: python -m src.server")
            print("=" * 60)
            sys.exit(1)

    async def _send_chat_message(self, message, color='blue'):
        """
        Send a message to Twitch chat with colored announcement.

        Args:
            message: Text to send to chat
            color: Announcement color ('blue', 'green', or 'orange')
                   - Blue: default/neutral
                   - Green: L-related (lay, reproduce)
                   - Orange: K-related (kill)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Prefix message with colored announcement command
            colored_message = f"/announce{color} {message}"

            url = "https://api.twitch.tv/helix/chat/messages"
            headers = {
                "Client-ID": self._client_id,
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "broadcaster_id": self.channel_id,
                "sender_id": self.bot_id,
                "message": colored_message
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return True

        except requests.exceptions.HTTPError as e:
            print(f"⚠ Failed to send chat message: HTTP {e.response.status_code}")
            print(f"  URL: {url}")
            print(f"  Response body: {e.response.text}")
            print(f"  Headers used:")
            print(f"    Client-ID: {self._client_id[:10]}...")
            print(f"    Bot ID: {self.bot_id}")
            print(f"    Channel ID: {self.channel_id}")
            return False
        except Exception as e:
            print(f"⚠ Failed to send chat message: {type(e).__name__}: {e}")
            return False

    def _register_vote_events(self):
        """
        Register SocketIO event handlers for vote_manager events.

        Handles:
        - round_start: Announce round opened by first voter
        - round_end: Announce winner and vote summary
        """
        @self.sio.on('round_start')
        async def on_round_start(data):
            """Handle round start announcement."""
            username = data.get('username', 'Unknown')
            vote = data.get('vote', '').upper()
            timer = data.get('timer_limit', 30)

            # Color based on initial vote: K=orange, L=green, X=blue
            color = 'orange' if vote == 'K' else ('green' if vote == 'L' else 'blue')

            message = f"Voting opened by @{username}: {vote}, {timer}s to have your say: K,L,X"
            success = await self._send_chat_message(message, color=color)

            if success:
                print(f"✓ Round start announced: {username} voted {vote}")
            else:
                print(f"✗ Failed to announce round start")

        @self.sio.on('round_end')
        async def on_round_end(data):
            """Handle round end summary."""
            winner = data.get('winner', 'x')
            k_votes = data.get('k_votes', 0)
            l_votes = data.get('l_votes', 0)
            x_votes = data.get('x_votes', 0)
            claimant = data.get('first_l_claimant')

            # Color based on winner: K=orange, L=green, X=blue
            color = 'orange' if winner == 'k' else ('green' if winner == 'l' else 'blue')

            # Build vote count string (omit zeros)
            vote_parts = []
            if k_votes > 0:
                vote_parts.append(f"K:{k_votes}")
            if l_votes > 0:
                vote_parts.append(f"L:{l_votes}")
            if x_votes > 0:
                vote_parts.append(f"X:{x_votes}")
            vote_str = ", ".join(vote_parts) if vote_parts else "No votes"

            # Build message based on winner
            if winner == 'k':
                message = f"K wins! Kill executed ({vote_str}) • Round reset"
            elif winner == 'l':
                claimant_str = f"@{claimant}" if claimant else "Unknown"
                message = f"L wins! {claimant_str} claims lineage • Lay executed ({vote_str}) • Round reset"
            else:  # x wins
                message = f"X wins (tie/no action) • {vote_str} • Round reset"

            success = await self._send_chat_message(message, color=color)

            if success:
                print(f"✓ Round end announced: {winner.upper()} wins")
            else:
                print(f"✗ Failed to announce round end")

    async def event_ready(self):
        """Called when bot connects to Twitch EventSub."""
        print(f"\n{'='*60}")
        print(f"TwitchIO EventSub Bot Connected!")
        print(f"{'='*60}")
        print(f"Bot ID: {self.bot_id}")
        print(f"Channel ID: {self.channel_id}")
        print(f"Connected at: {self.start_time.strftime('%H:%M:%S')}")
        print(f"\nListening for:")
        print(f"  Votes: k (kill), l (lay), x (extend)")
        print(f"  Commands: +/- (zoom), 0-4 (info panels, 0=hide)")
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

        # Send startup announcement to chat
        asyncio.create_task(self._send_startup_announcement())

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

        # Filter out bot's own messages (prevents announcement loops)
        if str(payload.chatter.id) == str(self.bot_id):
            return

        self.messages_received += 1

        # Log ALL chat messages
        print(f"[{timestamp}] {username}: {text}")

        # Parse first word from message (CHAT_UX.md spec)
        command = parse_first_word(text)

        # Skip if no valid command parsed
        if not command:
            return

        # Check if message is a valid vote command (k/l/x)
        if command in self.valid_actions:
            self.votes_received += 1

            # Log vote (highlighted)
            print(f"  → VOTE: {command.upper()}")

            # Send vote to Flask via SocketIO
            try:
                await self.sio.emit('vote_cast', {
                    'username': username,
                    'vote': command,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"  ⚠ Failed to send vote to Flask: {e}")

        # Check if message is a potential game command (any single character)
        # Server validates, determines keypress, and responds with accept/reject
        elif len(command) == 1:
            self.game_commands_received += 1

            # Log command (highlighted)
            print(f"  → COMMAND: {command}")

            # Send command to Flask via SocketIO (server validates and executes)
            try:
                await self.sio.emit('game_command', {
                    'username': username,
                    'command': command,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"  ⚠ Failed to send game command to Flask: {e}")

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

    async def _send_startup_announcement(self):
        """Send startup message to chat (blue announcement)."""
        # Wait a moment for EventSub to be fully ready
        await asyncio.sleep(2)

        message = "Selection Protocol online. Vote: k (kill) | l (lay) | x (extend) • Commands: +/- (zoom) | 0-4 (info panels, 0=hide)"
        success = await self._send_chat_message(message, color='blue')

        if success:
            print("✓ Startup announcement sent to chat")
        else:
            print(f"\n{'='*60}")
            print("✗ FATAL: Failed to send startup announcement")
            print(f"{'='*60}")
            print("\nPossible causes:")
            print("  1. Token lacks required scopes (user:write:chat, channel:bot)")
            print("  2. Bot not authorized for this channel")
            print("  3. Token expired or invalid")
            print(f"\nDelete .twitch_token and re-authorize with correct scopes")
            print(f"{'='*60}\n")
            sys.exit(1)

    async def _heartbeat(self):
        """Print periodic stats to show bot is alive."""
        while True:
            await asyncio.sleep(10)
            uptime = (datetime.now() - self.start_time).seconds
            print(f"[Heartbeat] Uptime: {uptime}s | Messages: {self.messages_received} | Votes: {self.votes_received} | Commands: {self.game_commands_received}")

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


async def run_bot(client_id, client_secret, bot_id, owner_id, channel_id, access_token, bot_username, flask_url="http://localhost:5000"):
    """
    Run the Twitch EventSub bot.

    Startup sequence:
    1. Connect to Flask (exit if fail)
    2. Fetch enabled actions (exit if fail)
    3. Connect to Twitch EventSub (exit if fail)
    4. Report readiness
    5. Announce to chat

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
    bot = SelectionBot(client_id, client_secret, bot_id, owner_id, channel_id, access_token, bot_username, flask_url)

    # Step 1: Connect to Flask (MUST succeed)
    await bot.connect_to_flask()

    # Step 2: Connect to Twitch EventSub
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

        # Run bot
        if test_mode:
            # Test mode: run for 30s then exit cleanly
            async def run_test():
                bot = SelectionBot(
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
