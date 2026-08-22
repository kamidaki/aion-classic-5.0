pub const HTML_DASHBOARD: &str = r#"<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aion Classic — Auto-Start EmuRust Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #090d16;
            --bg-card: rgba(18, 24, 38, 0.85);
            --bg-card-hover: rgba(26, 35, 56, 0.95);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(59, 130, 246, 0.2);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --accent-purple: #a855f7;
            --login-color: #f1f5f9;
            --game-color: #34d399;
            --chat-color: #38bdf8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at top right, #131d38, #090d16 60%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        /* Top Navbar */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 32px;
            background: rgba(9, 13, 22, 0.8);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-glass);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 20px;
            box-shadow: 0 4px 16px rgba(56, 189, 248, 0.3);
        }

        .logo-title {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .logo-subtitle {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 400;
        }

        .master-controls {
            display: flex;
            gap: 12px;
        }

        button {
            font-family: 'Outfit', sans-serif;
            font-size: 13px;
            font-weight: 600;
            padding: 8px 18px;
            border-radius: 8px;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-start {
            background: linear-gradient(135deg, #059669, #10b981);
            color: #fff;
            box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25);
        }
        .btn-start:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
        }

        .btn-stop {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #fca5a5;
        }
        .btn-stop:hover {
            background: rgba(239, 68, 68, 0.25);
            transform: translateY(-1px);
        }

        .btn-restart {
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.4);
            color: #7dd3fc;
        }
        .btn-restart:hover {
            background: rgba(56, 189, 248, 0.25);
            transform: translateY(-1px);
        }

        /* Container Layout */
        main {
            flex: 1;
            padding: 28px 32px;
            display: flex;
            flex-direction: column;
            gap: 28px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }

        /* 3 Cards Grid */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 22px;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 16px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.5), transparent);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title-box {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-red);
            box-shadow: 0 0 10px var(--accent-red);
            transition: all 0.3s ease;
        }

        .status-dot.online {
            background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
        }

        .status-dot.crashed {
            background: var(--accent-yellow);
            box-shadow: 0 0 10px var(--accent-yellow);
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            letter-spacing: -0.3px;
        }

        .card-tag {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Metrics */
        .metrics-box {
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: rgba(0, 0, 0, 0.2);
            padding: 14px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }

        .metric-label {
            color: var(--text-muted);
        }

        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
        }

        .progress-bar-bg {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 4px;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            width: 0%;
            border-radius: 3px;
            transition: width 0.4s ease;
        }

        .card-actions {
            display: flex;
            gap: 8px;
            margin-top: auto;
        }

        .card-actions button {
            flex: 1;
            justify-content: center;
            padding: 8px 10px;
            font-size: 12px;
        }

        /* Central Log Center */
        .log-center {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            flex: 1;
            min-height: 380px;
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }

        .log-filters {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .filter-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
        }

        .filter-btn.active {
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--accent-blue);
            color: var(--accent-blue);
        }

        .search-box {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-glass);
            padding: 6px 12px;
            border-radius: 6px;
            color: #fff;
            font-size: 12px;
            font-family: 'Outfit', sans-serif;
            outline: none;
            width: 220px;
        }

        .log-console {
            background: #06090f;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 14px;
            flex: 1;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.6;
            max-height: 380px;
        }

        .log-line {
            display: flex;
            gap: 12px;
            padding: 2px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
        }

        .log-ts {
            color: #64748b;
            min-width: 140px;
        }

        .log-badge {
            padding: 0 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            height: 18px;
            display: inline-flex;
            align-items: center;
        }

        .badge-login { background: rgba(241, 245, 249, 0.15); color: #f8fafc; }
        .badge-game  { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .badge-chat  { background: rgba(56, 189, 248, 0.2); color: #38bdf8; }

        .badge-info  { color: #94a3b8; }
        .badge-warn  { color: #fbbf24; }
        .badge-error { color: #f87171; font-weight: 700; }

        .log-msg {
            color: #e2e8f0;
            word-break: break-all;
        }
        .log-msg.srv-login { color: #f1f5f9; }
        .log-msg.srv-game  { color: #a7f3d0; }
        .log-msg.srv-chat  { color: #bae6fd; }
    </style>
</head>
<body>
    <header>
        <div class="logo-area">
            <div class="logo-icon">A</div>
            <div>
                <div class="logo-title">Aion Classic EU — EmuRust Manager</div>
                <div class="logo-subtitle">Unified Architecture & Observability Hub</div>
            </div>
        </div>
        <div class="master-controls">
            <button class="btn-start" onclick="startAll()">▶ LIGAR TODOS</button>
            <button class="btn-stop" onclick="stopAll()">⏹ PARAR TODOS</button>
            <button class="btn-restart" onclick="restartAll()">🔄 REINICIAR TODOS</button>
        </div>
    </header>

    <main>
        <div class="cards-grid">
            <!-- Login Server Card -->
            <div class="card" id="card-login">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-login"></div>
                        <div class="card-title">Login-Server</div>
                    </div>
                    <div class="card-tag">Port 2106 | 13001 | 6600</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row">
                        <span class="metric-label">Status / Uptime</span>
                        <span class="metric-value" id="val-uptime-login">OFFLINE</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">CPU Usage</span>
                        <span class="metric-value" id="val-cpu-login">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-cpu-login"></div></div>
                    <div class="metric-row" style="margin-top: 4px;">
                        <span class="metric-label">Memory RAM</span>
                        <span class="metric-value" id="val-mem-login">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-mem-login"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('login', 'start')">Ligar</button>
                    <button class="btn-stop" onclick="controlServer('login', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('login', 'restart')">Reiniciar</button>
                </div>
            </div>

            <!-- Game Server Card -->
            <div class="card" id="card-game">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-game"></div>
                        <div class="card-title">Game-Server</div>
                    </div>
                    <div class="card-tag">Port 7777 | 20 TPS</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row">
                        <span class="metric-label">Status / Uptime</span>
                        <span class="metric-value" id="val-uptime-game">OFFLINE</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">CPU Usage</span>
                        <span class="metric-value" id="val-cpu-game">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-cpu-game"></div></div>
                    <div class="metric-row" style="margin-top: 4px;">
                        <span class="metric-label">Memory RAM</span>
                        <span class="metric-value" id="val-mem-game">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-mem-game"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('game', 'start')">Ligar</button>
                    <button class="btn-stop" onclick="controlServer('game', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('game', 'restart')">Reiniciar</button>
                </div>
            </div>

            <!-- Chat Server Card -->
            <div class="card" id="card-chat">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-chat"></div>
                        <div class="card-title">Chat-Server</div>
                    </div>
                    <div class="card-tag">Port 10241</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row">
                        <span class="metric-label">Status / Uptime</span>
                        <span class="metric-value" id="val-uptime-chat">OFFLINE</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">CPU Usage</span>
                        <span class="metric-value" id="val-cpu-chat">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-cpu-chat"></div></div>
                    <div class="metric-row" style="margin-top: 4px;">
                        <span class="metric-label">Memory RAM</span>
                        <span class="metric-value" id="val-mem-chat">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-mem-chat"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('chat', 'start')">Ligar</button>
                    <button class="btn-stop" onclick="controlServer('chat', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('chat', 'restart')">Reiniciar</button>
                </div>
            </div>
        </div>

        <!-- Central Log Center -->
        <div class="log-center">
            <div class="log-header">
                <div class="log-filters">
                    <span style="font-size: 13px; font-weight: 600; margin-right: 6px;">LOG CENTER:</span>
                    <button class="filter-btn active" onclick="setFilter('srv', 'all', this)">Todos</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'login', this)">Login (Branco)</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'game', this)">Game (Verde)</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'chat', this)">Chat (Ciano)</button>
                </div>
                <div class="log-filters">
                    <input type="text" class="search-box" id="search-input" placeholder="🔍 Filtrar logs..." onkeyup="renderLogs()">
                    <button class="filter-btn" onclick="clearLogs()">Limpar</button>
                    <button class="filter-btn" id="pause-btn" onclick="togglePause()">Pausar</button>
                </div>
            </div>
            <div class="log-console" id="log-console">
                <!-- Log entries rendered dynamically -->
            </div>
        </div>
    </main>

    <script>
        let currentSrvFilter = 'all';
        let isPaused = false;
        let logBuffer = [];

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                data.forEach(s => {
                    const dot = document.getElementById(`dot-${s.name}`);
                    const uptimeVal = document.getElementById(`val-uptime-${s.name}`);
                    const cpuVal = document.getElementById(`val-cpu-${s.name}`);
                    const cpuBar = document.getElementById(`bar-cpu-${s.name}`);
                    const memVal = document.getElementById(`val-mem-${s.name}`);
                    const memBar = document.getElementById(`bar-mem-${s.name}`);

                    if (dot) {
                        dot.className = 'status-dot ' + (s.status === 'Online' ? 'online' : (s.status === 'Crashed' ? 'crashed' : ''));
                    }
                    if (uptimeVal) {
                        if (s.status === 'Online') {
                            const hrs = Math.floor(s.uptime_secs / 3600).toString().padStart(2, '0');
                            const mins = Math.floor((s.uptime_secs % 3600) / 60).toString().padStart(2, '0');
                            const secs = (s.uptime_secs % 60).toString().padStart(2, '0');
                            uptimeVal.innerText = `ONLINE (${hrs}:${mins}:${secs})`;
                        } else {
                            uptimeVal.innerText = s.status.toUpperCase();
                        }
                    }
                    if (cpuVal) cpuVal.innerText = `${s.cpu_percent.toFixed(1)}%`;
                    if (cpuBar) cpuBar.style.width = `${Math.min(s.cpu_percent, 100)}%`;
                    if (memVal) memVal.innerText = `${s.memory_mb.toFixed(1)} MB`;
                    if (memBar) memBar.style.width = `${Math.min((s.memory_mb / 2048) * 100, 100)}%`;
                });
            } catch (e) {
                console.error("Error fetching metrics:", e);
            }
        }

        async function fetchLogs() {
            if (isPaused) return;
            try {
                const res = await fetch(`/api/logs?server=${currentSrvFilter}`);
                const data = await res.json();
                logBuffer = data;
                renderLogs();
            } catch (e) {
                console.error("Error fetching logs:", e);
            }
        }

        function renderLogs() {
            const consoleBox = document.getElementById('log-console');
            const search = document.getElementById('search-input').value.toLowerCase();
            const shouldScroll = consoleBox.scrollTop + consoleBox.clientHeight >= consoleBox.scrollHeight - 20;

            consoleBox.innerHTML = logBuffer
                .filter(entry => {
                    if (currentSrvFilter !== 'all' && entry.server !== currentSrvFilter) return false;
                    if (search && !entry.message.toLowerCase().includes(search)) return false;
                    return true;
                })
                .map(entry => {
                    const srvClass = `srv-${entry.server}`;
                    const badgeClass = `badge-${entry.server}`;
                    const lvlClass = `badge-${entry.level.toLowerCase()}`;
                    return `<div class="log-line">
                        <span class="log-ts">${entry.timestamp}</span>
                        <span class="log-badge ${badgeClass}">${entry.server}</span>
                        <span class="log-badge ${lvlClass}">${entry.level}</span>
                        <span class="log-msg ${srvClass}">${escapeHtml(entry.message)}</span>
                    </div>`;
                })
                .join('');

            if (shouldScroll) {
                consoleBox.scrollTop = consoleBox.scrollHeight;
            }
        }

        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        function setFilter(type, val, btn) {
            if (type === 'srv') {
                currentSrvFilter = val;
                document.querySelectorAll('.log-filters .filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderLogs();
            }
        }

        function clearLogs() {
            logBuffer = [];
            renderLogs();
        }

        function togglePause() {
            isPaused = !isPaused;
            const btn = document.getElementById('pause-btn');
            btn.innerText = isPaused ? 'Resumir' : 'Pausar';
            btn.classList.toggle('active', isPaused);
        }

        async function controlServer(name, action) {
            try {
                await fetch(`/api/control/${name}/${action}`, { method: 'POST' });
                setTimeout(fetchMetrics, 300);
            } catch (e) {
                console.error(e);
            }
        }

        async function startAll() {
            await controlServer('login', 'start');
            await controlServer('game', 'start');
            await controlServer('chat', 'start');
        }

        async function stopAll() {
            await controlServer('chat', 'stop');
            await controlServer('game', 'stop');
            await controlServer('login', 'stop');
        }

        async function restartAll() {
            await controlServer('login', 'restart');
            await controlServer('game', 'restart');
            await controlServer('chat', 'restart');
        }

        setInterval(fetchMetrics, 1000);
        setInterval(fetchLogs, 800);
        fetchMetrics();
        fetchLogs();
    </script>
</body>
</html>
"#;
