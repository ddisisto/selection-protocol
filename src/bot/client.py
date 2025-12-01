"""
EventSub bot client for Selection Protocol.

Routes parsed chat input from Twitch to Flask server for processing.
"""

import asyncio
import requests
import socketio
from twitchio.ext import commands
from twitchio import eventsub, eventsub_
from datetime import datetime
import sys

from .parser import parse_chat_input
from .logging import log_chat_input
from ..oauth_flow import refresh_access_token, save_token_cache


class ChatInputBot(commands.AutoBot):
    """
    TwitchIO EventSub bot that routes parsed chat input to Flask server.

    Responsibilities:
    - Parse single-char commands from chat (k/l/x, +/-/0-4)
    - Forward parsed input to server via SocketIO
    - Handle server events (round_start, round_end)
    - Send announcements to chat
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
            prefix='',  # No prefix commands used
            force_subscribe=True,  # Auto-subscribe to EventSub events
        )
        self.channel_id = channel_id
        self.start_time = datetime.now()
        self.messages_received = 0
        # Store for chat message sending and filtering
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        self._bot_username = bot_username.lower()
        self._flask_url = flask_url

        # SocketIO client (will be initialized in connect_to_flask)
        self.sio = None

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
        Connect to Flask server via SocketIO.

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

            # Register server event handlers
            self._register_server_events()

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

    async def _send_chat_message(self, message):
        """
        Send a message to Twitch chat with announcement.

        Args:
            message: Text to send to chat

        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Prefix message with announcement command
        colored_message = f"/announce {message}"

        url = "https://api.twitch.tv/helix/chat/messages"

        for attempt in range(2):  # Try once, retry once if 401
            try:
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
                # Handle 401 Unauthorized - token expired
                if e.response.status_code == 401 and attempt == 0:
                    print(f"⚠ Token expired (HTTP 401), attempting refresh...")

                    # Attempt token refresh
                    from ..oauth_flow import get_cached_token
                    cached = get_cached_token()

                    if cached and 'refresh_token' in cached:
                        new_access, new_refresh = refresh_access_token(
                            self._client_id,
                            self._client_secret,
                            cached['refresh_token']
                        )

                        if new_access:
                            # Update token and save to cache
                            self._access_token = new_access
                            save_token_cache(
                                new_access,
                                new_refresh or cached['refresh_token'],
                                cached.get('expires_in', 14400)
                            )
                            print(f"✓ Token refreshed, retrying send...")
                            continue  # Retry with new token
                        else:
                            print(f"✗ Token refresh failed")
                    else:
                        print(f"✗ No refresh token in cache")

                # Log error details
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

        # Should not reach here, but just in case
        return False

    def _register_server_events(self):
        """
        Register SocketIO event handlers for server events.

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

            message = f"Voting opened by @{username}: {vote}, {timer}s to have your say: K,L,X"
            success = await self._send_chat_message(message)

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

            success = await self._send_chat_message(message)

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
        # Extract username and message text from EventSub payload
        username = payload.chatter.name
        text = payload.text

        # Filter out bot's own messages (prevents announcement loops)
        if str(payload.chatter.id) == str(self.bot_id):
            return

        self.messages_received += 1

        # Parse chat input (CHAT_UX.md spec)
        parsed_input = parse_chat_input(text)

        # Skip if no valid input parsed
        if not parsed_input:
            return

        # Forward to server via unified chat_input event
        try:
            response = await self.sio.call('chat_input', {
                'username': username,
                'input': parsed_input,
                'timestamp': datetime.now().isoformat()
            }, timeout=5)

            # Log single consolidated line with server response
            log_chat_input(username, text, parsed_input, response)

        except Exception as e:
            # Fail-fast: let exceptions surface
            print(f"[ERROR] Failed to send chat_input: {e}")
            raise

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
        sys.exit(1)

    async def _send_startup_announcement(self):
        """Send startup message to chat."""
        # Wait a moment for EventSub to be fully ready
        await asyncio.sleep(2)

        message = "Selection Protocol online. Vote: k (kill) | l (lay) | x (extend) • Commands: +/- (zoom) | 0-4 (info panels, 0=hide)"
        success = await self._send_chat_message(message)

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
            print(f"[Heartbeat] Uptime: {uptime}s | Messages: {self.messages_received}")
