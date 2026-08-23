pub const HTML_DASHBOARD: &str = r#"<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Aion Classic - EmuRust Dashboard</title>
    <style>
        :root {
            --bg-base: #060910;
            --bg-surface: #0c121e;
            --bg-card: rgba(15, 23, 42, 0.85);
            --bg-card-hover: rgba(22, 33, 58, 0.95);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(56, 189, 248, 0.3);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-login: #38bdf8;
            --accent-game: #10b981;
            --accent-chat: #a855f7;
            --accent-launcher: #eab308;
            --accent-red: #ef4444;
            --font-scale: 1rem;
            --safe-bottom: env(safe-area-inset-bottom, 0px);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        }

        html, body {
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at top right, #111a33, #060910 75%);
            color: var(--text-main);
            overflow-x: hidden;
            font-size: var(--font-scale);
        }

        body {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        /* Compact Slim Top Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 18px;
            background: rgba(8, 12, 22, 0.92);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-glass);
            position: sticky;
            top: 0;
            z-index: 100;
            width: 100%;
            height: 48px;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .drawer-toggle-btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-glass);
            color: var(--text-main);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .drawer-toggle-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: var(--accent-login);
        }

        .brand-box {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .brand-icon {
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            border-radius: 7px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 15px;
            color: #fff;
            box-shadow: 0 2px 10px rgba(56, 189, 248, 0.35);
        }

        .brand-text {
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: -0.3px;
        }

        .brand-pill {
            font-size: 0.68rem;
            padding: 2px 6px;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-login);
            border-radius: 4px;
            font-weight: 600;
        }

        .header-status-pills {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 0, 0, 0.3);
            padding: 4px 10px;
            border-radius: 20px;
            border: 1px solid var(--border-glass);
        }

        .mini-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--accent-red);
            transition: all 0.3s;
        }
        .mini-dot.online { background: var(--accent-game); box-shadow: 0 0 6px var(--accent-game); }
        .mini-dot.starting { background: var(--accent-launcher); box-shadow: 0 0 6px var(--accent-launcher); }

        .mini-stat-label {
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        button {
            font-size: 0.76rem;
            font-weight: 600;
            padding: 6px 11px;
            border-radius: 6px;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
        }

        .btn-svg {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 13px;
            height: 13px;
        }

        .btn-start {
            background: linear-gradient(135deg, #059669, #10b981);
            color: #fff;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
        }
        .btn-start:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4); }

        .btn-stop {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #fca5a5;
        }
        .btn-stop:hover { background: rgba(239, 68, 68, 0.25); transform: translateY(-1px); }

        .btn-restart {
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.4);
            color: #7dd3fc;
        }
        .btn-restart:hover { background: rgba(56, 189, 248, 0.25); transform: translateY(-1px); }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid var(--border-glass);
            color: #e2e8f0;
        }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.14); }

        .btn-mobile-url {
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(56, 189, 248, 0.2));
            border: 1px solid rgba(168, 85, 247, 0.4);
            color: #e9d5ff;
        }
        .btn-mobile-url:hover { background: rgba(168, 85, 247, 0.35); transform: translateY(-1px); }

        .btn-danger {
            background: linear-gradient(135deg, #dc2626, #ef4444);
            color: #fff;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
        }
        .btn-danger:hover { box-shadow: 0 4px 12px rgba(239, 68, 68, 0.5); transform: translateY(-1px); }

        /* Main Full Width Layout */
        main {
            flex: 1;
            padding: 12px 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            width: 100%;
            max-width: 100%;
        }

        /* 3 Server Status Cards */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            width: 100%;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            padding: 12px 14px;
            backdrop-filter: blur(16px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 10px;
            position: relative;
            overflow: hidden;
            width: 100%;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2.5px;
        }
        #card-login::before { background: linear-gradient(90deg, transparent, var(--accent-login), transparent); }
        #card-game::before { background: linear-gradient(90deg, transparent, var(--accent-game), transparent); }
        #card-chat::before { background: linear-gradient(90deg, transparent, var(--accent-chat), transparent); }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title-box {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: var(--accent-red);
            box-shadow: 0 0 8px var(--accent-red);
            transition: all 0.3s;
        }
        .status-dot.online { background: var(--accent-game); box-shadow: 0 0 8px var(--accent-game); }
        .status-dot.starting { background: var(--accent-launcher); box-shadow: 0 0 8px var(--accent-launcher); }
        .status-dot.crashed { background: #e11d48; box-shadow: 0 0 10px #e11d48; }

        .card-title {
            font-size: 0.92rem;
            font-weight: 700;
        }

        .card-tag {
            font-size: 0.68rem;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-muted);
            font-weight: 600;
        }

        .metrics-box {
            display: flex;
            flex-direction: column;
            gap: 6px;
            background: rgba(0, 0, 0, 0.25);
            padding: 9px;
            border-radius: 7px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.78rem;
        }

        .metric-label { color: var(--text-muted); }
        .metric-value { font-weight: 700; color: #ffffff; }

        .progress-bar-bg {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 2px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            width: 0%;
            border-radius: 2px;
            transition: width 0.4s ease;
        }
        .fill-login { background: linear-gradient(90deg, #0284c7, #38bdf8); }
        .fill-game { background: linear-gradient(90deg, #059669, #10b981); }
        .fill-chat { background: linear-gradient(90deg, #7c3aed, #a855f7); }

        .card-actions {
            display: flex;
            gap: 6px;
            margin-top: auto;
        }

        .card-actions button {
            flex: 1;
            padding: 5px;
            font-size: 0.72rem;
        }

        /* Day-Trade Real-Time Multi-Curve Telemetry Section */
        .daytrade-section {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            padding: 12px 14px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 8px;
            width: 100%;
        }

        .daytrade-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }

        .daytrade-title-box {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.88rem;
            font-weight: 700;
        }

        .daytrade-toggles {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .mode-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.72rem;
            cursor: pointer;
        }
        .mode-btn.active {
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--accent-login);
            color: var(--accent-login);
            font-weight: 700;
        }

        .legend-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.72rem;
            flex-wrap: wrap;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
        }
        .legend-line {
            width: 14px;
            height: 3px;
            border-radius: 2px;
        }
        .legend-login { background: var(--accent-login); }
        .legend-game  { background: var(--accent-game); }
        .legend-chat  { background: var(--accent-chat); }
        .legend-launcher { background: var(--accent-launcher); }
        .legend-total { background: #ffffff; }

        .daytrade-canvas-container {
            position: relative;
            width: 100%;
            height: 180px;
            background: #050810;
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            overflow: hidden;
        }

        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }

        .daytrade-tooltip {
            position: absolute;
            display: none;
            background: rgba(12, 18, 30, 0.95);
            border: 1px solid var(--accent-login);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 0.7rem;
            color: #fff;
            pointer-events: none;
            z-index: 50;
            box-shadow: 0 4px 16px rgba(0,0,0,0.6);
            backdrop-filter: blur(8px);
        }

        .chart-stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            background: rgba(0, 0, 0, 0.25);
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.72rem;
            color: var(--text-muted);
        }
        .stat-col span { color: #fff; font-weight: 700; margin-left: 3px; }

        /* Central Log Center */
        .log-center {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            flex: 1;
            min-height: 240px;
            width: 100%;
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
        }

        .log-filters {
            display: flex;
            gap: 5px;
            align-items: center;
            flex-wrap: wrap;
        }

        .filter-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 4px 9px;
            border-radius: 5px;
            font-size: 0.72rem;
        }
        .filter-btn.active {
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--accent-login);
            color: var(--accent-login);
            font-weight: 700;
        }

        .search-box {
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-glass);
            padding: 4px 9px;
            border-radius: 5px;
            color: #fff;
            font-size: 0.74rem;
            outline: none;
            width: 160px;
        }

        .log-console {
            background: #04060b;
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 6px;
            padding: 8px;
            flex: 1;
            overflow-y: auto;
            font-size: 0.74rem;
            line-height: 1.4;
            max-height: 260px;
            width: 100%;
            font-family: Consolas, "Courier New", monospace !important;
        }

        .log-line {
            display: flex;
            gap: 6px;
            padding: 2px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.015);
            align-items: flex-start;
        }

        .log-ts { color: #64748b; min-width: 68px; font-weight: 700; font-size: 0.7rem; }
        .log-badge {
            padding: 1px 4px;
            border-radius: 3px;
            font-size: 0.64rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .badge-login { background: rgba(56, 189, 248, 0.2); color: var(--accent-login); }
        .badge-game  { background: rgba(16, 185, 129, 0.2); color: var(--accent-game); }
        .badge-chat  { background: rgba(168, 85, 247, 0.2); color: var(--accent-chat); }
        .badge-launcher { background: rgba(234, 179, 8, 0.2); color: var(--accent-launcher); }

        .log-msg { color: #e2e8f0; word-break: break-all; flex: 1; }
        .log-msg.srv-login { color: #f1f5f9; }
        .log-msg.srv-game  { color: #a7f3d0; }
        .log-msg.srv-chat  { color: #e9d5ff; }
        .log-msg.srv-launcher { color: #fef08a; }

        /* Left Drawer Sidebar (Gaveta Lateral) */
        .drawer-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(6px);
            z-index: 1000;
            display: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .drawer-overlay.open { display: block; opacity: 1; }

        .drawer-sidebar {
            position: fixed;
            top: 0;
            left: 0;
            width: 380px;
            max-width: 88vw;
            height: 100vh;
            background: #0b111e;
            border-right: 1px solid var(--border-glass);
            z-index: 1001;
            transform: translateX(-100%);
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            box-shadow: 10px 0 40px rgba(0, 0, 0, 0.7);
        }
        .drawer-sidebar.open { transform: translateX(0); }

        .drawer-header {
            padding: 16px;
            background: rgba(15, 23, 42, 0.9);
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .drawer-title {
            font-size: 1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .drawer-close-btn {
            background: rgba(255, 255, 255, 0.08);
            border: none;
            color: var(--text-muted);
            width: 28px;
            height: 28px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .drawer-close-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.15); }

        .drawer-content {
            padding: 16px;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .drawer-section-title {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--accent-login);
            font-weight: 700;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .drawer-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-glass);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .drawer-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
        }
        .drawer-val { font-weight: 700; color: #fff; }

        /* Modal Dialogs */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(8px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }

        .modal-box {
            background: #0f172a;
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 20px;
            max-width: 440px;
            width: 90%;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .modal-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--accent-login);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .modal-text {
            font-size: 0.82rem;
            color: #cbd5e1;
            line-height: 1.45;
        }

        .qr-placeholder-box {
            background: #060910;
            border: 1px solid var(--border-glass);
            border-radius: 8px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }

        .url-copy-input {
            width: 100%;
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--border-glass);
            border-radius: 6px;
            padding: 6px 10px;
            color: #38bdf8;
            font-weight: 700;
            font-size: 0.82rem;
            text-align: center;
            outline: none;
        }

        /* Mobile Bottom Tab Bar (iOS Glass Style) */
        .mobile-bottom-bar {
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: calc(52px + var(--safe-bottom));
            padding-bottom: var(--safe-bottom);
            background: rgba(10, 16, 28, 0.94);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-top: 1px solid var(--border-glass);
            z-index: 100;
            justify-content: space-around;
            align-items: center;
        }

        .tab-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            color: var(--text-muted);
            font-size: 0.65rem;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 4px 8px;
            cursor: pointer;
        }
        .tab-btn.active { color: var(--accent-login); }

        .mobile-fab {
            display: none;
            position: fixed;
            bottom: calc(64px + var(--safe-bottom));
            right: 16px;
            width: 46px;
            height: 46px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            box-shadow: 0 4px 16px rgba(56, 189, 248, 0.45);
            color: #fff;
            border: none;
            align-items: center;
            justify-content: center;
            z-index: 99;
            cursor: pointer;
        }

        /* Mobile Responsive Adjustments */
        @media (max-width: 768px) {
            .cards-grid { grid-template-columns: 1fr; }
            .header-status-pills { display: none; }
            .mobile-bottom-bar { display: flex; }
            .mobile-fab { display: flex; }
            main { padding-bottom: calc(64px + var(--safe-bottom)); }
            .header-right .btn-start, .header-right .btn-stop, .header-right .btn-restart { display: none; }
            .chart-stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <!-- Top Header -->
    <header>
        <div class="header-left">
            <button class="drawer-toggle-btn" onclick="toggleDrawer(true)" title="Menu e Registradores">
                <span class="btn-svg"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></span>
            </button>
            <div class="brand-box">
                <div class="brand-icon">A</div>
                <div class="brand-text">EmuRust</div>
                <div class="brand-pill">Classic 4.5</div>
            </div>
            <div class="header-status-pills">
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-login"></div> Login</div>
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-game"></div> Game</div>
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-chat"></div> Chat</div>
            </div>
        </div>

        <div class="header-right">
            <button class="btn-start" onclick="startAll()">
                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span>
                INICIAR
            </button>
            <button class="btn-stop" onclick="stopAll()">
                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg></span>
                PARAR
            </button>
            <button class="btn-restart" onclick="restartAll()">
                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg></span>
                REINICIAR
            </button>
            <button class="btn-mobile-url" onclick="openMobileModal()" title="Acesso Mobile / LAN">
                <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></span>
                <span id="btn-mobile-label">Mobile LAN</span>
            </button>
            <button class="btn-secondary" onclick="toggleFullscreen()" title="Tela Cheia">
                <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg></span>
            </button>
            <button class="btn-danger" onclick="openShutdownModal()">
                <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18.36 6.64a9 9 0 1 1-12.73 0M12 2v10"/></svg></span>
            </button>
        </div>
    </header>

    <!-- Main Content -->
    <main>
        <!-- 3 Server Status Cards -->
        <div class="cards-grid">
            <!-- Login Server -->
            <div class="card" id="card-login">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-login"></div>
                        <div class="card-title">Login-Server</div>
                    </div>
                    <div class="card-tag">Portas: 2106 | 6600</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row">
                        <span class="metric-label">Status / Uptime:</span>
                        <span class="metric-value" id="val-uptime-login">OFFLINE</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">CPU:</span>
                        <span class="metric-value" id="val-cpu-login">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-login" id="bar-cpu-login"></div></div>
                    <div class="metric-row" style="margin-top: 3px;">
                        <span class="metric-label">Memória RAM:</span>
                        <span class="metric-value" id="val-mem-login">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-login" id="bar-mem-login"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('login', 'start')">Iniciar</button>
                    <button class="btn-stop" onclick="controlServer('login', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('login', 'restart')">Reiniciar</button>
                </div>
            </div>

            <!-- Game Server -->
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
                        <span class="metric-label">CPU:</span>
                        <span class="metric-value" id="val-cpu-game">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-game" id="bar-cpu-game"></div></div>
                    <div class="metric-row" style="margin-top: 3px;">
                        <span class="metric-label">Memória RAM:</span>
                        <span class="metric-value" id="val-mem-game">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-game" id="bar-mem-game"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('game', 'start')">Iniciar</button>
                    <button class="btn-stop" onclick="controlServer('game', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('game', 'restart')">Reiniciar</button>
                </div>
            </div>

            <!-- Chat Server -->
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
                        <span class="metric-label">CPU:</span>
                        <span class="metric-value" id="val-cpu-chat">0.0%</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-chat" id="bar-cpu-chat"></div></div>
                    <div class="metric-row" style="margin-top: 3px;">
                        <span class="metric-label">Memória RAM:</span>
                        <span class="metric-value" id="val-mem-chat">0.0 MB</span>
                    </div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-chat" id="bar-mem-chat"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('chat', 'start')">Iniciar</button>
                    <button class="btn-stop" onclick="controlServer('chat', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('chat', 'restart')">Reiniciar</button>
                </div>
            </div>
        </div>

        <!-- Day-Trade Real-Time Multi-Curve Telemetry Section -->
        <div class="daytrade-section" id="section-telemetry">
            <div class="daytrade-header">
                <div class="daytrade-title-box">
                    <span class="btn-svg" style="color: var(--accent-login);"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></span>
                    Telemetria Day-Trade Real-Time (Consumo por Subsistema)
                </div>

                <div class="daytrade-toggles">
                    <button class="mode-btn active" id="btn-mode-cpu" onclick="setChartMode('cpu')">Uso de CPU (%)</button>
                    <button class="mode-btn" id="btn-mode-mem" onclick="setChartMode('mem')">Memória RAM (MB)</button>
                </div>

                <div class="legend-bar">
                    <div class="legend-item" onclick="toggleSeries('login')"><div class="legend-line legend-login"></div> Login</div>
                    <div class="legend-item" onclick="toggleSeries('game')"><div class="legend-line legend-game"></div> Game</div>
                    <div class="legend-item" onclick="toggleSeries('chat')"><div class="legend-line legend-chat"></div> Chat</div>
                    <div class="legend-item" onclick="toggleSeries('launcher')"><div class="legend-line legend-launcher"></div> Launcher</div>
                    <div class="legend-item" onclick="toggleSeries('total')"><div class="legend-line legend-total"></div> Total</div>
                </div>
            </div>

            <div class="daytrade-canvas-container" id="chart-container">
                <canvas id="daytrade-canvas"></canvas>
                <div class="daytrade-tooltip" id="chart-tooltip"></div>
            </div>

            <div class="chart-stats-grid">
                <div class="stat-col">Mínimo:<span id="stat-min-val">0.0%</span></div>
                <div class="stat-col">Máximo:<span id="stat-max-val">0.0%</span></div>
                <div class="stat-col">Média:<span id="stat-avg-val">0.0%</span></div>
                <div class="stat-col">Tempo de Amostra:<span id="stat-sample-rate">1s Live</span></div>
            </div>
        </div>

        <!-- Central Live Logs Section -->
        <div class="log-center" id="section-logs">
            <div class="log-header">
                <div class="log-filters">
                    <span style="font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; gap: 5px;">
                        <span class="btn-svg" style="color: var(--accent-login);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></span>
                        LOGS UNIFICADOS:
                    </span>
                    <button class="filter-btn active" onclick="setFilter('srv', 'all', this)">Todos</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'login', this)">Login</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'game', this)">Game</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'chat', this)">Chat</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'launcher', this)">Launcher</button>
                </div>
                <div class="log-filters">
                    <input type="text" class="search-box" id="search-input" placeholder="Filtrar logs..." onkeyup="renderLogs()">
                    <button class="filter-btn" onclick="clearLogs()">Limpar</button>
                    <button class="filter-btn" id="pause-btn" onclick="togglePause()">Pausar</button>
                </div>
            </div>
            <div class="log-console" id="log-console"></div>
        </div>
    </main>

    <!-- Left Drawer Sidebar (Janela Gaveta Lateral) -->
    <div class="drawer-overlay" id="drawer-overlay" onclick="toggleDrawer(false)"></div>
    <div class="drawer-sidebar" id="drawer-sidebar">
        <div class="drawer-header">
            <div class="drawer-title">
                <span class="btn-svg" style="color: var(--accent-login);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></span>
                Menu & Registradores
            </div>
            <button class="drawer-close-btn" onclick="toggleDrawer(false)">✕</button>
        </div>

        <div class="drawer-content">
            <!-- Section: Acesso Mobile & LAN -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></span>
                    Acesso Mobile & Rede Local
                </div>
                <div class="drawer-card">
                    <div class="drawer-row">
                        <span style="color: var(--text-muted);">IP Local (LAN):</span>
                        <span class="drawer-val" id="reg-lan-ip">127.0.0.1</span>
                    </div>
                    <div class="drawer-row">
                        <span style="color: var(--text-muted);">URL do Painel:</span>
                        <span class="drawer-val" id="reg-ext-url" style="color: var(--accent-login); word-break: break-all;">http://127.0.0.1:18080</span>
                    </div>
                    <button class="btn-secondary" style="margin-top: 4px;" onclick="copyExternalUrl()">Copiar Link do Painel</button>
                </div>
            </div>

            <!-- Section: Registradores do Sistema -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></span>
                    Registradores & Telemetria
                </div>
                <div class="drawer-card">
                    <div class="drawer-row">
                        <span style="color: var(--text-muted);">Taxa de Tick (TPS):</span>
                        <span class="drawer-val" style="color: var(--accent-game);">20.0 / 20.0 TPS (Travado)</span>
                    </div>
                    <div class="drawer-row">
                        <span style="color: var(--text-muted);">Banco de Dados:</span>
                        <span class="drawer-val" id="reg-db-size">aion.db (0 KB)</span>
                    </div>
                    <div class="drawer-row">
                        <span style="color: var(--text-muted);">Memória Total do SO:</span>
                        <span class="drawer-val" id="reg-os-mem">0.0 / 0.0 GB</span>
                    </div>
                    <div class="drawer-row">
                        <span style="color: var(--text-muted);">Uptime do Launcher:</span>
                        <span class="drawer-val" id="reg-uptime">00:00:00</span>
                    </div>
                </div>
            </div>

            <!-- Section: Mapeamento de Portas -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></span>
                    Portas de Rede Ativas
                </div>
                <div class="drawer-card">
                    <div class="drawer-row"><span>Login Server:</span><span class="drawer-val" style="color: var(--accent-login);">2106 (TCP)</span></div>
                    <div class="drawer-row"><span>Game Server:</span><span class="drawer-val" style="color: var(--accent-game);">7777 (TCP)</span></div>
                    <div class="drawer-row"><span>Chat Server:</span><span class="drawer-val" style="color: var(--accent-chat);">10241 (TCP)</span></div>
                    <div class="drawer-row"><span>Gameforge STS:</span><span class="drawer-val">6600 (TCP)</span></div>
                    <div class="drawer-row"><span>HQ Auth:</span><span class="drawer-val">13001 (TCP)</span></div>
                    <div class="drawer-row"><span>Web Dashboard:</span><span class="drawer-val" style="color: var(--accent-launcher);">18080 (HTTP)</span></div>
                </div>
            </div>

            <!-- Section: Opções de Visualização -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
                    Visualização & Zoom
                </div>
                <div class="drawer-card" style="flex-direction: row; gap: 8px;">
                    <button class="btn-secondary" style="flex:1;" onclick="zoomFont(-1)">A- Diminuir</button>
                    <button class="btn-secondary" style="flex:1;" onclick="zoomFont(1)">A+ Aumentar</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Mobile Bottom Tab Bar (iOS Glassmorphism) -->
    <div class="mobile-bottom-bar">
        <button class="tab-btn active" onclick="scrollToSection('top')">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg></span>
            Status
        </button>
        <button class="tab-btn" onclick="scrollToSection('section-telemetry')">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></span>
            Gráfico
        </button>
        <button class="tab-btn" onclick="scrollToSection('section-logs')">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></span>
            Logs
        </button>
        <button class="tab-btn" onclick="toggleDrawer(true)">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></span>
            Menu
        </button>
    </div>

    <!-- Mobile FAB (Floating Action Button) -->
    <button class="mobile-fab" onclick="toggleDrawer(true)">
        <span class="btn-svg"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg></span>
    </button>

    <!-- Mobile Access Modal -->
    <div class="modal-overlay" id="mobile-modal">
        <div class="modal-box">
            <div class="modal-title">
                <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></span>
                Acesso Mobile no Celular / LAN
            </div>
            <div class="modal-text">
                Conecte seu celular na mesma rede Wi-Fi e acesse o endereço abaixo pelo navegador (Safari, Chrome, Firefox) para monitorar o emulador remotamente com visual estilo iOS:
            </div>
            <div class="qr-placeholder-box">
                <input type="text" class="url-copy-input" id="modal-url-input" readonly value="http://127.0.0.1:18080">
                <div style="font-size: 0.72rem; color: var(--text-muted); text-align: center;">Clique abaixo para copiar ou digite diretamente na barra do navegador do celular.</div>
            </div>
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
                <button class="btn-secondary" onclick="closeMobileModal()">Fechar</button>
                <button class="btn-start" onclick="copyExternalUrl()">Copiar Endereço</button>
            </div>
        </div>
    </div>

    <!-- Shutdown Modal -->
    <div class="modal-overlay" id="shutdown-modal">
        <div class="modal-box">
            <div class="modal-title" style="color: #f87171;">
                <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                Encerrar Emulador Rust
            </div>
            <div class="modal-text">
                Esta ação finalizará com segurança o Game Server, Login Server e Chat Server, liberando todas as portas de rede e encerrando o processo de forma limpa.
            </div>
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
                <button class="btn-secondary" onclick="closeShutdownModal()">Cancelar</button>
                <button class="btn-danger" onclick="confirmShutdown()">Confirmar Encerramento</button>
            </div>
        </div>
    </div>

    <script>
        let currentSrvFilter = 'all';
        let isPaused = false;
        let logBuffer = [];
        let historyData = [];
        let chartMode = 'cpu'; // 'cpu' or 'mem'
        let hiddenSeries = {};
        let currentFontScale = 1.0;
        let externalUrlStr = "http://127.0.0.1:18080";

        function setChartMode(mode) {
            chartMode = mode;
            document.getElementById('btn-mode-cpu').classList.toggle('active', mode === 'cpu');
            document.getElementById('btn-mode-mem').classList.toggle('active', mode === 'mem');
            drawDayTradeChart();
        }

        function toggleSeries(name) {
            hiddenSeries[name] = !hiddenSeries[name];
            drawDayTradeChart();
        }

        function toggleDrawer(open) {
            document.getElementById('drawer-overlay').classList.toggle('open', open);
            document.getElementById('drawer-sidebar').classList.toggle('open', open);
        }

        function openMobileModal() {
            document.getElementById('mobile-modal').style.display = 'flex';
        }

        function closeMobileModal() {
            document.getElementById('mobile-modal').style.display = 'none';
        }

        function copyExternalUrl() {
            navigator.clipboard.writeText(externalUrlStr).then(() => {
                alert("Endereço copiado para a área de transferência: " + externalUrlStr);
            }).catch(() => {
                prompt("Copie o endereço manualmente:", externalUrlStr);
            });
        }

        function zoomFont(delta) {
            currentFontScale = Math.min(Math.max(currentFontScale + (delta * 0.06), 0.8), 1.3);
            document.documentElement.style.setProperty('--font-scale', `${currentFontScale}rem`);
        }

        function toggleFullscreen() {
            fetch('/api/window/fullscreen', { method: 'POST' }).catch(() => {});
            if (!document.fullscreenElement) {
                if (document.documentElement.requestFullscreen) {
                    document.documentElement.requestFullscreen().catch(() => {});
                }
            } else if (document.exitFullscreen) {
                document.exitFullscreen().catch(() => {});
            }
        }

        function openShutdownModal() { document.getElementById('shutdown-modal').style.display = 'flex'; }
        function closeShutdownModal() { document.getElementById('shutdown-modal').style.display = 'none'; }

        async function confirmShutdown() {
            closeShutdownModal();
            try { await fetch('/api/shutdown', { method: 'POST' }); } catch (e) {}
        }

        function scrollToSection(id) {
            if (id === 'top') window.scrollTo({ top: 0, behavior: 'smooth' });
            else {
                const el = document.getElementById(id);
                if (el) el.scrollIntoView({ behavior: 'smooth' });
            }
        }

        // Fetch Metrics & Registers
        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();

                // 1. Update Server Cards & Mini Status Dots
                if (data.servers) {
                    data.servers.forEach(s => {
                        const dot = document.getElementById(`dot-${s.name}`);
                        const hdrDot = document.getElementById(`hdr-dot-${s.name}`);
                        const uptimeVal = document.getElementById(`val-uptime-${s.name}`);
                        const cpuVal = document.getElementById(`val-cpu-${s.name}`);
                        const cpuBar = document.getElementById(`bar-cpu-${s.name}`);
                        const memVal = document.getElementById(`val-mem-${s.name}`);
                        const memBar = document.getElementById(`bar-mem-${s.name}`);

                        const stateClass = s.status === 'Online' ? 'online' : (s.status === 'Starting' ? 'starting' : (s.status === 'Crashed' ? 'crashed' : ''));
                        if (dot) dot.className = 'status-dot ' + stateClass;
                        if (hdrDot) hdrDot.className = 'mini-dot ' + stateClass;

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

                // 2. Update System Registers in Drawer
                if (data.registers) {
                    const r = data.registers;
                    externalUrlStr = r.external_url;
                    document.getElementById('reg-lan-ip').innerText = r.lan_ip;
                    document.getElementById('reg-ext-url').innerText = r.external_url;
                    document.getElementById('modal-url-input').value = r.external_url;
                    document.getElementById('btn-mobile-label').innerText = `${r.lan_ip}:${r.http_port}`;
                    document.getElementById('reg-db-size').innerText = `aion.db (${(r.active_db_size_kb / 1024).toFixed(2)} MB)`;
                    document.getElementById('reg-os-mem').innerText = `${(r.os_used_memory_mb / 1024).toFixed(1)} / ${(r.os_total_memory_mb / 1024).toFixed(1)} GB`;
                }

                if (data.launcher_uptime_secs !== undefined) {
                    const u = data.launcher_uptime_secs;
                    const uHrs = Math.floor(u / 3600).toString().padStart(2, '0');
                    const uMins = Math.floor((u % 3600) / 60).toString().padStart(2, '0');
                    const uSecs = (u % 60).toString().padStart(2, '0');
                    document.getElementById('reg-uptime').innerText = `${uHrs}:${uMins}:${uSecs}`;
                }

                // 3. Process History Points & Draw Day-Trade Graph
                if (data.history && data.history.length > 0) {
                    historyData = data.history;
                    drawDayTradeChart();
                }
            } catch (e) {
                console.error("Error fetching metrics:", e);
            }
        }

        // Draw Day-Trade Financial Style Multi-Curve Graph
        function drawDayTradeChart() {
            const canvas = document.getElementById('daytrade-canvas');
            if (!canvas || !historyData || historyData.length < 2) return;

            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();

            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const w = rect.width;
            const h = rect.height;
            const padTop = 15;
            const padBottom = 15;
            const plotH = h - padTop - padBottom;

            ctx.clearRect(0, 0, w, h);

            // Compute Max Scale based on active mode
            let maxVal = chartMode === 'cpu' ? 100.0 : 250.0;
            if (chartMode === 'mem') {
                const maxInHist = Math.max(...historyData.map(d => d.total_mem_mb || 0));
                maxVal = Math.max(maxInHist * 1.25, 300.0);
            }

            // Draw Fibonacci Retracement Grid Lines
            const fibRatios = [
                { r: 1.0, label: chartMode === 'cpu' ? '100%' : `${maxVal.toFixed(0)}MB` },
                { r: 0.786, label: '78.6%' },
                { r: 0.618, label: '61.8%' },
                { r: 0.50, label: '50.0%' },
                { r: 0.382, label: '38.2%' },
                { r: 0.236, label: '23.6%' },
                { r: 0.0, label: '0.0%' }
            ];

            ctx.lineWidth = 1;
            ctx.font = '9px Arial';
            fibRatios.forEach(fib => {
                const y = h - padBottom - (fib.r * plotH);
                ctx.strokeStyle = fib.r === 0.618 ? 'rgba(234, 179, 8, 0.35)' : 'rgba(255, 255, 255, 0.05)';
                ctx.setLineDash(fib.r === 0.618 ? [4, 4] : [2, 4]);
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(w, y);
                ctx.stroke();

                ctx.fillStyle = fib.r === 0.618 ? '#eab308' : '#64748b';
                ctx.fillText(fib.label, 6, y - 3);
            });
            ctx.setLineDash([]);

            // Draw Multi-Curves
            const step = w / (historyData.length - 1);

            const seriesList = [
                { key: 'total', name: 'Total', color: '#ffffff', dash: [4, 3], val: d => chartMode === 'cpu' ? d.total_cpu : d.total_mem_mb },
                { key: 'login', name: 'Login', color: '#38bdf8', dash: [], val: d => chartMode === 'cpu' ? d.login_cpu : d.login_mem_mb },
                { key: 'game',  name: 'Game',  color: '#10b981', dash: [], val: d => chartMode === 'cpu' ? d.game_cpu : d.game_mem_mb },
                { key: 'chat',  name: 'Chat',  color: '#a855f7', dash: [], val: d => chartMode === 'cpu' ? d.chat_cpu : d.chat_mem_mb },
                { key: 'launcher', name: 'Launcher', color: '#eab308', dash: [], val: d => chartMode === 'cpu' ? d.launcher_cpu : d.launcher_mem_mb }
            ];

            seriesList.forEach(s => {
                if (hiddenSeries[s.key]) return;

                ctx.beginPath();
                ctx.strokeStyle = s.color;
                ctx.lineWidth = s.key === 'total' ? 2 : 1.8;
                ctx.setLineDash(s.dash);

                historyData.forEach((d, i) => {
                    const val = s.val(d) || 0;
                    const norm = Math.min(Math.max(val / maxVal, 0), 1);
                    const x = i * step;
                    const y = h - padBottom - (norm * plotH);

                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                });
                ctx.stroke();
            });

            ctx.setLineDash([]);

            // Update stats summary on bottom
            const totals = historyData.map(d => chartMode === 'cpu' ? d.total_cpu : d.total_mem_mb);
            const minV = Math.min(...totals);
            const maxV = Math.max(...totals);
            const avgV = totals.reduce((a, b) => a + b, 0) / totals.length;
            const unit = chartMode === 'cpu' ? '%' : ' MB';

            document.getElementById('stat-min-val').innerText = `${minV.toFixed(1)}${unit}`;
            document.getElementById('stat-max-val').innerText = `${maxV.toFixed(1)}${unit}`;
            document.getElementById('stat-avg-val').innerText = `${avgV.toFixed(1)}${unit}`;
        }

        // Live Log Stream
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
