/**
 * Admin panel functions - Command handlers and state display
 *
 * Sends commands to server, receives and displays state updates.
 * No local state - server is authoritative.
 */

// Vote Testing Functions
function adminAddVote(voteType) {
    socket.emit('admin_add_vote', {vote_type: voteType});
}

function adminRemoveVote(voteType) {
    socket.emit('admin_remove_vote', {vote_type: voteType});
}

function adminForceExecute(action) {
    socket.emit('admin_force_execute', {action: action});
}

// Timer Controls
function adminPauseTimer() {
    socket.emit('admin_pause_timer');
}

function adminResumeTimer() {
    socket.emit('admin_resume_timer');
}

function adminResetTimer() {
    socket.emit('admin_reset_timer', {duration: 30});
}

// Game Keypress Functions (direct, no cooldowns)
function sendKeypress(key) {
    socket.emit('admin_send_keypress', {key: key});
}

// Admin state update handler
socket.on('admin_state_update', function(data) {
    console.log('Admin state update:', data);

    // Update admin panel displays
    if (data.last_action_time) {
        document.getElementById('last-action-display').textContent =
            `${data.last_action} @ ${data.last_action_time}`;
    }
    if (data.camera_mode) {
        document.getElementById('camera-mode').textContent = data.camera_mode;
    }
    if (data.connected_clients !== undefined) {
        document.getElementById('client-count').textContent = data.connected_clients;
    }
});

// Keypress result handler
socket.on('keypress_result', function(data) {
    console.log('Keypress result:', data);
    if (data.success) {
        console.log(`Keypress ${data.key} succeeded`);
    } else {
        console.error('Keypress failed:', data.error);
    }
});

// Vote update handler (from vote_manager)
socket.on('vote_update', function(data) {
    console.log('Vote update:', data);

    // Update admin panel vote counts
    const kCountEl = document.getElementById('admin-k-count');
    const lCountEl = document.getElementById('admin-l-count');
    const xCountEl = document.getElementById('admin-x-count');
    const timerEl = document.getElementById('admin-timer');
    const firstLEl = document.getElementById('admin-first-l');

    if (kCountEl) kCountEl.textContent = data.k_votes;
    if (lCountEl) lCountEl.textContent = data.l_votes;
    if (xCountEl) xCountEl.textContent = data.x_votes;
    if (timerEl && data.time_remaining !== null) {
        timerEl.textContent = data.time_remaining + 's';
    }
    if (firstLEl) {
        firstLEl.textContent = data.first_l_claimant || '—';
    }
});
