# Twitch Bot Setup Guide

Complete guide to get the TwitchIO bot running for Selection Protocol using modern OAuth.

## Prerequisites

- Python 3.10+ with venv
- A Twitch account (for the bot - can be your main account or create a separate bot account)
- Browser access to Twitch Developer Console

---

## Step 1: Register Your Application

1. Go to https://dev.twitch.tv/console/apps
2. Log in with your Twitch account
3. Click **"Register Your Application"**
4. Fill in the form:
   - **Name:** `Selection Protocol Bot` (or any name you like)
   - **OAuth Redirect URLs:** `http://localhost:3000`
   - **Category:** `Chat Bot`
5. Click **"Create"**
6. Click **"Manage"** on your new application
7. Copy your **Client ID** (you'll need this in Step 2)

---

## Step 2: Get Your OAuth Token

Run the OAuth helper script with your Client ID:

```bash
python tools/get_oauth_token.py YOUR_CLIENT_ID_HERE
```

**What this does:**
- Opens your browser to Twitch authorization page
- Shows you what permissions the bot needs (`chat:read` and `chat:edit`)
- Redirects to `localhost:3000` with the token in the URL

**After authorizing:**
1. Browser shows an error (normal - no server running on port 3000)
2. Look at the URL bar: `http://localhost:3000/#access_token=abc123xyz...&scope=...`
3. Copy the part between `access_token=` and `&scope=`
4. Save it for Step 3

---

## Step 3: Create config.yaml

Copy the example config:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your credentials:

```yaml
twitch:
  token: "oauth:YOUR_TOKEN_HERE"  # Add 'oauth:' prefix to token from Step 2!
  channel: "your_channel_name"    # Your Twitch channel (lowercase)
  nick: "your_bot_username"       # Bot username (usually same as channel)
```

**Important:**
- Token MUST have `oauth:` prefix
- Channel and nick should be lowercase
- `config.yaml` is gitignored (won't be committed)

---

## Step 4: Install Dependencies

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 5: Test Bot (Standalone)

Run the bot in test mode (no vote manager):

```bash
source .venv/bin/activate
python -m src.twitch_bot
```

**Expected output:**
```
Starting TwitchIO bot in TEST MODE (no vote manager)
Type k, l, or x in chat to test command parsing

============================================================
TwitchIO Bot Connected!
============================================================
Bot username: your_bot_username
Joined channel: #your_channel_name
Connected at: 21:45:32

Listening for commands: k (kill), l (lay), x (extend)
============================================================
```

---

## Step 6: Test Vote Commands

1. Open your Twitch channel in a browser: `https://twitch.tv/your_channel_name`
2. Type in chat: `k`, `l`, or `x`
3. Watch bot terminal for parsed votes:

```
[21:45:45] Vote from your_username: K
  → No vote manager connected (skeleton mode)
[21:45:47] Vote from viewer123: L
  → No vote manager connected (skeleton mode)
```

If you see votes logged, **the bot is working!** 🎉

---

## Bot Commands (Future Phase 4)

The bot includes skeleton commands:

- `!lineage` - Show your lineage stats
- `!stats` - Show overall voting stats

These respond with "coming soon" messages for now.

---

## Troubleshooting

### "Error: config.yaml not found!"

Make sure you:
1. Copied `config.yaml.example` to `config.yaml`
2. Filled in your token, channel, and nick
3. Running from project root directory

### "Authentication failed" or bot disconnects immediately

Your OAuth token is invalid. Possible causes:
- Forgot to add `oauth:` prefix
- Token expired (get a new one from Step 2)
- Token from wrong Twitch account

### Bot connects but doesn't respond to chat

Check:
- Channel name is lowercase in `config.yaml`
- You're typing exactly `k`, `l`, or `x` (lowercase, no spaces)
- Bot ignores its own messages (if you're testing with the bot account, use a different account to vote)

### "ModuleNotFoundError: No module named 'twitchio'"

Install dependencies:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Token expired after a few weeks

OAuth tokens expire periodically. When this happens:
1. Re-run Step 2 to get a new token
2. Update `config.yaml` with the new token
3. Restart the bot

(Future: we'll add automatic token refresh in Phase 4)

---

## Security Notes

- **Never commit config.yaml** (it's gitignored)
- **Never share your OAuth token** publicly
- **Don't stream with config.yaml visible**
- If token is compromised, regenerate it at https://dev.twitch.tv/console

---

## Next Steps

Once the bot is working standalone:
- **Commit 7:** Integrate with vote manager
- **Commit 8:** Add vote display to overlay
- **Commit 9:** Full end-to-end testing

The bot skeleton is complete and ready for integration!
