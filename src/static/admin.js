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

// Game Keypress Functions
function sendKeypress(key, cooldownGroup) {
    socket.emit('admin_send_keypress', {key: key, cooldown_group: cooldownGroup});
}

// Cooldown UI Update (server-driven)
function updateCooldownUI(cooldownState) {
    // Update primary cooldown (Kill, Lay)
    const primaryRemaining = cooldownState.primary.remaining;
    const primaryBtn = document.getElementById('btn-kill');
    const layBtn = document.getElementById('btn-lay');
    const primaryStatus = document.getElementById('primary-cooldown');

    if (cooldownState.primary.active) {
        primaryBtn.disabled = true;
        layBtn.disabled = true;
        document.getElementById('cd-kill').textContent = `CD: ${primaryRemaining}s`;
        document.getElementById('cd-kill').style.display = 'flex';
        document.getElementById('cd-lay').textContent = `CD: ${primaryRemaining}s`;
        document.getElementById('cd-lay').style.display = 'flex';
        primaryStatus.textContent = `${primaryRemaining}s`;
    } else {
        primaryBtn.disabled = false;
        layBtn.disabled = false;
        document.getElementById('cd-kill').style.display = 'none';
        document.getElementById('cd-lay').style.display = 'none';
        primaryStatus.textContent = 'Ready';
    }

    // Update extend cooldown
    const extendBtn = document.getElementById('btn-extend');
    if (cooldownState.extend.active) {
        extendBtn.disabled = true;
        document.getElementById('cd-extend').textContent = `CD: ${cooldownState.extend.remaining}s`;
        document.getElementById('cd-extend').style.display = 'flex';
    } else {
        extendBtn.disabled = false;
        document.getElementById('cd-extend').style.display = 'none';
    }

    // Update camera cooldown
    const camGenBtn = document.getElementById('btn-cam-gen');
    const camOldBtn = document.getElementById('btn-cam-old');
    const camRandBtn = document.getElementById('btn-cam-rand');
    const cameraActive = cooldownState.camera.active;

    camGenBtn.disabled = cameraActive;
    camOldBtn.disabled = cameraActive;
    camRandBtn.disabled = cameraActive;

    // Update zoom cooldowns
    const zoomInBtn = document.getElementById('btn-zoom-in');
    const zoomOutBtn = document.getElementById('btn-zoom-out');

    if (cooldownState.zoom_in.active) {
        zoomInBtn.disabled = true;
        document.getElementById('cd-zoom-in').textContent = `CD: ${cooldownState.zoom_in.remaining}s`;
        document.getElementById('cd-zoom-in').style.display = 'flex';
    } else {
        zoomInBtn.disabled = false;
        document.getElementById('cd-zoom-in').style.display = 'none';
    }

    if (cooldownState.zoom_out.active) {
        zoomOutBtn.disabled = true;
        document.getElementById('cd-zoom-out').textContent = `CD: ${cooldownState.zoom_out.remaining}s`;
        document.getElementById('cd-zoom-out').style.display = 'flex';
    } else {
        zoomOutBtn.disabled = false;
        document.getElementById('cd-zoom-out').style.display = 'none';
    }
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

// Cooldown update handler
socket.on('cooldown_update', function(cooldownState) {
    console.log('Cooldown update:', cooldownState);
    updateCooldownUI(cooldownState);
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

// Request cooldown updates every second
setInterval(() => {
    socket.emit('get_cooldown_state');
}, 1000);
