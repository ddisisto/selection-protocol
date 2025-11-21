"""
HTML/CSS/JS template for the overlay and admin panel.

This module contains the complete web interface served to clients.
Includes both the OBS overlay (right side) and admin control panel (left side).
"""

OVERLAY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Selection Protocol - Overlay + Admin</title>
    <meta charset="utf-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #000000;
            font-family: monospace, 'Arial', sans-serif;
            color: white;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: row;
        }

        /* Admin Panel - Left Side */
        .admin-panel {
            width: 300px;
            height: 100vh;
            background: #1a1a1a;
            border-right: 3px solid #00ff88;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            flex-shrink: 0;
        }

        .admin-section {
            border-bottom: 1px solid #333;
            padding: 15px;
        }

        .admin-section-title {
            font-size: 14px;
            font-weight: bold;
            color: #00ff88;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            border-bottom: 1px solid #00ff88;
            padding-bottom: 5px;
        }

        .admin-btn {
            width: 100%;
            padding: 12px;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: bold;
            border: 2px solid;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            color: white;
            background: #333;
            position: relative;
        }

        .admin-btn:hover:not(:disabled) {
            transform: scale(1.02);
            filter: brightness(1.2);
        }

        .admin-btn:active:not(:disabled) {
            transform: scale(0.98);
        }

        .admin-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            background: #222;
        }

        .cooldown-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            color: #ff6666;
            pointer-events: none;
        }

        .admin-btn.kill {
            background: #cc0000;
            border-color: #ff3333;
        }

        .admin-btn.lay {
            background: #0033cc;
            border-color: #3366ff;
        }

        .admin-btn.extend {
            background: #ccaa00;
            border-color: #ffdd33;
            color: #000;
        }

        .admin-btn.camera {
            background: #555;
            border-color: #888;
            font-size: 12px;
            padding: 10px;
        }

        .admin-btn.small {
            padding: 8px;
            font-size: 12px;
        }

        .vote-controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 10px;
        }

        .vote-display {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #2a2a2a;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 8px;
        }

        .vote-label {
            font-weight: bold;
            color: #aaa;
        }

        .vote-count {
            font-size: 20px;
            font-weight: bold;
        }

        .vote-count.k {
            color: #ff6666;
        }

        .vote-count.l {
            color: #6666ff;
        }

        .timer-controls {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
        }

        .timer-controls .admin-btn {
            margin-bottom: 0;
        }

        .status-line {
            display: flex;
            justify-content: space-between;
            background: #2a2a2a;
            padding: 8px 10px;
            border-radius: 4px;
            margin-bottom: 6px;
            font-size: 12px;
        }

        .status-label {
            color: #888;
        }

        .status-value {
            color: #fff;
            font-weight: bold;
        }

        .status-value.connected {
            color: #00ff88;
        }

        .status-value.disconnected {
            color: #ff3333;
        }

        input[type="number"] {
            width: 100%;
            padding: 8px;
            background: #2a2a2a;
            border: 1px solid #555;
            border-radius: 4px;
            color: white;
            font-size: 14px;
            margin-bottom: 8px;
        }

        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin-right: 8px;
            cursor: pointer;
        }

        .checkbox-row {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            cursor: pointer;
            padding: 6px;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .checkbox-row:hover {
            background: #2a2a2a;
        }

        .log-container {
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 8px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 11px;
            font-family: monospace;
        }

        .log-entry {
            margin-bottom: 4px;
            color: #aaa;
        }

        .log-entry:first-child {
            color: #00ff88;
        }

        /* Overlay Container - Right Side */
        .overlay-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #000000;
        }

        .title {
            display: flex;
            align-items: flex-end;
            justify-content: center;
            font-size: 24px;
            font-weight: 900;
            height: 120px;
            padding: 0 40px 12px 40px;
            color: white;
            background: #808080;
            text-transform: uppercase;
            letter-spacing: 8px;
        }

        .overlay-container {
            margin-top: auto;
            background: #000000;
            border: none;
            border-radius: 15px;
            padding: 20px 25px;
            margin-left: 20px;
            margin-right: 20px;
            margin-bottom: 20px;
        }

        .main-layout {
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 25px;
            align-items: center;
        }

        .pie-chart-container {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        canvas {
            max-width: 140px;
            max-height: 140px;
            border: 3px solid #00ff88;
            border-radius: 50%;
            transition: border-color 0.3s ease;
        }

        .right-section {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .timer-display {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            font-size: 54px;
            font-weight: bold;
            color: #00ff88;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
            line-height: 1;
            pointer-events: none;
            z-index: 10;
        }

        .votes-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .vote-item {
            background: #000000;
            border-radius: 8px;
            padding: 12px;
            border: 2px solid transparent;
            transition: border-color 0.3s ease;
        }

        .vote-item.k {
            border-color: #ff6666;
        }

        .vote-item.i {
            border-color: #6666ff;
        }

        .vote-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .vote-label {
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .vote-label.k {
            color: #ff9999;
        }

        .vote-label.i {
            color: #9999ff;
        }

        .vote-number {
            font-size: 36px;
            font-weight: bold;
            position: relative;
            display: inline-block;
        }

        .vote-number.k {
            color: #ff9999;
        }

        .vote-number.i {
            color: #9999ff;
        }

        @keyframes vote-increment {
            0% {
                transform: scale(1);
                filter: brightness(1);
            }
            50% {
                transform: scale(1.2);
                filter: brightness(1.5);
            }
            100% {
                transform: scale(1);
                filter: brightness(1);
            }
        }

        .vote-number.animate {
            animation: vote-increment 0.4s ease;
        }

        .vote-bar-container {
            height: 12px;
            background: #333333;
            border-radius: 6px;
            overflow: hidden;
        }

        .vote-bar {
            height: 100%;
            transition: width 0.4s ease;
            border-radius: 6px;
        }

        .vote-bar.k {
            background: linear-gradient(90deg, #ff6666, #ff9999);
        }

        .vote-bar.i {
            background: linear-gradient(90deg, #6666ff, #9999ff);
        }

        .status {
            text-align: center;
            font-size: 18px;
            color: white;
            background: #333333;
            text-shadow: 2px 2px 4px #00FFFF;
            margin-top: 10px;
            font-style: italic;
        }
    </style>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <!-- Admin Panel - Left Side -->
    <div class="admin-panel">
        <!-- Game Actions -->
        <div class="admin-section">
            <div class="admin-section-title">Game Actions (15s shared)</div>
            <button class="admin-btn kill" id="btn-kill" onclick="sendKeypress('Delete', 'primary')">
                [Delete] KILL
                <span class="cooldown-overlay" id="cd-kill" style="display: none;"></span>
            </button>
            <button class="admin-btn lay" id="btn-lay" onclick="sendKeypress('Insert', 'primary')">
                [Ins] LAY
                <span class="cooldown-overlay" id="cd-lay" style="display: none;"></span>
            </button>
            <button class="admin-btn extend" id="btn-extend" onclick="sendKeypress('x', 'extend')">
                [x] EXTEND (30s)
                <span class="cooldown-overlay" id="cd-extend" style="display: none;"></span>
            </button>
            <div class="status-line">
                <span class="status-label">Cooldown:</span>
                <span class="status-value" id="primary-cooldown">Ready</span>
            </div>
        </div>

        <!-- Camera Controls -->
        <div class="admin-section">
            <div class="admin-section-title">Camera (10s shared)</div>
            <button class="admin-btn camera" id="btn-cam-gen" onclick="sendKeypress('ctrl+g', 'camera')">[Ctrl+G] Generation</button>
            <button class="admin-btn camera" id="btn-cam-old" onclick="sendKeypress('ctrl+o', 'camera')">[Ctrl+O] Oldest</button>
            <button class="admin-btn camera" id="btn-cam-rand" onclick="sendKeypress('ctrl+r', 'camera')">[Ctrl+R] Random</button>
            <div class="status-line">
                <span class="status-label">Mode:</span>
                <span class="status-value" id="camera-mode">Unknown</span>
            </div>
        </div>

        <!-- Zoom Controls -->
        <div class="admin-section">
            <div class="admin-section-title">Zoom (5s individual)</div>
            <button class="admin-btn camera" id="btn-zoom-in" onclick="sendKeypress('KP_Add', 'zoom_in')">
                [KP+] Zoom In
                <span class="cooldown-overlay" id="cd-zoom-in" style="display: none;"></span>
            </button>
            <button class="admin-btn camera" id="btn-zoom-out" onclick="sendKeypress('KP_Subtract', 'zoom_out')">
                [KP-] Zoom Out
                <span class="cooldown-overlay" id="cd-zoom-out" style="display: none;"></span>
            </button>
        </div>

        <!-- Timer Controls -->
        <div class="admin-section">
            <div class="admin-section-title">Timer (demo/testing)</div>
            <div class="vote-display">
                <span class="vote-label">Time:</span>
                <span class="vote-count" id="admin-timer">30s</span>
            </div>
            <div class="timer-controls">
                <button class="admin-btn small" onclick="adminPauseTimer()">Pause</button>
                <button class="admin-btn small" onclick="adminResumeTimer()">Resume</button>
            </div>
            <button class="admin-btn" onclick="adminResetTimer()">Reset</button>
        </div>

        <!-- System Status -->
        <div class="admin-section">
            <div class="admin-section-title">Status</div>
            <div class="status-line">
                <span class="status-label">Clients:</span>
                <span class="status-value connected" id="client-count">0</span>
            </div>
            <div class="status-line">
                <span class="status-label">Last:</span>
                <span class="status-value" id="last-action-display">None</span>
            </div>
        </div>
    </div>

    <!-- Overlay Wrapper - Right Side (visible in OBS) -->
    <div class="overlay-wrapper">
        <div class="title">SELECTION PROTOCOL</div>

        <div class="overlay-container">
            <div class="main-layout">
                <div class="pie-chart-container">
                    <canvas id="pieChart" width="140" height="140"></canvas>
                    <div class="timer-display" id="time-remaining">30s</div>
                </div>

                <div class="right-section">
                    <div class="votes-container">
                        <div class="vote-item k">
                            <div class="vote-header">
                                <span class="vote-label k">K: Kill</span>
                                <span class="vote-number k" id="k-count">0</span>
                            </div>
                            <div class="vote-bar-container">
                                <div class="vote-bar k" id="k-bar" style="width: 50%"></div>
                            </div>
                        </div>

                        <div class="vote-item l">
                            <div class="vote-header">
                                <span class="vote-label l">L: Lay</span>
                                <span class="vote-number l" id="l-count">0</span>
                            </div>
                            <div class="vote-bar-container">
                                <div class="vote-bar l" id="l-bar" style="width: 50%"></div>
                            </div>
                        </div>
                    </div>

                    <div class="status" id="status">Waiting for votes...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        const canvas = document.getElementById('pieChart');
        const ctx = canvas.getContext('2d');
        let currentTime = 30;

        // Countdown timer
        setInterval(() => {
            currentTime--;
            if (currentTime < 0) {
                currentTime = 30; // Reset to 30 when it hits 0
            }
            updateTimerDisplay();
        }, 1000);

        function getTimerColor(seconds) {
            if (seconds >= 16) {
                return '#00ff88'; // Green
            } else if (seconds >= 1) {
                // Linear gradient from green → yellow → red
                // Convert to HSL for smooth interpolation
                // Green: hsl(158, 100%, 50%)
                // Red: hsl(0, 100%, 50%)
                const progress = (15 - seconds) / 14; // 0 to 1 as time decreases from 15 to 1
                const hue = 158 - (158 * progress); // 158 → 0
                return `hsl(${hue}, 100%, 50%)`;
            } else {
                return '#ff0000'; // Bright red at 0
            }
        }

        function updateTimerDisplay() {
            const timerEl = document.getElementById('time-remaining');
            timerEl.textContent = currentTime + 's';
            timerEl.style.color = getTimerColor(currentTime);
            timerEl.style.textShadow = `0 0 20px ${getTimerColor(currentTime)}80`;
        }

        function getBorderColor(kVotes, iVotes) {
            const total = kVotes + iVotes;
            if (total === 0) {
                return '#00ff88'; // Green when no votes
            }

            const kRatio = kVotes / total;
            const iRatio = iVotes / total;

            if (Math.abs(kRatio - iRatio) < 0.01) {
                return '#00ff88'; // Green when tied
            }

            // Interpolate between green and red/blue based on vote ratio
            if (kRatio > iRatio) {
                // K is winning, trend toward red
                const redWeight = (kRatio - 0.5) * 2; // 0 to 1 as K dominates
                const r = Math.round(0 + redWeight * 255);
                const g = Math.round(255 - redWeight * 153);
                const b = Math.round(136 - redWeight * 34);
                return `rgb(${r}, ${g}, ${b})`;
            } else {
                // I is winning, trend toward blue
                const blueWeight = (iRatio - 0.5) * 2; // 0 to 1 as I dominates
                const r = Math.round(0 + blueWeight * 102);
                const g = Math.round(255 - blueWeight * 153);
                const b = Math.round(136 + blueWeight * 119);
                return `rgb(${r}, ${g}, ${b})`;
            }
        }

        function updateCanvasBorder(kVotes, iVotes) {
            canvas.style.borderColor = getBorderColor(kVotes, iVotes);
        }

        function drawPieChart(kVotes, iVotes) {
            const total = kVotes + iVotes;
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

            const kAngle = (kVotes / total) * 2 * Math.PI;
            const iAngle = (iVotes / total) * 2 * Math.PI;

            // Draw K slice (red)
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + kAngle);
            ctx.closePath();
            ctx.fillStyle = '#ff6666';
            ctx.fill();

            // Draw I slice (blue)
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, -Math.PI / 2 + kAngle, -Math.PI / 2 + kAngle + iAngle);
            ctx.closePath();
            ctx.fillStyle = '#6666ff';
            ctx.fill();

            // Update border color based on votes
            updateCanvasBorder(kVotes, iVotes);
        }

        socket.on('connect', function() {
            console.log('Connected to overlay server');
        });

        let lastKVotes = 0;
        let lastLVotes = 0;

        socket.on('vote_update', function(data) {
            console.log('Vote update:', data);

            // Update vote counts with animation
            const kCountEl = document.getElementById('k-count');
            const lCountEl = document.getElementById('l-count');

            if (data.k_votes !== lastKVotes) {
                kCountEl.classList.remove('animate');
                void kCountEl.offsetWidth; // Force reflow
                kCountEl.classList.add('animate');
                lastKVotes = data.k_votes;
            }

            if (data.l_votes !== lastLVotes) {
                lCountEl.classList.remove('animate');
                void lCountEl.offsetWidth; // Force reflow
                lCountEl.classList.add('animate');
                lastLVotes = data.l_votes;
            }

            kCountEl.textContent = data.k_votes;
            lCountEl.textContent = data.l_votes;

            // Calculate percentages
            const total = data.k_votes + data.l_votes;
            let kPercent = 50;
            let lPercent = 50;

            if (total > 0) {
                kPercent = (data.k_votes / total) * 100;
                lPercent = (data.l_votes / total) * 100;
            }

            // Update bars
            document.getElementById('k-bar').style.width = kPercent + '%';
            document.getElementById('l-bar').style.width = lPercent + '%';

            // Update pie chart
            drawPieChart(data.k_votes, data.l_votes);

            // Update timer
            document.getElementById('time-remaining').textContent = data.time_remaining + 's';

            // Update status
            const statusEl = document.getElementById('status');
            if (data.voting_active) {
                statusEl.textContent = 'Chat decides fate (NOT YET LIVE). Features coming: KILL, REPRODUCE, change target, zoom, change/show/hide info overlay panels';
            } else {
                statusEl.textContent = 'Waiting for next vote...';
            }
        });

        // Initial draw
        drawPieChart(0, 0);
        updateTimerDisplay();

        // Cooldown tracking
        let cooldownIntervals = {};

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

        // Game Keypress Functions with Cooldown Check
        function sendKeypress(key, cooldownGroup) {
            socket.emit('admin_send_keypress', {key: key, cooldown_group: cooldownGroup});
        }

        // Cooldown UI Update
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

        // Request cooldown updates every second
        setInterval(() => {
            socket.emit('get_cooldown_state');
        }, 1000);
    </script>
</body>
</html>
"""
