pub const HTML_DASHBOARD: &str = r#"<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aion Classic - Emulador Rust</title>
    <style>
        :root {
            --bg-base: #0a0e17;
            --bg-card: rgba(16, 22, 36, 0.88);
            --bg-card-hover: rgba(22, 30, 48, 0.95);
            --border-glass: rgba(255, 255, 255, 0.09);
            --border-glow: rgba(56, 189, 248, 0.25);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --accent-purple: #a855f7;
            --fibonacci-gold: rgba(234, 179, 8, 0.65);
            --fibonacci-grid: rgba(255, 255, 255, 0.06);
            --font-scale: 1rem;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            font-family: Arial, Helvetica, sans-serif !important;
        }

        html {
            font-size: var(--font-scale);
        }

        body {
            background: radial-gradient(circle at top right, #111a33, #070a12 70%);
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
            padding: 16px 28px;
            background: rgba(8, 12, 20, 0.85);
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
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 22px;
            box-shadow: 0 4px 16px rgba(56, 189, 248, 0.3);
            color: #ffffff;
        }

        .logo-title {
            font-size: 1.25rem;
            font-weight: bold;
            letter-spacing: -0.3px;
        }

        .logo-subtitle {
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: normal;
        }

        .master-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        button {
            font-size: 0.82rem;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 7px;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
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

        .btn-secondary {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border-glass);
            color: #e2e8f0;
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .btn-danger {
            background: linear-gradient(135deg, #dc2626, #ef4444);
            color: #fff;
            box-shadow: 0 2px 10px rgba(239, 68, 68, 0.3);
        }
        .btn-danger:hover {
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.5);
            transform: translateY(-1px);
        }

        /* Container Layout */
        main {
            flex: 1;
            padding: 24px 28px;
            display: flex;
            flex-direction: column;
            gap: 22px;
            max-width: 1480px;
            margin: 0 auto;
            width: 100%;
        }

        /* 3 Cards Grid */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            padding: 20px;
            backdrop-filter: blur(20px);
            box-shadow: 0 6px 28px rgba(0, 0, 0, 0.35);
            display: flex;
            flex-direction: column;
            gap: 14px;
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
            background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.6), transparent);
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
            width: 11px;
            height: 11px;
            border-radius: 50%;
            background: var(--accent-red);
            box-shadow: 0 0 10px var(--accent-red);
            transition: all 0.3s ease;
        }

        .status-dot.online {
            background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
        }

        .status-dot.starting {
            background: var(--accent-yellow);
            box-shadow: 0 0 10px var(--accent-yellow);
        }

        .status-dot.crashed {
            background: #e11d48;
            box-shadow: 0 0 12px #e11d48;
        }

        .card-title {
            font-size: 1.05rem;
            font-weight: bold;
            letter-spacing: -0.2px;
        }

        .card-tag {
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.07);
            color: var(--text-muted);
            font-weight: bold;
        }

        /* Metrics */
        .metrics-box {
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: rgba(0, 0, 0, 0.25);
            padding: 14px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
        }

        .metric-label {
            color: var(--text-muted);
        }

        .metric-value {
            font-weight: bold;
            color: #ffffff;
        }

        .progress-bar-bg {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 3px;
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
            padding: 8px;
            font-size: 0.78rem;
        }

        /* Financial & Fibonacci Charts Section */
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }

        .chart-card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 6px 28px rgba(0, 0, 0, 0.35);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chart-title {
            font-size: 0.95rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chart-badge {
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 5px;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            font-weight: bold;
        }

        .chart-canvas-box {
            position: relative;
            width: 100%;
            height: 170px;
            background: #060911;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            overflow: hidden;
        }

        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }

        .chart-stats-row {
            display: flex;
            justify-content: space-around;
            background: rgba(0, 0, 0, 0.2);
            padding: 8px;
            border-radius: 8px;
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .chart-stat-item span {
            color: #ffffff;
            font-weight: bold;
            margin-left: 4px;
        }

        /* Online Players & Accounts Section */
        .players-section {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 6px 28px rgba(0, 0, 0, 0.35);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .players-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .players-table-container {
            max-height: 190px;
            overflow-y: auto;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            background: #060911;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
            text-align: left;
        }

        th {
            background: rgba(255, 255, 255, 0.04);
            padding: 9px 14px;
            color: var(--text-muted);
            font-weight: bold;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            position: sticky;
            top: 0;
        }

        td {
            padding: 8px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
            color: #e2e8f0;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.03);
        }

        /* Central Log Center */
        .log-center {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            padding: 18px 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: 0 6px 28px rgba(0, 0, 0, 0.35);
            flex: 1;
            min-height: 280px;
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }

        .log-filters {
            display: flex;
            gap: 6px;
            align-items: center;
            flex-wrap: wrap;
        }

        .filter-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
        }

        .filter-btn.active {
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--accent-blue);
            color: var(--accent-blue);
        }

        .search-box {
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-glass);
            padding: 6px 12px;
            border-radius: 6px;
            color: #fff;
            font-size: 0.78rem;
            outline: none;
            width: 200px;
        }

        .log-console {
            background: #05080e;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px;
            flex: 1;
            overflow-y: auto;
            font-size: 0.78rem;
            line-height: 1.5;
            max-height: 320px;
        }

        .log-line {
            display: flex;
            gap: 10px;
            padding: 2px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
            align-items: flex-start;
        }

        .log-ts {
            color: #64748b;
            min-width: 75px;
            font-weight: bold;
        }

        .log-badge {
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 0.68rem;
            font-weight: bold;
            text-transform: uppercase;
        }

        .badge-login { background: rgba(241, 245, 249, 0.15); color: #f8fafc; }
        .badge-game  { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .badge-chat  { background: rgba(56, 189, 248, 0.2); color: #38bdf8; }
        .badge-launcher { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }

        .log-msg {
            color: #e2e8f0;
            word-break: break-all;
            flex: 1;
        }
        .log-msg.srv-login { color: #f1f5f9; }
        .log-msg.srv-game  { color: #a7f3d0; }
        .log-msg.srv-chat  { color: #bae6fd; }
        .log-msg.srv-launcher { color: #fef08a; }

        /* Modal Confirmation */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(8px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal-box {
            background: #0f172a;
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 14px;
            padding: 26px;
            max-width: 480px;
            width: 90%;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .modal-title {
            font-size: 1.15rem;
            font-weight: bold;
            color: #f87171;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .modal-text {
            font-size: 0.88rem;
            color: #cbd5e1;
            line-height: 1.5;
        }

        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 6px;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-area">
            <div class="logo-icon">A</div>
            <div>
                <div class="logo-title">Emulador Rust - Gerenciador</div>
                <div class="logo-subtitle">Hub de Arquitetura Unificada e Observabilidade</div>
            </div>
        </div>
        <div class="master-controls">
            <button class="btn-start" onclick="startAll()">▶ INICIAR TODOS</button>
            <button class="btn-stop" onclick="stopAll()">⏹ PARAR TODOS</button>
            <button class="btn-restart" onclick="restartAll()">🔄 REINICIAR TODOS</button>
            <button class="btn-secondary" onclick="toggleFullscreen()" title="Tela Cheia">⛶ Tela Cheia</button>
            <button class="btn-secondary" onclick="zoomFont(-1)" title="Diminuir Fonte">A-</button>
            <button class="btn-secondary" onclick="zoomFont(1)" title="Aumentar Fonte">A+</button>
            <button class="btn-danger" onclick="openShutdownModal()">🛑 ENCERRAR</button>
        </div>
    </header>

    <main>
        <!-- 3 Server Status Cards -->
        <div class="cards-grid">
            <!-- Login Server Card -->
            <div class="card" id="card-login">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-login"></div>
                        <div class="card-title">Login-Server</div>
                    </div>
                    <div class="card-tag">Portas: 2106 | 13001 | 6600</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row">
                        <span class="metric-label">Status / Uptime:</span>
                        <span class="metric-value" id="val-uptime-login">OFFLINE</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Uso de CPU:</span>
                        <span class="metric-value" id="val-cpu-login">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-cpu-login"></div></div>
                    <div class="metric-row" style="margin-top: 4px;">
                        <span class="metric-label">Memória RAM:</span>
                        <span class="metric-value" id="val-mem-login">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-mem-login"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('login', 'start')">Iniciar</button>
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
                    <div class="card-tag">Porta: 7777 | 20 TPS</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row">
                        <span class="metric-label">Status / Uptime:</span>
                        <span class="metric-value" id="val-uptime-game">OFFLINE</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Uso de CPU:</span>
                        <span class="metric-value" id="val-cpu-game">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-cpu-game"></div></div>
                    <div class="metric-row" style="margin-top: 4px;">
                        <span class="metric-label">Memória RAM:</span>
                        <span class="metric-value" id="val-mem-game">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-mem-game"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('game', 'start')">Iniciar</button>
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
                    <div class="card-tag">Porta: 10241</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row">
                        <span class="metric-label">Status / Uptime:</span>
                        <span class="metric-value" id="val-uptime-chat">OFFLINE</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Uso de CPU:</span>
                        <span class="metric-value" id="val-cpu-chat">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-cpu-chat"></div></div>
                    <div class="metric-row" style="margin-top: 4px;">
                        <span class="metric-label">Memória RAM:</span>
                        <span class="metric-value" id="val-mem-chat">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="bar-mem-chat"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('chat', 'start')">Iniciar</button>
                    <button class="btn-stop" onclick="controlServer('chat', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('chat', 'restart')">Reiniciar</button>
                </div>
            </div>
        </div>

        <!-- Financial & Fibonacci Resource Charts -->
        <div class="charts-section">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">Monitoramento de CPU (Níveis Fibonacci)</div>
                    <div class="chart-badge" id="chart-cpu-val">0.0% Atual</div>
                </div>
                <div class="chart-canvas-box">
                    <canvas id="canvas-cpu"></canvas>
                </div>
                <div class="chart-stats-row">
                    <div class="chart-stat-item">Mín:<span id="stat-cpu-min">0.0%</span></div>
                    <div class="chart-stat-item">Máx:<span id="stat-cpu-max">0.0%</span></div>
                    <div class="chart-stat-item">Média:<span id="stat-cpu-avg">0.0%</span></div>
                    <div class="chart-stat-item">Tendência:<span id="stat-cpu-trend">Estável</span></div>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">Monitoramento de Memória RAM</div>
                    <div class="chart-badge" id="chart-mem-val">0.0 MB Atual</div>
                </div>
                <div class="chart-canvas-box">
                    <canvas id="canvas-mem"></canvas>
                </div>
                <div class="chart-stats-row">
                    <div class="chart-stat-item">Mín:<span id="stat-mem-min">0.0 MB</span></div>
                    <div class="chart-stat-item">Máx:<span id="stat-mem-max">0.0 MB</span></div>
                    <div class="chart-stat-item">Média:<span id="stat-mem-avg">0.0 MB</span></div>
                    <div class="chart-stat-item">Uptime:<span id="stat-launcher-uptime">00:00:00</span></div>
                </div>
            </div>
        </div>

        <!-- Online Players & Accounts Section -->
        <div class="players-section">
            <div class="players-header">
                <div style="font-size: 0.95rem; font-weight: bold;">Jogadores e Contas Online (<span id="players-count-badge">0</span>)</div>
                <button class="filter-btn" onclick="fetchPlayers()">Atualizar Lista</button>
            </div>
            <div class="players-table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Conta</th>
                            <th>Personagem</th>
                            <th>Servidor</th>
                            <th>Horário Login</th>
                            <th>Duração Conexão</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="players-table-body">
                        <tr>
                            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">Nenhum jogador conectado no momento.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Central Log Center -->
        <div class="log-center">
            <div class="log-header">
                <div class="log-filters">
                    <span style="font-size: 0.85rem; font-weight: bold; margin-right: 4px;">CENTRAL DE LOGS:</span>
                    <button class="filter-btn active" onclick="setFilter('srv', 'all', this)">Todos</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'login', this)">Login (Branco)</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'game', this)">Game (Verde)</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'chat', this)">Chat (Ciano)</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'launcher', this)">Launcher (Amarelo)</button>
                </div>
                <div class="log-filters">
                    <input type="text" class="search-box" id="search-input" placeholder="Filtrar logs..." onkeyup="renderLogs()">
                    <button class="filter-btn" onclick="clearLogs()">Limpar</button>
                    <button class="filter-btn" id="pause-btn" onclick="togglePause()">Pausar</button>
                </div>
            </div>
            <div class="log-console" id="log-console">
                <!-- Logs rendered dynamically -->
            </div>
        </div>
    </main>

    <!-- Confirmation Modal -->
    <div class="modal-overlay" id="shutdown-modal">
        <div class="modal-box">
            <div class="modal-title">Encerrar Emulador Rust</div>
            <div class="modal-text">
                Atenção: Esta ação irá parar com segurança o Game Server, Login Server e Chat Server, finalizando todos os processos do emulador de forma ordenada.<br><br>
                Tem certeza que deseja encerrar todos os serviços agora?
            </div>
            <div class="modal-actions">
                <button class="btn-secondary" onclick="closeShutdownModal()">Cancelar</button>
                <button class="btn-danger" onclick="confirmShutdown()">Confirmar Encerramento</button>
            </div>
        </div>
    </div>

    <script>
        let currentSrvFilter = 'all';
        let isPaused = false;
        let logBuffer = [];
        let cpuHistory = [];
        let memHistory = [];
        let currentFontScale = 1.0;

        function zoomFont(delta) {
            currentFontScale = Math.min(Math.max(currentFontScale + (delta * 0.08), 0.8), 1.4);
            document.documentElement.style.setProperty('--font-scale', `${currentFontScale}rem`);
        }

        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => console.log(err));
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        }

        function openShutdownModal() {
            document.getElementById('shutdown-modal').style.display = 'flex';
        }

        function closeShutdownModal() {
            document.getElementById('shutdown-modal').style.display = 'none';
        }

        async function confirmShutdown() {
            closeShutdownModal();
            try {
                await fetch('/api/shutdown', { method: 'POST' });
            } catch (e) {
                console.error(e);
            }
        }

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                
                if (data.servers) {
                    data.servers.forEach(s => {
                        const dot = document.getElementById(`dot-${s.name}`);
                        const uptimeVal = document.getElementById(`val-uptime-${s.name}`);
                        const cpuVal = document.getElementById(`val-cpu-${s.name}`);
                        const cpuBar = document.getElementById(`bar-cpu-${s.name}`);
                        const memVal = document.getElementById(`val-mem-${s.name}`);
                        const memBar = document.getElementById(`bar-mem-${s.name}`);

                        if (dot) {
                            dot.className = 'status-dot ' + (s.status === 'Online' ? 'online' : (s.status === 'Starting' ? 'starting' : (s.status === 'Crashed' ? 'crashed' : '')));
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
                }

                // Process History and Fibonacci Graphs
                if (data.history && data.history.length > 0) {
                    cpuHistory = data.history.map(h => h.total_cpu);
                    memHistory = data.history.map(h => h.total_mem_mb);

                    const currCpu = data.total_cpu_percent || (cpuHistory.length > 0 ? cpuHistory[cpuHistory.length - 1] : 0);
                    const currMem = data.total_memory_mb || (memHistory.length > 0 ? memHistory[memHistory.length - 1] : 0);

                    document.getElementById('chart-cpu-val').innerText = `${currCpu.toFixed(1)}% Atual`;
                    document.getElementById('chart-mem-val').innerText = `${currMem.toFixed(1)} MB Atual`;

                    const minCpu = Math.min(...cpuHistory);
                    const maxCpu = Math.max(...cpuHistory);
                    const avgCpu = (cpuHistory.reduce((a, b) => a + b, 0) / cpuHistory.length);

                    document.getElementById('stat-cpu-min').innerText = `${minCpu.toFixed(1)}%`;
                    document.getElementById('stat-cpu-max').innerText = `${maxCpu.toFixed(1)}%`;
                    document.getElementById('stat-cpu-avg').innerText = `${avgCpu.toFixed(1)}%`;

                    const minMem = Math.min(...memHistory);
                    const maxMem = Math.max(...memHistory);
                    const avgMem = (memHistory.reduce((a, b) => a + b, 0) / memHistory.length);

                    document.getElementById('stat-mem-min').innerText = `${minMem.toFixed(1)} MB`;
                    document.getElementById('stat-mem-max').innerText = `${maxMem.toFixed(1)} MB`;
                    document.getElementById('stat-mem-avg').innerText = `${avgMem.toFixed(1)} MB`;

                    const u = data.launcher_uptime_secs || 0;
                    const uHrs = Math.floor(u / 3600).toString().padStart(2, '0');
                    const uMins = Math.floor((u % 3600) / 60).toString().padStart(2, '0');
                    const uSecs = (u % 60).toString().padStart(2, '0');
                    document.getElementById('stat-launcher-uptime').innerText = `${uHrs}:${uMins}:${uSecs}`;

                    drawFibonacciChart('canvas-cpu', cpuHistory, 100, '%', '#38bdf8');
                    drawFibonacciChart('canvas-mem', memHistory, Math.max(maxMem * 1.25, 200), ' MB', '#10b981');
                }

                if (data.online_players) {
                    renderPlayers(data.online_players);
                }
            } catch (e) {
                console.error("Error fetching metrics:", e);
            }
        }

        function drawFibonacciChart(canvasId, dataPoints, maxScale, unit, strokeColor) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();

            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const width = rect.width;
            const height = rect.height;

            ctx.clearRect(0, 0, width, height);

            // Fibonacci Retracement Levels (0.0%, 23.6%, 38.2%, 50.0%, 61.8%, 78.6%, 100.0%)
            const fibLevels = [
                { ratio: 1.0, label: '100.0%' },
                { ratio: 0.786, label: '78.6%' },
                { ratio: 0.618, label: '61.8% (Golden)' },
                { ratio: 0.50, label: '50.0%' },
                { ratio: 0.382, label: '38.2%' },
                { ratio: 0.236, label: '23.6%' },
                { ratio: 0.0, label: '0.0%' }
            ];

            // Draw Fibonacci Reference Lines
            ctx.lineWidth = 1;
            ctx.font = '10px Arial';
            fibLevels.forEach(fib => {
                const y = height - (fib.ratio * (height - 20)) - 10;
                ctx.strokeStyle = fib.ratio === 0.618 ? 'rgba(234, 179, 8, 0.4)' : 'rgba(255, 255, 255, 0.07)';
                ctx.setLineDash(fib.ratio === 0.618 ? [4, 4] : [2, 4]);
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();

                ctx.fillStyle = fib.ratio === 0.618 ? '#eab308' : '#64748b';
                ctx.fillText(fib.label, 8, y - 3);
            });

            ctx.setLineDash([]);

            if (!dataPoints || dataPoints.length < 2) return;

            // Draw Data Curve
            const step = width / (dataPoints.length - 1);
            ctx.beginPath();
            dataPoints.forEach((val, i) => {
                const normalized = Math.min(Math.max(val / maxScale, 0), 1);
                const x = i * step;
                const y = height - (normalized * (height - 20)) - 10;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });

            ctx.strokeStyle = strokeColor;
            ctx.lineWidth = 2;
            ctx.shadowColor = strokeColor;
            ctx.shadowBlur = 6;
            ctx.stroke();
            ctx.shadowBlur = 0;

            // Fill gradient under curve
            const lastX = (dataPoints.length - 1) * step;
            ctx.lineTo(lastX, height);
            ctx.lineTo(0, height);
            ctx.closePath();

            const grad = ctx.createLinearGradient(0, 0, 0, height);
            grad.addColorStop(0, strokeColor === '#38bdf8' ? 'rgba(56, 189, 248, 0.25)' : 'rgba(16, 185, 129, 0.25)');
            grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
            ctx.fillStyle = grad;
            ctx.fill();
        }

        async function fetchPlayers() {
            try {
                const res = await fetch('/api/players');
                const players = await res.json();
                renderPlayers(players);
            } catch (e) {
                console.error(e);
            }
        }

        function renderPlayers(players) {
            const badge = document.getElementById('players-count-badge');
            const tbody = document.getElementById('players-table-body');
            badge.innerText = players.length;

            if (!players || players.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">Nenhum jogador conectado no momento.</td></tr>`;
                return;
            }

            tbody.innerHTML = players.map(p => {
                const hrs = Math.floor(p.duration_secs / 3600).toString().padStart(2, '0');
                const mins = Math.floor((p.duration_secs % 3600) / 60).toString().padStart(2, '0');
                const secs = (p.duration_secs % 60).toString().padStart(2, '0');
                return `<tr>
                    <td style="font-weight: bold;">${escapeHtml(p.account_name)}</td>
                    <td>${escapeHtml(p.character_name)}</td>
                    <td><span class="card-tag">${escapeHtml(p.server)}</span></td>
                    <td>${escapeHtml(p.login_time)}</td>
                    <td>${hrs}:${mins}:${secs}</td>
                    <td><span style="color: var(--accent-green); font-weight: bold;">${escapeHtml(p.status)}</span></td>
                </tr>`;
            }).join('');
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
                    return `<div class="log-line">
                        <span class="log-ts">${entry.timestamp}</span>
                        <span class="log-badge ${badgeClass}">${entry.server}</span>
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
            btn.innerText = isPaused ? 'Continuar' : 'Pausar';
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
