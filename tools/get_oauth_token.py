#!/usr/bin/env python3
"""
OAuth Token Generator for Selection Protocol Twitch Bot

Simple helper to generate the OAuth authorization URL.
Opens browser for you to authorize, then you copy the token from the redirect URL.
"""

import webbrowser
import sys


def generate_auth_url(client_id):
    """Generate OAuth authorization URL for Twitch IRC bot."""

    # Twitch OAuth endpoint
    base_url = "https://id.twitch.tv/oauth2/authorize"

    # Parameters for implicit grant flow (no server needed)
    params = {
        "client_id": client_id,
        "redirect_uri": "http://localhost:3000",
        "response_type": "token",
        "scope": "chat:read chat:edit",  # Read and send messages
    }

    # Build URL
    param_string = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{base_url}?{param_string}"

    return auth_url


def main():
    print("=" * 70)
    print("Selection Protocol - Twitch OAuth Token Generator")
    print("=" * 70)
    print()

    # Check if client_id provided
    if len(sys.argv) < 2:
        print("Usage: python tools/get_oauth_token.py <your_client_id>")
        print()
        print("Steps to get your Client ID:")
        print("  1. Go to https://dev.twitch.tv/console/apps")
        print("  2. Click 'Register Your Application'")
        print("  3. Name: 'Selection Protocol Bot' (or anything)")
        print("  4. OAuth Redirect URL: http://localhost:3000")
        print("  5. Category: Chat Bot")
        print("  6. Click 'Create'")
        print("  7. Copy your Client ID and run this script again")
        print()
        print("Example:")
        print("  python tools/get_oauth_token.py abc123def456...")
        sys.exit(1)

    client_id = sys.argv[1]

    print("Generating OAuth URL...")
    auth_url = generate_auth_url(client_id)

    print()
    print("Step 1: Opening browser to authorize bot...")
    print("        (If browser doesn't open, copy this URL manually)")
    print()
    print(auth_url)
    print()

    # Try to open browser
    try:
        webbrowser.open(auth_url)
        print("✓ Browser opened")
    except:
        print("✗ Could not open browser automatically")
        print("  Please copy the URL above and open it manually")

    print()
    print("=" * 70)
    print("Step 2: After authorizing in browser...")
    print("=" * 70)
    print()
    print("1. You'll be redirected to: http://localhost:3000/#access_token=...")
    print("2. Your browser will show an error (that's normal - no server running)")
    print("3. Look at the URL bar and copy the part AFTER 'access_token='")
    print("4. Copy everything BEFORE '&scope=' (the token is ~30 chars)")
    print()
    print("Example URL:")
    print("  http://localhost:3000/#access_token=abc123xyz789...&scope=chat:read")
    print("                                      ^^^^^^^^^^^^^")
    print("                                      Copy this part")
    print()
    print("5. Save your token to config.yaml:")
    print()
    print("   twitch:")
    print("     token: 'oauth:abc123xyz789...'  # Add 'oauth:' prefix!")
    print("     channel: 'your_channel_name'")
    print("     nick: 'your_bot_username'")
    print()
    print("=" * 70)
    print("Done! Once config.yaml is set up, test with:")
    print("  python -m src.twitch_bot")
    print("=" * 70)


if __name__ == '__main__':
    main()
