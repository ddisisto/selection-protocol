/**
 * Overlay rendering functions - Server-authoritative state
 *
 * All state comes from server via SocketIO vote_update events.
 * Zero client-side timers or vote counters.
 */

// Canvas setup
const canvas = document.getElementById('pieChart');
const ctx = canvas.getContext('2d');

/**
 * Get timer color based on remaining seconds
 * Green → Yellow → Red gradient as time runs out
 */
function getTimerColor(seconds) {
    if (seconds >= 16) {
        return '#00ff88'; // Green
    } else if (seconds >= 1) {
        // Linear gradient from green → yellow → red
        // Green: hsl(158, 100%, 50%)
        // Red: hsl(0, 100%, 50%)
        const progress = (15 - seconds) / 14; // 0 to 1 as time decreases from 15 to 1
        const hue = 158 - (158 * progress); // 158 → 0
        return `hsl(${hue}, 100%, 50%)`;
    } else {
        return '#ff0000'; // Bright red at 0
    }
}

/**
 * Get pie chart border color based on winning vote
 * Returns color of leader, or green for tie/no votes
 */
function getBorderColor(kVotes, lVotes, xVotes) {
    const total = kVotes + lVotes + xVotes;
    if (total === 0) {
        return '#00ff88'; // Green when no votes
    }

    // Find which vote is winning
    const max = Math.max(kVotes, lVotes, xVotes);

    // Check for tie
    const winners = [
        kVotes === max ? 'k' : null,
        lVotes === max ? 'l' : null,
        xVotes === max ? 'x' : null
    ].filter(v => v !== null);

    if (winners.length > 1) {
        return '#00ff88'; // Green when tied
    }

    // Color based on winner
    if (kVotes === max) return '#ff6666'; // Red for K
    if (lVotes === max) return '#6666ff'; // Blue for L
    if (xVotes === max) return '#00ff88'; // Green for X
}

/**
 * Draw 3-way pie chart (K, L, X)
 * Order: L (blue), X (green), K (red) clockwise from 12 o'clock
 */
function drawPieChart(kVotes, lVotes, xVotes) {
    const total = kVotes + lVotes + xVotes;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 60;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (total === 0) {
        // Draw empty circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.fillStyle = '#333333';
        ctx.fill();
        return;
    }

    // Calculate angles (clockwise from 12 o'clock: L, X, K)
    const lAngle = (lVotes / total) * 2 * Math.PI;
    const xAngle = (xVotes / total) * 2 * Math.PI;
    const kAngle = (kVotes / total) * 2 * Math.PI;

    let currentAngle = -Math.PI / 2; // Start at 12 o'clock

    // Draw L slice (blue)
    if (lVotes > 0) {
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + lAngle);
        ctx.closePath();
        ctx.fillStyle = '#6666ff';
        ctx.fill();
        currentAngle += lAngle;
    }

    // Draw X slice (green)
    if (xVotes > 0) {
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + xAngle);
        ctx.closePath();
        ctx.fillStyle = '#00ff88';
        ctx.fill();
        currentAngle += xAngle;
    }

    // Draw K slice (red)
    if (kVotes > 0) {
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + kAngle);
        ctx.closePath();
        ctx.fillStyle = '#ff6666';
        ctx.fill();
    }

    // Update border color based on votes
    canvas.style.borderColor = getBorderColor(kVotes, lVotes, xVotes);
}

/**
 * Handle vote updates from server
 * Renders current state - no client-side state tracking
 */
socket.on('vote_update', function(data) {
    console.log('Vote update:', data);

    // Update vote counts
    const kCountEl = document.getElementById('k-count');
    const lCountEl = document.getElementById('l-count');
    const xCountEl = document.getElementById('x-count');

    // Trigger animation if value changed (CSS-based, stateless)
    if (kCountEl && kCountEl.textContent !== String(data.k_votes)) {
        kCountEl.classList.remove('animate');
        void kCountEl.offsetWidth; // Force reflow
        kCountEl.classList.add('animate');
    }
    if (lCountEl && lCountEl.textContent !== String(data.l_votes)) {
        lCountEl.classList.remove('animate');
        void lCountEl.offsetWidth; // Force reflow
        lCountEl.classList.add('animate');
    }
    if (xCountEl && xCountEl.textContent !== String(data.x_votes)) {
        xCountEl.classList.remove('animate');
        void xCountEl.offsetWidth; // Force reflow
        xCountEl.classList.add('animate');
    }

    kCountEl.textContent = data.k_votes;
    lCountEl.textContent = data.l_votes;
    xCountEl.textContent = data.x_votes;

    // Update first-L claimant
    const claimantEl = document.getElementById('l-claimant');
    if (claimantEl) {
        claimantEl.textContent = data.first_l_claimant || '';
    }

    // Update pie chart
    drawPieChart(data.k_votes, data.l_votes, data.x_votes);

    // Update timer from SERVER (not local countdown)
    const timerEl = document.getElementById('time-remaining');
    if (timerEl && data.time_remaining !== undefined) {
        timerEl.textContent = data.time_remaining + 's';
        timerEl.style.color = getTimerColor(data.time_remaining);
        timerEl.style.textShadow = `0 0 20px ${getTimerColor(data.time_remaining)}80`;
    }

    // Update status
    const statusEl = document.getElementById('status');
    if (statusEl) {
        if (data.voting_active) {
            statusEl.textContent = 'Chat decides fate (NOT YET LIVE). Features coming: KILL, REPRODUCE, change target, zoom, change/show/hide info overlay panels';
        } else {
            statusEl.textContent = 'Waiting for next vote...';
        }
    }
});

// Initial draw
drawPieChart(0, 0, 0);
