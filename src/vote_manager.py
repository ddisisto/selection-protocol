"""
Vote manager for Selection Protocol.

Tracks k/l/x votes from chat, manages first-L claimant logic,
and broadcasts state updates to overlay via SocketIO.
"""

from datetime import datetime
from math import log2
from .actions import ACTIONS, is_valid_action
from .game_controller import send_keypress


class VoteManager:
    """
    Manages vote tracking and first-L claimant logic.

    Vote rules:
    - One person, one vote (latest replaces previous)
    - First L voter gets naming claim
    - Switching away from L loses claim
    - Switching back to L = new timestamp (back of queue)
    """

    def __init__(self, socketio, log_action=None):
        """
        Initialize vote manager.

        Args:
            socketio: Flask-SocketIO instance for broadcasting
            log_action: Optional logging function for admin panel
        """
        self.socketio = socketio
        self.log_action = log_action or (lambda *args: None)

        # Vote tracking
        # Format: {username: {'vote': 'k', 'timestamp': datetime}}
        self.votes = {}

        # First-L claimant tracking
        # username of current first-L claimant, or None
        self.first_l_claimant = None
        self.first_l_timestamp = None

        # Action registry
        self.actions = ACTIONS

        # Cycle management
        self.cycle_active = False
        self.cycle_start_time = None

        # Timer system (dynamic, ratio-based)
        self.base_time = 30          # Minimum timer duration
        self.timer_limit = None      # Target time in seconds (30-120s)
        self.time_remaining = None   # Current countdown value
        self.timer_started = False   # Whether timer is running

    def cast_vote(self, username, vote, timestamp=None):
        """
        Record or update a vote from a user.

        Args:
            username: Twitch username
            vote: Vote code ('k', 'l', 'x')
            timestamp: Vote timestamp (defaults to now)

        Returns:
            bool: True if vote was recorded, False if invalid
        """
        # Validate vote
        if not is_valid_action(vote):
            return False

        timestamp = timestamp or datetime.now()
        previous_vote = self.votes.get(username, {}).get('vote')

        # Record vote
        self.votes[username] = {
            'vote': vote,
            'timestamp': timestamp
        }

        # Update first-L claimant logic
        self._update_first_l_claim(username, vote, previous_vote, timestamp)

        # Start timer on first K or L vote (X requires K/L to unlock)
        if not self.timer_started and vote in ['k', 'l']:
            self._start_timer()

        # Recalculate timer limit based on new ratios
        if self.timer_started:
            self._update_timer_limit()

        # Log the vote
        self.log_action(f"Vote: {username}", f"{vote.upper()}")

        # Broadcast updated state
        self._broadcast_state()

        return True

    def _update_first_l_claim(self, username, new_vote, previous_vote, timestamp):
        """
        Update first-L claimant based on vote change.

        Rules:
        - First L voter gets claim
        - Switching away from L loses claim
        - If current claimant switches away, find next earliest L voter
        """
        # User switched TO L
        if new_vote == 'l' and previous_vote != 'l':
            # If no current claimant, this user gets it
            if self.first_l_claimant is None:
                self.first_l_claimant = username
                self.first_l_timestamp = timestamp
                self.log_action("First-L claim", username)

        # User switched AWAY from L
        elif previous_vote == 'l' and new_vote != 'l':
            # If this user was the claimant, find new claimant
            if username == self.first_l_claimant:
                self._find_new_first_l_claimant()

    def _find_new_first_l_claimant(self):
        """
        Find the earliest L voter to become new claimant.

        Called when current claimant switches away from L.
        """
        # Find all current L voters
        l_voters = [
            (uname, data['timestamp'])
            for uname, data in self.votes.items()
            if data['vote'] == 'l'
        ]

        if l_voters:
            # Earliest L voter becomes claimant
            new_claimant, new_timestamp = min(l_voters, key=lambda x: x[1])
            self.first_l_claimant = new_claimant
            self.first_l_timestamp = new_timestamp
            self.log_action("First-L claim transferred", new_claimant)
        else:
            # No L voters left
            self.first_l_claimant = None
            self.first_l_timestamp = None
            self.log_action("First-L claim", "None (no L voters)")

    def get_vote_counts(self):
        """
        Get current vote counts for each action.

        Returns:
            dict: {action_code: count} (e.g., {'k': 5, 'l': 3, 'x': 2})
        """
        counts = {'k': 0, 'l': 0, 'x': 0}

        for vote_data in self.votes.values():
            vote = vote_data['vote']
            if vote in counts:
                counts[vote] += 1

        return counts

    def _start_timer(self):
        """
        Start the vote timer.

        Called when first K or L vote is cast.
        Initializes timer at 30s (1:0:0 ratio).
        """
        counts = self.get_vote_counts()
        self.timer_limit = self.get_timer_limit(counts['k'], counts['l'], counts['x'])
        self.time_remaining = self.timer_limit
        self.timer_started = True
        self.log_action("Timer started", f"{self.timer_limit}s")

    def _update_timer_limit(self):
        """
        Recalculate timer limit based on current vote ratios.

        Called whenever a vote changes.
        Adjusts time_remaining to match new limit.
        """
        counts = self.get_vote_counts()
        new_limit = self.get_timer_limit(counts['k'], counts['l'], counts['x'])

        if new_limit != self.timer_limit:
            old_limit = self.timer_limit
            self.timer_limit = new_limit

            # Set remaining time to new limit
            # Timer extends/contracts based on vote uncertainty
            if self.time_remaining is not None:
                self.time_remaining = new_limit

                self.log_action(
                    "Timer adjusted",
                    f"{old_limit}s → {new_limit}s (remaining: {self.time_remaining}s)"
                )

    def get_timer_limit(self, k_count, l_count, x_count):
        """
        Calculate timer limit based purely on vote distribution.

        Uses Shannon entropy to measure vote uncertainty/split:
        - Unanimous (100% one option) → 30s (certain, quick)
        - 50/50 split → ~68s (uncertain, debate)
        - Perfect 3-way split → ~100s (maximum complexity)
        - X dominant → extends further (deliberation request)

        Formula:
            time = base_time + uncertainty_bonus + x_bonus
            - uncertainty_bonus: 0-60s based on entropy (how split)
            - x_bonus: 0-60s based on X percentage (deliberation)
            - Capped at 120s maximum

        Args:
            k_count: Number of K votes
            l_count: Number of L votes
            x_count: Number of X votes

        Returns:
            int: Timer limit in seconds (30-120)
        """
        total = k_count + l_count + x_count

        if total == 0:
            return self.base_time

        # Convert to percentages
        k_pct = k_count / total
        l_pct = l_count / total
        x_pct = x_count / total

        # Calculate Shannon entropy (measures uncertainty)
        # Entropy = -Σ(p_i * log2(p_i)) for each vote type
        # Range: 0 (unanimous) to log2(3)≈1.585 (perfect 3-way split)
        entropy = 0
        for pct in [k_pct, l_pct, x_pct]:
            if pct > 0:
                entropy -= pct * log2(pct)

        # Normalize entropy to 0-1 scale
        max_possible_entropy = 1.585  # log2(3) for 3 options
        uncertainty = min(entropy / max_possible_entropy, 1.0)

        # Additive components
        uncertainty_bonus = uncertainty * 60  # How split votes are (0-60s)
        x_bonus = x_pct * 60                  # Deliberation request (0-60s)

        # Combine and cap
        total_time = self.base_time + uncertainty_bonus + x_bonus
        return min(int(total_time), 120)

    def get_vote_state(self):
        """
        Get complete vote state for broadcasting.

        Returns:
            dict: Vote state including counts, claimant, etc.
        """
        counts = self.get_vote_counts()

        return {
            'k_votes': counts['k'],
            'l_votes': counts['l'],
            'x_votes': counts['x'],
            'total_votes': len(self.votes),
            'first_l_claimant': self.first_l_claimant,
            'voting_active': self.cycle_active,
            'time_remaining': self.time_remaining,
            # Additional metadata
            'voter_count': len(self.votes),
            'timestamp': datetime.now().isoformat()
        }

    def tick(self):
        """
        Timer tick - called every second by background task.

        Decrements time_remaining and checks for expiry.
        When timer hits 0, executes winner and resets round.
        """
        if not self.timer_started or self.time_remaining is None:
            return

        self.time_remaining -= 1

        # Broadcast updated timer
        self._broadcast_state()

        # Check for expiry
        if self.time_remaining <= 0:
            self.log_action("Timer expired", "Resolving vote")
            self._execute_winner()

    def _execute_winner(self):
        """
        Execute the winning action and reset for next round.

        Called when timer expires.
        Determines winner, sends keypress if K or L, resets votes.
        """
        winner = self.get_winner()

        if winner == 'k':
            self.log_action("Winner: K", "Sending Delete keypress")
            result = send_keypress('Delete', self.log_action)
            if result['success']:
                print("✓ EXECUTED: Delete keypress (K wins)")
            else:
                print(f"✗ FAILED: Delete keypress - {result.get('error', 'Unknown error')}")
        elif winner == 'l':
            claimant = self.first_l_claimant or "Unknown"
            self.log_action("Winner: L", f"Sending Insert keypress (Claimant: {claimant})")
            result = send_keypress('Insert', self.log_action)
            if result['success']:
                print(f"✓ EXECUTED: Insert keypress (L wins, claimant: {claimant})")
            else:
                print(f"✗ FAILED: Insert keypress - {result.get('error', 'Unknown error')}")
        else:
            # X wins or tie
            self.log_action("Winner: X", "No action (extend)")
            print("→ No action (X wins)")

        # Reset for next round
        self.reset_votes()

    def reset_votes(self):
        """
        Reset all votes for a new cycle.

        Called at the start of each new voting cycle.
        Clears votes, timer state, and waits for next round to start.
        """
        self.votes.clear()
        self.first_l_claimant = None
        self.first_l_timestamp = None

        # Reset timer state (waiting for first K/L vote)
        self.timer_limit = None
        self.time_remaining = None
        self.timer_started = False

        self.log_action("Votes reset", "Awaiting next round")
        self._broadcast_state()

    def start_cycle(self):
        """Start a new voting cycle."""
        self.cycle_active = True
        self.cycle_start_time = datetime.now()
        self.reset_votes()
        self.log_action("Vote cycle started")
        self._broadcast_state()

    def end_cycle(self):
        """End current voting cycle."""
        self.cycle_active = False
        self.log_action("Vote cycle ended")
        # Don't reset votes yet - need them for resolution
        self._broadcast_state()

    def get_winner(self):
        """
        Determine winner of current vote cycle per VOTING_RULES.md.

        Rules:
        - K wins IF: K > 33% AND K > L
        - L wins IF: L > 33% AND L > K
        - X wins (no action) IF: Neither K nor L > 33%, OR K = L (tie)

        Returns:
            str: Winning action code ('k', 'l', or 'x')
        """
        counts = self.get_vote_counts()
        total = sum(counts.values())

        # No votes = X wins (no action)
        if total == 0:
            return 'x'

        k_count = counts['k']
        l_count = counts['l']

        k_percent = (k_count / total) * 100
        l_percent = (l_count / total) * 100

        # K wins: K > 33% AND K > L
        if k_percent > 33 and k_count > l_count:
            return 'k'

        # L wins: L > 33% AND L > K
        if l_percent > 33 and l_count > k_count:
            return 'l'

        # X wins: Neither K nor L > 33%, OR K = L (tie)
        return 'x'

    def get_enabled_actions(self):
        """
        Get list of currently enabled action codes.

        Returns:
            list: Action codes (e.g., ['k', 'l', 'x'])
        """
        return [code for code, action in self.actions.items() if action['enabled']]

    def _broadcast_state(self):
        """Broadcast current vote state to all connected clients."""
        state = self.get_vote_state()
        self.socketio.emit('vote_update', state)

    # ============================================================
    # ADMIN TESTING METHODS
    # ============================================================

    def add_test_vote(self, vote_type):
        """
        Add a test vote with a random username (admin panel testing).

        Args:
            vote_type: Vote code ('k', 'l', or 'x')

        Returns:
            str: Generated test username
        """
        import random
        test_username = f"test_{random.randint(100000, 999999)}"
        self.cast_vote(test_username, vote_type)
        return test_username

    def remove_last_vote(self, vote_type):
        """
        Remove the most recent vote of a specific type (admin panel testing).

        Args:
            vote_type: Vote code ('k', 'l', or 'x')

        Returns:
            bool: True if a vote was removed, False if no votes of that type
        """
        # Find all voters of this type
        voters_of_type = [
            (username, data['timestamp'])
            for username, data in self.votes.items()
            if data['vote'] == vote_type
        ]

        if not voters_of_type:
            self.log_action(f"Remove {vote_type.upper()} vote", "No votes to remove")
            return False

        # Find most recent voter
        most_recent_voter, _ = max(voters_of_type, key=lambda x: x[1])

        # Remove the vote
        del self.votes[most_recent_voter]
        self.log_action(f"Removed {vote_type.upper()} vote", most_recent_voter)

        # If it was an L vote, recalculate first-L claimant
        if vote_type == 'l' and most_recent_voter == self.first_l_claimant:
            self._find_new_first_l_claimant()

        # Recalculate timer limit
        if self.timer_started:
            self._update_timer_limit()

        # Broadcast updated state
        self._broadcast_state()

        return True

    def force_execute_action(self, action):
        """
        Force immediate execution of a specific action (admin panel testing).

        Bypasses normal vote resolution and timer.
        Executes the specified action immediately and resets for next round.

        Args:
            action: Action code ('k', 'l', or 'x')
        """
        self.log_action(f"FORCE EXECUTE: {action.upper()}", "Admin override")

        if action == 'k':
            result = send_keypress('Delete', self.log_action)
            if result['success']:
                print("✓ FORCE EXECUTED: Delete keypress (admin K)")
            else:
                print(f"✗ FAILED: Delete keypress - {result.get('error', 'Unknown error')}")
        elif action == 'l':
            claimant = self.first_l_claimant or "Unknown"
            result = send_keypress('Insert', self.log_action)
            if result['success']:
                print(f"✓ FORCE EXECUTED: Insert keypress (admin L, claimant: {claimant})")
            else:
                print(f"✗ FAILED: Insert keypress - {result.get('error', 'Unknown error')}")
        else:  # action == 'x'
            print("→ FORCE EXECUTED: No action (admin X)")

        # Reset for next round
        self.reset_votes()
