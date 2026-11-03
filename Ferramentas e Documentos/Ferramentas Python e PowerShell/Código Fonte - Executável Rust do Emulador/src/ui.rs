pub const HTML_DASHBOARD: &str = r##"<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Aion Classic 5.0 — Multi-Server Management Dashboard</title>
    <style>
        :root {
            --bg-base: #060911;
            --bg-surface: #0b1120;
            --bg-card: rgba(15, 23, 42, 0.85);
            --bg-card-hover: rgba(30, 41, 59, 0.95);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(56, 189, 248, 0.3);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-chat: #06b6d4;
            --accent-login: #f59e0b;
            --accent-gf: #38bdf8;
            --accent-rm: #10b981;
            --accent-br: #f97316;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: var(--font-family);
        }

        body {
            width: 100vw;
            height: 100vh;
            background: radial-gradient(circle at 85% 10%, #111e38 0%, var(--bg-base) 80%);
            color: var(--text-main);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        /* Top Bar */
        header {
            height: 52px;
            background: rgba(11, 17, 32, 0.94);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            z-index: 100;
            flex-shrink: 0;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 14px;
            color: #060911;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
        }

        .brand-title {
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .brand-title span.badge {
            font-size: 10px;
            padding: 2px 7px;
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: #38bdf8;
            border-radius: 9999px;
            font-weight: 600;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-glass);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .btn-primary {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            border: none;
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #0369a1, #1d4ed8);
        }

        .btn-danger {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #fca5a5;
        }
        .btn-danger:hover {
            background: rgba(239, 68, 68, 0.25);
            border-color: #ef4444;
        }

        .btn-success {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #6ee7b7;
        }
        .btn-success:hover {
            background: rgba(16, 185, 129, 0.25);
            border-color: #10b981;
        }

        /* App Layout */
        .app-body {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* Sidebar */
        aside.sidebar {
            width: 220px;
            background: rgba(11, 17, 32, 0.7);
            border-right: 1px solid var(--border-glass);
            display: flex;
            flex-direction: column;
            padding: 12px 8px;
            gap: 4px;
            flex-shrink: 0;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.18s;
            user-select: none;
        }

        .nav-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
        }

        .nav-item.active {
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            font-weight: 600;
            border-left: 3px solid #38bdf8;
        }

        .sidebar-spacer {
            flex: 1;
        }

        .sys-kpis {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border-glass);
            border-radius: 8px;
            padding: 10px;
            font-size: 11px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .kpi-row {
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
        }

        .kpi-row b {
            color: var(--text-main);
        }

        /* Main Content View Container */
        main.main-content {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .view-section {
            display: none;
            flex-direction: column;
            gap: 18px;
        }

        .view-section.active {
            display: flex;
        }

        /* Section Headers */
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .section-title {
            font-size: 17px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section-subtitle {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* KPI Banner */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            transition: all 0.2s;
        }

        .kpi-card:hover {
            border-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-1px);
        }

        .kpi-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            font-weight: 600;
        }

        .kpi-val {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-main);
        }

        .kpi-meta {
            font-size: 11px;
            color: var(--text-muted);
        }

        /* Server Cards Grid */
        .server-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
        }

        .server-card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            transition: all 0.2s;
            position: relative;
            overflow: hidden;
        }

        .server-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--card-accent, #38bdf8);
        }

        .server-card:hover {
            border-color: rgba(255, 255, 255, 0.18);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        }

        .sc-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .sc-title {
            font-size: 15px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tag-pill {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.08);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 9999px;
            background: rgba(255, 255, 255, 0.05);
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #94a3b8;
        }

        .status-online {
            color: #34d399;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.25);
        }
        .status-online .status-dot {
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
        }

        .status-starting {
            color: #fbbf24;
            background: rgba(245, 158, 11, 0.12);
            border: 1px solid rgba(245, 158, 11, 0.25);
        }
        .status-starting .status-dot {
            background: #f59e0b;
        }

        .status-offline {
            color: #94a3b8;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        .status-crashed {
            color: #f87171;
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.25);
        }
        .status-crashed .status-dot {
            background: #ef4444;
        }

        .sc-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            background: rgba(0, 0, 0, 0.25);
            padding: 10px;
            border-radius: 8px;
            font-size: 11px;
        }

        .sc-field {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .sc-field-label {
            color: var(--text-muted);
            font-size: 10px;
            text-transform: uppercase;
        }

        .sc-field-val {
            font-weight: 600;
            color: var(--text-main);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .sc-actions {
            display: flex;
            gap: 6px;
        }

        .sc-actions .btn {
            flex: 1;
            justify-content: center;
            font-size: 11px;
            padding: 5px 8px;
        }

        /* Properties Manager View */
        .properties-container {
            display: flex;
            gap: 16px;
            height: calc(100vh - 120px);
        }

        .prop-files-panel {
            width: 280px;
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            padding: 12px;
            gap: 10px;
            flex-shrink: 0;
            overflow-y: auto;
        }

        .prop-file-item {
            padding: 8px 10px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .prop-file-item:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--border-glass);
        }

        .prop-file-item.active {
            background: rgba(56, 189, 248, 0.12);
            border-color: #38bdf8;
        }

        .pfi-name {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-main);
        }

        .pfi-meta {
            font-size: 10px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }

        .prop-editor-panel {
            flex: 1;
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .pe-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0, 0, 0, 0.2);
        }

        .pe-body {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .prop-row {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-glass);
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .prop-row-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .prop-key {
            font-size: 12px;
            font-weight: 700;
            color: #38bdf8;
            font-family: monospace;
        }

        .prop-cat-badge {
            font-size: 9px;
            padding: 1px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
        }

        .prop-comment {
            font-size: 11px;
            color: var(--text-muted);
            font-style: italic;
        }

        .prop-input {
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-glass);
            border-radius: 6px;
            padding: 6px 10px;
            color: var(--text-main);
            font-size: 12px;
            font-family: monospace;
            width: 100%;
        }

        .prop-input:focus {
            outline: none;
            border-color: #38bdf8;
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.2);
        }

        /* Database Studio */
        .db-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 14px;
        }

        .db-card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        /* Logs Console */
        .log-container {
            flex: 1;
            background: #04060a;
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 120px);
            overflow: hidden;
        }

        .log-toolbar {
            padding: 8px 12px;
            background: rgba(11, 17, 32, 0.85);
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .log-filter-group {
            display: flex;
            gap: 6px;
        }

        .filter-chip {
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-glass);
            color: var(--text-muted);
            user-select: none;
        }

        .filter-chip.active {
            background: #38bdf8;
            color: #060911;
            border-color: #38bdf8;
        }

        .log-output {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            font-family: Consolas, "Courier New", monospace;
            font-size: 11.5px;
            line-height: 1.45;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .log-entry {
            display: flex;
            gap: 8px;
            word-break: break-all;
        }

        .log-ts {
            color: #64748b;
            flex-shrink: 0;
        }

        .log-srv {
            font-weight: 700;
            flex-shrink: 0;
            padding: 0 4px;
            border-radius: 3px;
            font-size: 10px;
        }

        .log-text {
            color: #cbd5e1;
        }

        /* Toast Notifications */
        #toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 1000;
        }

        .toast {
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid #38bdf8;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.2s ease-out;
        }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="header-brand">
            <div class="brand-logo">A5</div>
            <div class="brand-title">
                AION CLASSIC 5.0
                <span class="badge">MULTI-GAMESERVER</span>
            </div>
        </div>

        <div class="header-actions">
            <button class="btn btn-primary" onclick="controlAll('start')">
                ▶ Iniciar Orquestrado (CS → LS → GS)
            </button>
            <button class="btn btn-danger" onclick="controlAll('stop')">
                ⏹ Parar Todos
            </button>
            <button class="btn" onclick="controlAll('restart')">
                🔄 Reiniciar
            </button>
            <button class="btn btn-success" onclick="orchestrateDatabases()">
                🗄️ Migrar Banco
            </button>
            <button class="btn" onclick="toggleFullscreen()">
                ⛶
            </button>
        </div>
    </header>

    <div class="app-body">
        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <div class="nav-item active" onclick="switchView('dashboard')">
                📊 Dashboard
            </div>
            <div class="nav-item" onclick="switchView('servers')">
                🖥️ Servidores GS
            </div>
            <div class="nav-item" onclick="switchView('properties')">
                ⚙️ Properties Manager
            </div>
            <div class="nav-item" onclick="switchView('database')">
                🗄️ Banco de Dados
            </div>
            <div class="nav-item" onclick="switchView('logs')">
                📜 Logs & Console
            </div>
            <div class="nav-item" onclick="switchView('docs')">
                🛠️ Arquitetura & Portas
            </div>

            <div class="sidebar-spacer"></div>

            <div class="sys-kpis">
                <div class="kpi-row"><span>CPU Total:</span><b id="side-cpu">0.0%</b></div>
                <div class="kpi-row"><span>RAM Total:</span><b id="side-ram">0 MB</b></div>
                <div class="kpi-row"><span>Players GS:</span><b id="side-players">0</b></div>
                <div class="kpi-row"><span>Uptime:</span><b id="side-uptime">00:00:00</b></div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <!-- VIEW: DASHBOARD -->
            <section id="view-dashboard" class="view-section active">
                <div class="section-header">
                    <div>
                        <div class="section-title">Painel Geral de Operações</div>
                        <div class="section-subtitle">Monitoramento em tempo real dos serviços ativos e GameServers independentes</div>
                    </div>
                </div>

                <!-- KPI Cards -->
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">Status do Cluster</div>
                        <div class="kpi-val" id="kpi-status-text" style="color: #38bdf8;">Pronto</div>
                        <div class="kpi-meta" id="kpi-active-count">0 de 0 serviços online</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Uso de CPU Host</div>
                        <div class="kpi-val" id="kpi-cpu-text">0.0%</div>
                        <div class="kpi-meta">Alocação dinâmica do cluster</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Uso de Memória RAM</div>
                        <div class="kpi-val" id="kpi-ram-text">0 MB</div>
                        <div class="kpi-meta" id="kpi-os-ram">RAM Total: --</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Jogadores Conectados</div>
                        <div class="kpi-val" id="kpi-players-count" style="color: #34d399;">0</div>
                        <div class="kpi-meta">Sincronização MySQL em tempo real</div>
                    </div>
                </div>

                <!-- Dynamic Server Cards Grid -->
                <div class="section-header" style="margin-top: 10px;">
                    <div class="section-title">Instâncias de Servidores Habilitadas</div>
                </div>
                <div class="server-grid" id="dashboard-server-grid">
                    <!-- Injected dynamically by JS according to config.json enabled servers -->
                </div>
            </section>

            <!-- VIEW: INDIVIDUAL SERVERS -->
            <section id="view-servers" class="view-section">
                <div class="section-header">
                    <div>
                        <div class="section-title">Gerenciamento Individual dos GameServers</div>
                        <div class="section-subtitle">Controle isolado de processos, portas e bancos de dados de cada modalidade</div>
                    </div>
                </div>
                <div class="server-grid" id="individual-server-grid">
                    <!-- Populated dynamically -->
                </div>
            </section>

            <!-- VIEW: PROPERTIES MANAGER -->
            <section id="view-properties" class="view-section">
                <div class="section-header">
                    <div>
                        <div class="section-title">Gerenciador Integrado de Properties</div>
                        <div class="section-subtitle">Edição direta com backup automático (.bak) e categorização inteligente</div>
                    </div>
                </div>

                <div class="properties-container">
                    <!-- File list panel -->
                    <div class="prop-files-panel" id="prop-files-list">
                        <div style="font-size: 11px; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Arquivos de Configuração</div>
                        <!-- Injected by JS -->
                    </div>

                    <!-- Editor panel -->
                    <div class="prop-editor-panel">
                        <div class="pe-header">
                            <div>
                                <span style="font-size: 13px; font-weight: 700;" id="pe-current-file">Selecione um arquivo .properties</span>
                                <span style="font-size: 11px; color: var(--text-muted); margin-left: 8px;" id="pe-current-path"></span>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <input type="text" id="prop-search" placeholder="Filtrar chave..." class="prop-input" style="width: 180px;" oninput="filterProperties()">
                                <button class="btn btn-success" onclick="saveCurrentProperties()">
                                    💾 Salvar Alterações
                                </button>
                            </div>
                        </div>
                        <div class="pe-body" id="prop-rows-container">
                            <div style="color: var(--text-muted); font-size: 13px; padding: 20px; text-align: center;">
                                Selecione um arquivo properties na lista à esquerda para carregar as chaves configuráveis.
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- VIEW: DATABASE STUDIO -->
            <section id="view-database" class="view-section">
                <div class="section-header">
                    <div>
                        <div class="section-title">Banco de Dados & Status de Migrations</div>
                        <div class="section-subtitle">Visualização das instâncias isoladas: aionclassic_cs, aionclassic_ls, aionclassic_gs, gs2, gs3</div>
                    </div>
                    <div>
                        <button class="btn btn-success" onclick="orchestrateDatabases()">
                            ▶ Executar Migração & Validação Completa
                        </button>
                    </div>
                </div>

                <div class="db-grid" id="db-summaries-grid">
                    <!-- Injected by JS -->
                </div>
            </section>

            <!-- VIEW: LOGS & CONSOLE -->
            <section id="view-logs" class="view-section">
                <div class="section-header">
                    <div>
                        <div class="section-title">Console Centralizado & Logs em Tempo Real</div>
                        <div class="section-subtitle">Captura unificada de stdout/stderr de todos os processos e supervisor</div>
                    </div>
                </div>

                <div class="log-container">
                    <div class="log-toolbar">
                        <div class="log-filter-group" id="log-filter-chips">
                            <div class="filter-chip active" onclick="setLogFilter('all')">Todos</div>
                            <div class="filter-chip" onclick="setLogFilter('launcher')">Launcher / DB</div>
                            <div class="filter-chip" onclick="setLogFilter('chat')">ChatServer</div>
                            <div class="filter-chip" onclick="setLogFilter('login')">LoginServer</div>
                            <div class="filter-chip" onclick="setLogFilter('gameforge')">GameForge (GS1)</div>
                            <div class="filter-chip" onclick="setLogFilter('remake')">Remake (GS2)</div>
                            <div class="filter-chip" onclick="setLogFilter('battleroyale')">BattleRoyale (GS3)</div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <label style="font-size: 11px; display: flex; align-items: center; gap: 4px; color: var(--text-muted);">
                                <input type="checkbox" id="auto-scroll-chk" checked> Auto-Scroll
                            </label>
                            <button class="btn" onclick="clearLogDisplay()">Limpar Tela</button>
                        </div>
                    </div>
                    <div class="log-output" id="log-display"></div>
                </div>
            </section>

            <!-- VIEW: ARCHITECTURE & PORTS -->
            <section id="view-docs" class="view-section">
                <div class="section-header">
                    <div class="section-title">Arquitetura Multi-GameServer & Mapeamento de Portas</div>
                </div>

                <div style="background: var(--bg-card); border: 1px solid var(--border-glass); border-radius: 10px; padding: 18px; display: flex; flex-direction: column; gap: 14px;">
                    <h3 style="font-size: 14px; color: #38bdf8;">Mapeamento Oficial de Portas e Identificadores (GSID)</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <thead>
                            <tr style="background: rgba(255, 255, 255, 0.05); text-align: left;">
                                <th style="padding: 8px;">Serviço</th>
                                <th style="padding: 8px;">GSID</th>
                                <th style="padding: 8px;">Porta Cliente</th>
                                <th style="padding: 8px;">Porta Interna / Telemetria</th>
                                <th style="padding: 8px;">Banco de Dados</th>
                                <th style="padding: 8px;">Função / Descrição</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid var(--border-glass);">
                                <td style="padding: 8px; font-weight: 700; color: #06b6d4;">ChatServer (CS)</td>
                                <td style="padding: 8px;">-</td>
                                <td style="padding: 8px;">10241</td>
                                <td style="padding: 8px;">9021 (GS listener)</td>
                                <td style="padding: 8px;"><code>aionclassic_cs</code></td>
                                <td style="padding: 8px;">Compartilhado entre todos os GS</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border-glass);">
                                <td style="padding: 8px; font-weight: 700; color: #f59e0b;">LoginServer (LS)</td>
                                <td style="padding: 8px;">-</td>
                                <td style="padding: 8px;">2106</td>
                                <td style="padding: 8px;">9014 (GS listener)</td>
                                <td style="padding: 8px;"><code>aionclassic_ls</code></td>
                                <td style="padding: 8px;">Autenticação central e lista de mundos</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border-glass);">
                                <td style="padding: 8px; font-weight: 700; color: #38bdf8;">GameForge</td>
                                <td style="padding: 8px; font-weight: 700;">1</td>
                                <td style="padding: 8px;">7777</td>
                                <td style="padding: 8px;">2130 (Telemetria)</td>
                                <td style="padding: 8px;"><code>aionclassic_gs</code></td>
                                <td style="padding: 8px;">Modalidade Original Clássica</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border-glass);">
                                <td style="padding: 8px; font-weight: 700; color: #10b981;">Remake</td>
                                <td style="padding: 8px; font-weight: 700;">2</td>
                                <td style="padding: 8px;">7778</td>
                                <td style="padding: 8px;">2131 (Telemetria)</td>
                                <td style="padding: 8px;"><code>aionclassic_gs2</code></td>
                                <td style="padding: 8px;">Modalidade Remake / Rates Rebalanceados</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: 700; color: #f97316;">BattleRoyale</td>
                                <td style="padding: 8px; font-weight: 700;">3</td>
                                <td style="padding: 8px;">7779</td>
                                <td style="padding: 8px;">2132 (Telemetria)</td>
                                <td style="padding: 8px;"><code>aionclassic_gs3</code></td>
                                <td style="padding: 8px;">Modalidade BattleRoyale / Instâncias PvP</td>
                            </tr>
                        </tbody>
                    </table>

                    <h3 style="font-size: 14px; color: #38bdf8; margin-top: 10px;">Sequência de Orquestração com Readiness</h3>
                    <p style="font-size: 12px; color: var(--text-muted); line-height: 1.6;">
                        1. <b>Preparação do Banco:</b> O launcher conecta ao MySQL, assegura que as databases (aionclassic_cs, ls, gs, gs2, gs3) existam e valida o registro dos três servidores na tabela <code>gameservers</code> do LoginServer.<br>
                        2. <b>ChatServer:</b> Inicializa e aguarda readiness na porta 10241/9021.<br>
                        3. <b>LoginServer:</b> Inicializa após confirmação do ChatServer e aguarda readiness na porta 2106/9014.<br>
                        4. <b>GameForge (GSID 1):</b> Inicializa após confirmação do LoginServer e aguarda readiness na porta 7777.<br>
                        5. <b>Remake (GSID 2):</b> Inicializa após confirmação do GSID 1 e aguarda readiness na porta 7778.<br>
                        6. <b>BattleRoyale (GSID 3):</b> Inicializa após confirmação do GSID 2 e aguarda readiness na porta 7779.<br>
                        <i>* Servidores desabilitados no <code>config.json</code> são ignorados automaticamente pela sequência e pela interface.</i>
                    </p>
                </div>
            </section>
        </main>
    </div>

    <!-- Toast container -->
    <div id="toast-container"></div>

    <script>
        let currentView = 'dashboard';
        let activeLogFilter = 'all';
        let currentLoadedPropFile = null;
        let currentPropData = null;

        function showToast(msg) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = msg;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 200);
            }, 3500);
        }

        function switchView(viewId) {
            currentView = viewId;
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));

            const target = document.getElementById('view-' + viewId);
            if (target) target.classList.add('active');

            const navIndex = {
                'dashboard': 0, 'servers': 1, 'properties': 2, 'database': 3, 'logs': 4, 'docs': 5
            }[viewId];
            const navItems = document.querySelectorAll('.nav-item');
            if (navItems[navIndex]) navItems[navIndex].classList.add('active');

            if (viewId === 'properties') {
                loadPropertiesFilesList();
            } else if (viewId === 'database') {
                loadDatabaseSummaries();
            }
        }

        // Metrics polling (every 1000ms)
        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                if (!res.ok) return;
                const data = await res.json();
                renderMetrics(data);
            } catch (e) {
                console.error(e);
            }
        }

        function formatUptime(secs) {
            const h = Math.floor(secs / 3600);
            const m = Math.floor((secs % 3600) / 60);
            const s = secs % 60;
            return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }

        function renderMetrics(data) {
            document.getElementById('side-cpu').textContent = data.total_cpu.toFixed(1) + '%';
            document.getElementById('side-ram').textContent = Math.round(data.total_memory_mb) + ' MB';
            document.getElementById('side-players').textContent = data.online_players_count;
            document.getElementById('side-uptime').textContent = formatUptime(data.uptime_secs);

            document.getElementById('kpi-cpu-text').textContent = data.total_cpu.toFixed(1) + '%';
            document.getElementById('kpi-ram-text').textContent = Math.round(data.total_memory_mb) + ' MB';
            document.getElementById('kpi-players-count').textContent = data.online_players_count;
            document.getElementById('kpi-os-ram').textContent = `RAM Host: ${Math.round(data.os_used_memory_mb)} / ${Math.round(data.os_total_memory_mb)} MB`;

            // Active count
            const onlineCount = data.servers.filter(s => s.status === 'Online').length;
            const totalCount = data.servers.length;
            document.getElementById('kpi-active-count').textContent = `${onlineCount} de ${totalCount} serviços online`;
            document.getElementById('kpi-status-text').textContent = onlineCount === totalCount ? 'Todos Operacionais' : (onlineCount > 0 ? 'Parcialmente Online' : 'Serviços Parados');
            document.getElementById('kpi-status-text').style.color = onlineCount === totalCount ? '#34d399' : (onlineCount > 0 ? '#fbbf24' : '#94a3b8');

            // Render Dynamic Server Cards on Dashboard & Servers View
            renderServerCards(data.servers);
        }

        function renderServerCards(servers) {
            const dashGrid = document.getElementById('dashboard-server-grid');
            const indGrid = document.getElementById('individual-server-grid');

            let html = '';
            servers.forEach(s => {
                const statusClass = s.status === 'Online' ? 'status-online' : (s.status === 'Starting' ? 'status-starting' : (s.status === 'Crashed' ? 'status-crashed' : 'status-offline'));
                const statusLabel = s.status === 'Online' ? 'ONLINE' : (s.status === 'Starting' ? 'INICIANDO...' : (s.status === 'Crashed' ? 'FALHOU' : 'OFFLINE'));
                const gsidDisplay = s.gsid ? `<span class="tag-pill" style="color: ${s.color};">GSID ${s.gsid}</span>` : '';
                const portDisplay = s.port ? `${s.port}` : '--';

                html += `
                    <div class="server-card" style="--card-accent: ${s.color};">
                        <div class="sc-top">
                            <div>
                                <div class="sc-title">
                                    <span style="color: ${s.color}; font-weight: 800;">[${s.tag}]</span>
                                    ${s.label}
                                    ${gsidDisplay}
                                </div>
                                <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">
                                    DB: <b style="color: #cbd5e1;">${s.db_name}</b> | Porta: <b style="color: #cbd5e1;">${portDisplay}</b>
                                </div>
                            </div>
                            <div class="status-badge ${statusClass}">
                                <div class="status-dot"></div>
                                ${statusLabel}
                            </div>
                        </div>

                        <div class="sc-details">
                            <div class="sc-field">
                                <span class="sc-field-label">CPU</span>
                                <span class="sc-field-val">${s.cpu_percent.toFixed(1)}%</span>
                            </div>
                            <div class="sc-field">
                                <span class="sc-field-label">Memória</span>
                                <span class="sc-field-val">${Math.round(s.memory_mb)} MB</span>
                            </div>
                            <div class="sc-field">
                                <span class="sc-field-label">PID</span>
                                <span class="sc-field-val">${s.pid || '--'}</span>
                            </div>
                            <div class="sc-field">
                                <span class="sc-field-label">Tempo Ativo</span>
                                <span class="sc-field-val">${formatUptime(s.uptime_secs)}</span>
                            </div>
                        </div>

                        <div class="sc-actions">
                            <button class="btn btn-success" onclick="controlServer('${s.name}', 'start')">▶ Iniciar</button>
                            <button class="btn btn-danger" onclick="controlServer('${s.name}', 'stop')">⏹ Parar</button>
                            <button class="btn" onclick="controlServer('${s.name}', 'restart')">🔄</button>
                            <button class="btn" onclick="openServerLogs('${s.name}')">📜 Logs</button>
                        </div>
                    </div>
                `;
            });

            dashGrid.innerHTML = html;
            indGrid.innerHTML = html;
        }

        async function controlServer(name, action) {
            try {
                showToast(`Enviando comando '${action}' para ${name}...`);
                const res = await fetch(`/api/control/${name}/${action}`, { method: 'POST' });
                const json = await res.json();
                if (json.status === 'ok') {
                    showToast(`Comando '${action}' aceito para ${name}.`);
                } else {
                    showToast(`Erro: ${json.message}`);
                }
            } catch (e) {
                showToast(`Erro de conexão ao enviar comando.`);
            }
        }

        async function controlAll(action) {
            try {
                showToast(`Enviando comando '${action}' para todos os servidores...`);
                const res = await fetch(`/api/control/all/${action}`, { method: 'POST' });
                const json = await res.json();
                if (json.status === 'ok') {
                    showToast(`Orquestração '${action}' iniciada com sucesso!`);
                } else {
                    showToast(`Erro: ${json.message}`);
                }
            } catch (e) {
                showToast(`Erro ao disparar orquestração geral.`);
            }
        }

        async function orchestrateDatabases() {
            try {
                showToast("Executando preparação e migração automática dos bancos...");
                const res = await fetch('/api/db/orchestrate', { method: 'POST' });
                const json = await res.json();
                if (json.status === 'ok') {
                    showToast(json.message);
                    if (currentView === 'database') loadDatabaseSummaries();
                } else {
                    showToast(`Erro na migração: ${json.message}`);
                }
            } catch (e) {
                showToast("Falha na chamada de migração.");
            }
        }

        async function toggleFullscreen() {
            try {
                await fetch('/api/window/fullscreen', { method: 'POST' });
            } catch (e) {}
        }

        function openServerLogs(srvName) {
            switchView('logs');
            setLogFilter(srvName);
        }

        // --- PROPERTIES MANAGER ---
        async function loadPropertiesFilesList() {
            try {
                const res = await fetch('/api/properties/list');
                const json = await res.json();
                if (json.status !== 'ok') return;

                const listEl = document.getElementById('prop-files-list');
                let html = '<div style="font-size: 11px; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Arquivos Properties</div>';

                json.files.forEach(f => {
                    html += `
                        <div class="prop-file-item" onclick="loadPropertyFile('${f.full_path.replace(/\\/g, '\\\\')}', '${f.name}', '${f.server_label}')">
                            <div class="pfi-name">${f.name}</div>
                            <div class="pfi-meta">
                                <span>${f.server_label}</span>
                                <span>${f.category}</span>
                            </div>
                        </div>
                    `;
                });
                listEl.innerHTML = html;
            } catch (e) {
                console.error(e);
            }
        }

        async function loadPropertyFile(fullPath, name, serverLabel) {
            try {
                showToast(`Carregando ${name}...`);
                document.querySelectorAll('.prop-file-item').forEach(el => el.classList.remove('active'));
                const res = await fetch(`/api/properties/file?path=${encodeURIComponent(fullPath)}`);
                const json = await res.json();
                if (json.status !== 'ok') {
                    showToast(`Erro ao carregar properties: ${json.message}`);
                    return;
                }

                currentLoadedPropFile = fullPath;
                currentPropData = json.file;

                document.getElementById('pe-current-file').textContent = `${name} (${serverLabel})`;
                document.getElementById('pe-current-path').textContent = fullPath;

                renderPropertyRows(json.file.items);
            } catch (e) {
                showToast("Erro ao abrir arquivo.");
            }
        }

        function renderPropertyRows(items) {
            const container = document.getElementById('prop-rows-container');
            if (!items || items.length === 0) {
                container.innerHTML = '<div style="color: var(--text-muted); font-size: 13px;">Nenhuma propriedade encontrada neste arquivo.</div>';
                return;
            }

            let html = '';
            items.forEach((item, idx) => {
                const commentHtml = item.comment ? `<div class="prop-comment">${item.comment}</div>` : '';
                html += `
                    <div class="prop-row" data-key="${item.key}">
                        <div class="prop-row-top">
                            <span class="prop-key">${item.key}</span>
                            <span class="prop-cat-badge">${item.category}</span>
                        </div>
                        ${commentHtml}
                        <input type="text" class="prop-input" value="${item.value.replace(/"/g, '&quot;')}" data-orig="${item.value.replace(/"/g, '&quot;')}">
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        function filterProperties() {
            const q = document.getElementById('prop-search').value.toLowerCase();
            document.querySelectorAll('.prop-row').forEach(row => {
                const key = row.getAttribute('data-key').toLowerCase();
                const val = row.querySelector('.prop-input').value.toLowerCase();
                row.style.display = (key.includes(q) || val.includes(q)) ? 'flex' : 'none';
            });
        }

        async function saveCurrentProperties() {
            if (!currentLoadedPropFile) {
                showToast("Nenhum arquivo properties selecionado!");
                return;
            }

            const updates = {};
            document.querySelectorAll('.prop-row').forEach(row => {
                const key = row.getAttribute('data-key');
                const val = row.querySelector('.prop-input').value;
                updates[key] = val;
            });

            try {
                showToast("Gravando alterações e gerando backup .bak...");
                const res = await fetch('/api/properties/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        path: currentLoadedPropFile,
                        updates: updates
                    })
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    showToast(json.message);
                } else {
                    showToast(`Erro ao salvar: ${json.message}`);
                }
            } catch (e) {
                showToast("Falha de conexão ao salvar propriedades.");
            }
        }

        // --- DATABASE SUMMARIES ---
        async function loadDatabaseSummaries() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                const container = document.getElementById('db-summaries-grid');

                let html = '';
                (data.databases || []).forEach(db => {
                    const statusClass = db.is_connected ? 'status-online' : 'status-crashed';
                    const statusLabel = db.is_connected ? 'CONECTADO' : 'DESCONECTADO';

                    html += `
                        <div class="db-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <b style="color: ${db.color}; font-size: 14px;">${db.label}</b>
                                <div class="status-badge ${statusClass}">
                                    <div class="status-dot"></div>
                                    ${statusLabel}
                                </div>
                            </div>
                            <div style="font-size: 12px; color: var(--text-muted);">
                                Database: <code style="color: #f8fafc; font-weight: 700;">${db.db_name}</code><br>
                                Host: ${db.host}:${db.port}<br>
                                Usuário: ${db.user}
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 11px; background: rgba(0,0,0,0.25); padding: 8px; border-radius: 6px;">
                                <span>Tabelas: <b style="color: #38bdf8;">${db.total_tables}</b></span>
                                <span>Registros: <b style="color: #34d399;">${db.total_rows}</b></span>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } catch (e) {
                console.error(e);
            }
        }

        // --- LOGS POLLING ---
        function setLogFilter(srv) {
            activeLogFilter = srv;
            document.querySelectorAll('#log-filter-chips .filter-chip').forEach(c => {
                c.classList.remove('active');
                if (c.textContent.toLowerCase().includes(srv.toLowerCase()) || (srv === 'all' && c.textContent === 'Todos')) {
                    c.classList.add('active');
                }
            });
            fetchLogs();
        }

        function clearLogDisplay() {
            document.getElementById('log-display').innerHTML = '';
        }

        async function fetchLogs() {
            if (currentView !== 'logs' && currentView !== 'dashboard') return;
            try {
                const url = activeLogFilter === 'all' ? '/api/logs' : `/api/logs?server=${activeLogFilter}`;
                const res = await fetch(url);
                if (!res.ok) return;
                const entries = await res.json();
                renderLogEntries(entries);
            } catch (e) {}
        }

        function renderLogEntries(entries) {
            const display = document.getElementById('log-display');
            if (!entries || entries.length === 0) return;

            let html = '';
            entries.forEach(e => {
                const srvColor = {
                    'chat': '#06b6d4', 'login': '#f59e0b', 'gameforge': '#38bdf8', 'remake': '#10b981', 'battleroyale': '#f97316', 'launcher': '#a855f7'
                }[e.server.toLowerCase()] || '#94a3b8';

                html += `
                    <div class="log-entry">
                        <span class="log-ts">[${e.timestamp}]</span>
                        <span class="log-srv" style="color: ${srvColor}; background: rgba(255,255,255,0.06);">[${e.server.toUpperCase()}]</span>
                        <span class="log-text">${escapeHtml(e.message)}</span>
                    </div>
                `;
            });
            display.innerHTML = html;

            if (document.getElementById('auto-scroll-chk').checked) {
                display.scrollTop = display.scrollHeight;
            }
        }

        function escapeHtml(s) {
            return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }

        // Init loops
        setInterval(fetchMetrics, 1000);
        setInterval(fetchLogs, 1500);
        fetchMetrics();
        fetchLogs();
    </script>
</body>
</html>"##;
