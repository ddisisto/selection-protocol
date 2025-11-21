"""
Vote manager for Selection Protocol.

Tracks k/l/x votes from chat, manages first-L claimant logic,
and broadcasts state updates to overlay via SocketIO.
"""

from datetime import datetime
from .actions import ACTIONS, is_valid_action


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
            # Additional metadata
            'voter_count': len(self.votes),
            'timestamp': datetime.now().isoformat()
        }

    def reset_votes(self):
        """
        Reset all votes for a new cycle.

        Called at the start of each new voting cycle.
        """
        self.votes.clear()
        self.first_l_claimant = None
        self.first_l_timestamp = None
        self.log_action("Votes reset", "New cycle")
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
        Determine winner of current vote cycle.

        Returns:
            str: Winning action code ('k', 'l', 'x', or None for tie/no votes)
        """
        counts = self.get_vote_counts()

        # No votes = default to extend
        if sum(counts.values()) == 0:
            return 'x'

        # Find max count
        max_count = max(counts.values())

        # Check for tie
        winners = [action for action, count in counts.items() if count == max_count]

        if len(winners) > 1:
            return None  # Tie
        else:
            return winners[0]

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
