#!/usr/bin/env python3
"""
OAuth authorization code flow for Twitch user access tokens.

Handles the full flow:
1. Check for cached token in .twitch_token
2. If not found, start local server and open browser for authorization
3. Exchange code for access + refresh tokens
4. Cache tokens for future use
5. Refresh token when expired
"""

import json
import requests
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to receive OAuth callback from Twitch."""

    auth_code = None

    def do_GET(self):
        """Handle GET request from Twitch redirect."""
        # Parse query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)

        # Check if we got an authorization code
        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Complete</title></head>
                <body style="font-family: Arial; text-align: center; margin-top: 100px;">
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to your terminal.</p>
                </body>
                </html>
            """)
        else:
            # Authorization failed
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: Arial; text-align: center; margin-top: 100px;">
                    <h1>Authorization Failed</h1>
                    <p>No authorization code received. Please try again.</p>
                </body>
                </html>
            """)

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def get_cached_token(cache_file='.twitch_token'):
    """
    Load cached token from file.

    Returns:
        dict with 'access_token' and 'refresh_token' if valid, None otherwise
    """
    cache_path = Path(cache_file)
    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        # Check if token exists
        if 'access_token' in data and 'refresh_token' in data:
            return data
    except (json.JSONDecodeError, KeyError):
        pass

    return None


def save_token_cache(access_token, refresh_token, expires_in, cache_file='.twitch_token'):
    """Save tokens to cache file."""
    cache_path = Path(cache_file)

    data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expires_in,
        'cached_at': time.time()
    }

    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Tokens cached to {cache_file}")


def refresh_access_token(client_id, client_secret, refresh_token):
    """
    Refresh an expired access token.

    Returns:
        New access token string, or None if refresh failed
    """
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        data = response.json()

        return data['access_token'], data.get('refresh_token', refresh_token)
    except Exception as e:
        print(f"✗ Token refresh failed: {e}")
        return None, None


def get_user_access_token(client_id, client_secret, scopes=['chat:read', 'chat:edit', 'user:read:chat', 'user:write:chat', 'user:bot', 'channel:bot'], port=3000):
    """
    Get user access token via authorization code flow.

    Opens browser for user to authorize, starts local server to receive callback.

    Args:
        client_id: Application client ID
        client_secret: Application client secret
        scopes: List of OAuth scopes to request
        port: Local server port for OAuth callback

    Returns:
        Tuple of (access_token, refresh_token)
    """
    redirect_uri = f"http://localhost:{port}"
    scope_str = " ".join(scopes)

    # Build authorization URL
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope_str}"
    )

    print(f"\n{'='*70}")
    print(f"TWITCH AUTHORIZATION REQUIRED")
    print(f"{'='*70}")
    print(f"\nOpening browser for authorization...")
    print(f"If browser doesn't open, visit this URL:\n")
    print(f"  {auth_url}\n")
    print(f"Waiting for authorization...")
    print(f"{'='*70}\n")

    # Start local HTTP server
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)

    # Open browser
    try:
        webbrowser.open(auth_url)
    except:
        print(f"✗ Could not open browser automatically")
        print(f"  Please visit the URL above manually")

    # Wait for callback (with timeout)
    server.timeout = 0.5  # Check every 0.5s
    timeout = 120  # 2 minute timeout
    start_time = time.time()

    while OAuthCallbackHandler.auth_code is None:
        server.handle_request()
        if time.time() - start_time > timeout:
            print(f"\n✗ Authorization timeout (2 minutes)")
            print(f"  Please try again")
            return None, None

    auth_code = OAuthCallbackHandler.auth_code
    print(f"✓ Authorization code received")

    # Exchange code for access token
    token_url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }

    try:
        response = requests.post(token_url, params=params)
        response.raise_for_status()
        data = response.json()

        access_token = data['access_token']
        refresh_token = data['refresh_token']
        expires_in = data['expires_in']

        print(f"✓ Access token obtained")

        # Cache the tokens
        save_token_cache(access_token, refresh_token, expires_in)

        return access_token, refresh_token

    except Exception as e:
        print(f"✗ Failed to exchange code for token: {e}")
        return None, None


def get_token(client_id, client_secret, cache_file='.twitch_token'):
    """
    Get a valid user access token (from cache or new authorization).

    Handles:
    - Loading from cache
    - Refreshing expired tokens
    - Full OAuth flow if needed

    Returns:
        Access token string, or None if failed
    """
    # Try cached token first
    cached = get_cached_token(cache_file)
    if cached:
        print(f"✓ Found cached token")

        # Check if token might be expired (rough check)
        age = time.time() - cached.get('cached_at', 0)
        expires_in = cached.get('expires_in', 0)

        if age < expires_in - 300:  # Valid for at least 5 more minutes
            print(f"✓ Cached token still valid")
            return cached['access_token']
        else:
            # Try to refresh
            print(f"Token expired, attempting refresh...")
            new_access, new_refresh = refresh_access_token(
                client_id,
                client_secret,
                cached['refresh_token']
            )

            if new_access:
                save_token_cache(new_access, new_refresh, expires_in, cache_file)
                return new_access

    # No cached token or refresh failed - do full OAuth flow
    print(f"No valid cached token, starting OAuth flow...")
    access_token, refresh_token = get_user_access_token(client_id, client_secret)

    return access_token


if __name__ == '__main__':
    """Test OAuth flow."""
    import yaml
    from pathlib import Path

    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)

    twitch_config = config['twitch']

    token = get_token(twitch_config['client_id'], twitch_config['client_secret'])

    if token:
        print(f"\n{'='*70}")
        print(f"SUCCESS!")
        print(f"{'='*70}")
        print(f"Access token: {token[:20]}...")
        print(f"Token cached for future use")
    else:
        print(f"\n✗ Failed to get access token")
