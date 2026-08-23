pub const HTML_DASHBOARD: &str = r##"<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Aion Classic - EmuRust Dashboard</title>
    <style>
        :root {
            --bg-base: #060910;
            --bg-surface: #0c121e;
            --bg-card: rgba(13, 20, 36, 0.88);
            --bg-card-hover: rgba(20, 30, 54, 0.95);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(56, 189, 248, 0.25);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-login: #38bdf8;
            --accent-game: #10b981;
            --accent-chat: #a855f7;
            --accent-launcher: #eab308;
            --accent-red: #ef4444;
            --font-scale: 1rem;
            --safe-bottom: env(safe-area-inset-bottom, 0px);
            --safe-top: env(safe-area-inset-top, 0px);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        }

        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at 85% 10%, #111a33 0%, #060910 80%);
            color: var(--text-main);
            overflow: hidden;
            font-size: var(--font-scale);
            display: flex;
            flex-direction: column;
        }

        /* Slim Minimal Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: calc(6px + var(--safe-top)) 16px 6px 16px;
            background: rgba(8, 12, 22, 0.92);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-glass);
            z-index: 100;
            width: 100%;
            height: calc(44px + var(--safe-top));
            flex-shrink: 0;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }

        .drawer-toggle-btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-glass);
            color: var(--text-main);
            width: 30px;
            height: 30px;
            border-radius: 7px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        .drawer-toggle-btn:active, .drawer-toggle-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: var(--accent-login);
        }

        .brand-box {
            display: flex;
            align-items: center;
            gap: 7px;
            min-width: 0;
        }

        .brand-icon {
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 13px;
            color: #fff;
            box-shadow: 0 2px 8px rgba(56, 189, 248, 0.35);
            flex-shrink: 0;
        }

        .brand-text {
            font-size: 0.88rem;
            font-weight: 700;
            letter-spacing: -0.3px;
            white-space: nowrap;
        }

        .brand-pill {
            font-size: 0.65rem;
            padding: 2px 5px;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-login);
            border-radius: 4px;
            font-weight: 600;
            white-space: nowrap;
        }

        .header-status-pills {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 0, 0, 0.35);
            padding: 3px 8px;
            border-radius: 20px;
            border: 1px solid var(--border-glass);
            flex-shrink: 0;
        }

        .mini-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--accent-red);
            transition: all 0.3s;
            display: inline-block;
        }
        .mini-dot.online { background: var(--accent-game); box-shadow: 0 0 6px var(--accent-game); }
        .mini-dot.starting { background: var(--accent-launcher); box-shadow: 0 0 6px var(--accent-launcher); }
        .mini-dot.crashed { background: #e11d48; box-shadow: 0 0 8px #e11d48; }

        .mini-stat-label {
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-shrink: 0;
        }

        /* Simple Host:Port Text Display */
        .lan-text-badge {
            font-size: 0.72rem;
            color: var(--text-muted);
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-glass);
            padding: 3px 8px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .lan-text-badge:hover {
            color: var(--accent-login);
            border-color: var(--border-glow);
        }
        .lan-text-badge b { color: #fff; }

        button {
            font-size: 0.74rem;
            font-weight: 600;
            padding: 5px 9px;
            border-radius: 6px;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            white-space: nowrap;
        }

        .btn-svg {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 13px;
            height: 13px;
            flex-shrink: 0;
        }

        .btn-start {
            background: linear-gradient(135deg, #059669, #10b981);
            color: #fff;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
        }
        .btn-start:active, .btn-start:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4); }

        .btn-stop {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #fca5a5;
        }
        .btn-stop:active, .btn-stop:hover { background: rgba(239, 68, 68, 0.25); transform: translateY(-1px); }

        .btn-restart {
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.4);
            color: #7dd3fc;
        }
        .btn-restart:active, .btn-restart:hover { background: rgba(56, 189, 248, 0.25); transform: translateY(-1px); }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid var(--border-glass);
            color: #e2e8f0;
        }
        .btn-secondary:active, .btn-secondary:hover { background: rgba(255, 255, 255, 0.14); }

        .btn-danger {
            background: linear-gradient(135deg, #dc2626, #ef4444);
            color: #fff;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
        }
        .btn-danger:active, .btn-danger:hover { box-shadow: 0 4px 12px rgba(239, 68, 68, 0.5); transform: translateY(-1px); }

        /* Main Layout */
        main {
            flex: 1;
            padding: 10px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            width: 100%;
            max-width: 100%;
            min-height: 0;
            overflow: hidden;
        }

        /* 3 Server Cards Grid */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            width: 100%;
            flex-shrink: 0;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 9px;
            padding: 10px 12px;
            backdrop-filter: blur(16px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            gap: 8px;
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
        .card-login::before { background: linear-gradient(90deg, transparent, var(--accent-login), transparent); }
        .card-game::before  { background: linear-gradient(90deg, transparent, var(--accent-game), transparent); }
        .card-chat::before  { background: linear-gradient(90deg, transparent, var(--accent-chat), transparent); }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title-box {
            display: flex;
            align-items: center;
            gap: 7px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-red);
            box-shadow: 0 0 7px var(--accent-red);
            transition: all 0.3s;
            display: inline-block;
        }
        .status-dot.online { background: var(--accent-game); box-shadow: 0 0 7px var(--accent-game); }
        .status-dot.starting { background: var(--accent-launcher); box-shadow: 0 0 7px var(--accent-launcher); }
        .status-dot.crashed { background: #e11d48; box-shadow: 0 0 9px #e11d48; }

        .card-title {
            font-size: 0.86rem;
            font-weight: 700;
        }

        .card-tag {
            font-size: 0.65rem;
            padding: 2px 5px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-muted);
            font-weight: 600;
        }

        .metrics-box {
            display: flex;
            flex-direction: column;
            gap: 4px;
            background: rgba(0, 0, 0, 0.25);
            padding: 6px 8px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.74rem;
        }

        .metric-label { color: var(--text-muted); }
        .metric-value { font-weight: 700; color: #ffffff; }

        .progress-bar-bg {
            width: 100%;
            height: 3.5px;
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
        .fill-game  { background: linear-gradient(90deg, #059669, #10b981); }
        .fill-chat  { background: linear-gradient(90deg, #7c3aed, #a855f7); }

        .card-actions {
            display: flex;
            gap: 5px;
            margin-top: auto;
        }

        .card-actions button {
            flex: 1;
            padding: 4px;
            font-size: 0.7rem;
        }

        /* Clean Real-Time Day-Trade Fibonacci Telemetry Section */
        .telemetry-section {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            padding: 8px 12px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            gap: 6px;
            width: 100%;
            flex-shrink: 0;
        }

        .telemetry-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
        }

        .telemetry-title-box {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--accent-login);
        }

        .telemetry-controls-row {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .toggle-group {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.35);
            padding: 2px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .mode-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.68rem;
            cursor: pointer;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .mode-btn.active {
            background: rgba(56, 189, 248, 0.25);
            color: var(--accent-login);
            font-weight: 700;
        }

        .legend-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.68rem;
            flex-wrap: wrap;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            padding: 2px 6px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            white-space: nowrap;
        }

        .legend-line {
            width: 12px;
            height: 3px;
            border-radius: 2px;
            flex-shrink: 0;
        }

        /* Day-Trade Multi-Curve Canvas */
        .chart-visual-container {
            position: relative;
            width: 100%;
            height: 125px;
            background: #050810;
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 6px;
            overflow: hidden;
        }

        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }

        .chart-stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
            background: rgba(0, 0, 0, 0.25);
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.68rem;
            color: var(--text-muted);
        }
        .stat-col span { color: #fff; font-weight: 700; margin-left: 3px; }

        /* Central Log Center */
        .log-center {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 10px;
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
            flex: 1;
            min-height: 0;
            width: 100%;
            overflow: hidden;
        }

        .log-header {
            display: flex;
            flex-direction: column;
            gap: 6px;
            width: 100%;
            flex-shrink: 0;
        }

        .log-header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 6px;
        }

        .log-filter-scroll-row {
            display: flex;
            gap: 4px;
            overflow-x: auto;
            white-space: nowrap;
            padding-bottom: 2px;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }
        .log-filter-scroll-row::-webkit-scrollbar { display: none; }

        .filter-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.7rem;
            flex-shrink: 0;
        }
        .filter-btn.active {
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--accent-login);
            color: var(--accent-login);
            font-weight: 700;
        }

        .log-controls-row {
            display: flex;
            gap: 6px;
            align-items: center;
            width: 100%;
        }

        .search-box {
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-glass);
            padding: 4px 8px;
            border-radius: 5px;
            color: #fff;
            font-size: 0.72rem;
            outline: none;
            flex: 1;
            min-width: 0;
        }

        .log-console {
            background: #04060b;
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 6px;
            padding: 8px;
            flex: 1;
            height: 100%;
            max-height: none;
            min-height: 0;
            overflow-y: auto;
            font-size: 0.72rem;
            line-height: 1.4;
            width: 100%;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
            -webkit-overflow-scrolling: touch;
        }

        .log-line {
            display: flex;
            gap: 6px;
            padding: 2px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.015);
            align-items: flex-start;
        }

        .log-ts { color: #64748b; min-width: 64px; font-weight: 600; font-size: 0.68rem; flex-shrink: 0; }
        .log-badge {
            padding: 1px 4px;
            border-radius: 3px;
            font-size: 0.62rem;
            font-weight: 700;
            text-transform: uppercase;
            flex-shrink: 0;
        }

        .badge-login { background: rgba(56, 189, 248, 0.2); color: var(--accent-login); }
        .badge-game  { background: rgba(16, 185, 129, 0.2); color: var(--accent-game); }
        .badge-chat  { background: rgba(168, 85, 247, 0.2); color: var(--accent-chat); }
        .badge-launcher { background: rgba(234, 179, 8, 0.2); color: var(--accent-launcher); }

        .log-msg {
            color: #e2e8f0;
            word-break: break-word;
            overflow-wrap: anywhere;
            flex: 1;
        }
        .log-msg.srv-login { color: #f1f5f9; }
        .log-msg.srv-game  { color: #a7f3d0; }
        .log-msg.srv-chat  { color: #e9d5ff; }
        .log-msg.srv-launcher { color: #fef08a; }

        /* Left Drawer Sidebar */
        .drawer-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
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
            max-width: 90vw;
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
            padding: calc(14px + var(--safe-top)) 16px 14px 16px;
            background: rgba(15, 23, 42, 0.92);
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .drawer-title {
            font-size: 0.92rem;
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
        .drawer-close-btn:active, .drawer-close-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.15); }

        .drawer-content {
            padding: 14px 16px calc(24px + var(--safe-bottom)) 16px;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 14px;
            -webkit-overflow-scrolling: touch;
        }

        .drawer-section-title {
            font-size: 0.72rem;
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
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 7px;
        }

        .drawer-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.78rem;
        }
        .drawer-val { font-weight: 700; color: #fff; }

        /* Mobile Bottom Tab Bar */
        .mobile-bottom-bar {
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: calc(50px + var(--safe-bottom));
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
            gap: 2px;
            color: var(--text-muted);
            font-size: 0.64rem;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 3px 8px;
            cursor: pointer;
            flex: 1;
        }
        .tab-btn.active { color: var(--accent-login); }

        .mobile-fab {
            display: none;
            position: fixed;
            bottom: calc(58px + var(--safe-bottom));
            right: 14px;
            width: 44px;
            height: 44px;
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

        /* Mobile Responsive */
        @media (max-width: 768px) {
            html, body {
                overflow-y: auto !important;
                height: auto !important;
            }
            .cards-grid { display: none !important; }
            .header-status-pills { display: flex; }
            .header-status-pills .mini-stat-label span { display: none; }
            .lan-text-badge { display: none !important; }
            
            .mobile-bottom-bar { display: flex; }
            .mobile-fab { display: flex; }
            
            main {
                padding: 10px 12px calc(62px + var(--safe-bottom)) 12px;
                gap: 10px;
                overflow: visible !important;
                flex: initial !important;
            }
            
            .telemetry-section { padding: 8px 10px; }
            .chart-visual-container { height: 130px; }
            .chart-stats-grid { grid-template-columns: repeat(2, 1fr); font-size: 0.68rem; }
            
            .log-center {
                padding: 10px 12px;
                min-height: 280px;
                flex: initial !important;
            }
            .log-console { max-height: 320px; height: 320px; }
        }
    </style>
</head>
<body>
    <!-- Top Header -->
    <header>
        <div class="header-left">
            <button class="drawer-toggle-btn" onclick="toggleDrawer(true)" title="Menu e Servidores">
                <span class="btn-svg"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></span>
            </button>
            <div class="brand-box">
                <div class="brand-icon">A</div>
                <div class="brand-text">EmuRust</div>
                <div class="brand-pill">Classic 4.5</div>
            </div>
            <div class="header-status-pills">
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-login"></div> <span>Login</span></div>
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-game"></div> <span>Game</span></div>
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-chat"></div> <span>Chat</span></div>
            </div>
        </div>

        <div class="header-right">
            <!-- Plain Host:Port Text Display (Copy on click) -->
            <div class="lan-text-badge" onclick="copyExternalUrl()" title="Clique para copiar o endereço do painel">
                <span class="btn-svg" style="color: var(--accent-login);"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></span>
                <span>Web: <b id="hdr-lan-ip">127.0.0.1:18080</b></span>
            </div>

            <button class="btn-secondary" onclick="toggleFullscreen()" title="Tela Cheia">
                <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg></span>
            </button>
            <button class="btn-danger" onclick="openShutdownModal()" title="Encerrar Emulador">
                <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18.36 6.64a9 9 0 1 1-12.73 0M12 2v10"/></svg></span>
            </button>
        </div>
    </header>

    <!-- Main Content -->
    <main>
        <!-- Desktop 3 Server Cards -->
        <div class="cards-grid">
            <!-- Login Server -->
            <div class="card card-login" id="card-login">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-login"></div>
                        <div class="card-title">Login-Server</div>
                    </div>
                    <div class="card-tag">Porta 2106</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row"><span class="metric-label">Status / Uptime:</span><span class="metric-value" id="val-uptime-login">OFFLINE</span></div>
                    <div class="metric-row"><span class="metric-label">CPU:</span><span class="metric-value" id="val-cpu-login">0.0%</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-login" id="bar-cpu-login"></div></div>
                    <div class="metric-row" style="margin-top: 2px;"><span class="metric-label">Memória RAM:</span><span class="metric-value" id="val-mem-login">0.0 MB</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-login" id="bar-mem-login"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('login', 'start')">Iniciar</button>
                    <button class="btn-stop" onclick="controlServer('login', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('login', 'restart')">Reiniciar</button>
                </div>
            </div>

            <!-- Game Server -->
            <div class="card card-game" id="card-game">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-game"></div>
                        <div class="card-title">Game-Server</div>
                    </div>
                    <div class="card-tag">Porta 7777</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row"><span class="metric-label">Status / Uptime:</span><span class="metric-value" id="val-uptime-game">OFFLINE</span></div>
                    <div class="metric-row"><span class="metric-label">CPU:</span><span class="metric-value" id="val-cpu-game">0.0%</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-game" id="bar-cpu-game"></div></div>
                    <div class="metric-row" style="margin-top: 2px;"><span class="metric-label">Memória RAM:</span><span class="metric-value" id="val-mem-game">0.0 MB</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-game" id="bar-mem-game"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('game', 'start')">Iniciar</button>
                    <button class="btn-stop" onclick="controlServer('game', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('game', 'restart')">Reiniciar</button>
                </div>
            </div>

            <!-- Chat Server -->
            <div class="card card-chat" id="card-chat">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot" id="dot-chat"></div>
                        <div class="card-title">Chat-Server</div>
                    </div>
                    <div class="card-tag">Porta 10241</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row"><span class="metric-label">Status / Uptime:</span><span class="metric-value" id="val-uptime-chat">OFFLINE</span></div>
                    <div class="metric-row"><span class="metric-label">CPU:</span><span class="metric-value" id="val-cpu-chat">0.0%</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-chat" id="bar-cpu-chat"></div></div>
                    <div class="metric-row" style="margin-top: 2px;"><span class="metric-label">Memória RAM:</span><span class="metric-value" id="val-mem-chat">0.0 MB</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-chat" id="bar-mem-chat"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-start" onclick="controlServer('chat', 'start')">Iniciar</button>
                    <button class="btn-stop" onclick="controlServer('chat', 'stop')">Parar</button>
                    <button class="btn-restart" onclick="controlServer('chat', 'restart')">Reiniciar</button>
                </div>
            </div>
        </div>

        <!-- Real-Time Day-Trade Fibonacci Multi-Curve Telemetry Section -->
        <div class="telemetry-section" id="section-telemetry">
            <div class="telemetry-header">
                <div class="telemetry-title-box">
                    <span class="btn-svg"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></span>
                    <span>Telemetria em Tempo Real (Day-Trade Fibonacci)</span>
                </div>

                <div class="telemetry-controls-row">
                    <div class="legend-bar" id="legend-bar-container">
                        <div class="legend-item"><div class="legend-line" style="background:#ffffff; border-top:1px dashed #ffffff;"></div><span>Total</span></div>
                        <div class="legend-item"><div class="legend-line" style="background:#38bdf8;"></div><span>Login</span></div>
                        <div class="legend-item"><div class="legend-line" style="background:#10b981;"></div><span>Game</span></div>
                        <div class="legend-item"><div class="legend-line" style="background:#a855f7;"></div><span>Chat</span></div>
                        <div class="legend-item"><div class="legend-line" style="background:#eab308;"></div><span>Launcher</span></div>
                    </div>

                    <!-- Metric Switcher: CPU % vs RAM MB -->
                    <div class="toggle-group">
                        <button class="mode-btn active" id="btn-mode-cpu" onclick="setChartMetric('cpu')">CPU (%)</button>
                        <button class="mode-btn" id="btn-mode-mem" onclick="setChartMetric('mem')">RAM (MB)</button>
                    </div>
                </div>
            </div>

            <!-- Canvas Chart -->
            <div class="chart-visual-container" id="chart-container">
                <canvas id="telemetry-canvas"></canvas>
            </div>

            <div class="chart-stats-grid">
                <div class="stat-col">Foco:<span>Servidores (Total)</span></div>
                <div class="stat-col">Mínimo:<span id="stat-min-val">0.0%</span></div>
                <div class="stat-col">Máximo:<span id="stat-max-val">0.0%</span></div>
                <div class="stat-col">Amostragem:<span>1s Contínua</span></div>
            </div>
        </div>

        <!-- Central Live Logs Section -->
        <div class="log-center" id="section-logs">
            <div class="log-header">
                <div class="log-header-top">
                    <span style="font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; gap: 5px;">
                        <span class="btn-svg" style="color: var(--accent-login);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></span>
                        LOGS UNIFICADOS (LOGIN, GAME, CHAT, LAUNCHER)
                    </span>
                    <div style="display: flex; gap: 5px;">
                        <button class="filter-btn" onclick="clearLogs()">Limpar</button>
                        <button class="filter-btn" id="pause-btn" onclick="togglePause()">Pausar</button>
                    </div>
                </div>

                <div class="log-filter-scroll-row">
                    <button class="filter-btn active" onclick="setFilter('srv', 'all', this)">Todos</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'login', this)">Login</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'game', this)">Game</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'chat', this)">Chat</button>
                    <button class="filter-btn" onclick="setFilter('srv', 'launcher', this)">Launcher</button>
                </div>

                <div class="log-controls-row">
                    <input type="text" class="search-box" id="search-input" placeholder="Buscar nos logs em tempo real..." onkeyup="renderLogs()">
                </div>
            </div>
            <div class="log-console" id="log-console"></div>
        </div>
    </main>

    <!-- Left Drawer Sidebar -->
    <div class="drawer-overlay" id="drawer-overlay" onclick="toggleDrawer(false)"></div>
    <div class="drawer-sidebar" id="drawer-sidebar">
        <div class="drawer-header">
            <div class="drawer-title">
                <span class="btn-svg" style="color: var(--accent-login);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg></span>
                Menu e Gestão de Servidores
            </div>
            <button class="drawer-close-btn" onclick="toggleDrawer(false)">✕</button>
        </div>

        <div class="drawer-content">
            <!-- Section: Ações Mestres -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg></span>
                    Controles Mestres
                </div>
                <div style="display: flex; gap: 6px;">
                    <button class="btn-start" style="flex:1;" onclick="startAll()">Iniciar Todos</button>
                    <button class="btn-stop" style="flex:1;" onclick="stopAll()">Parar Todos</button>
                    <button class="btn-restart" style="flex:1;" onclick="restartAll()">Reiniciar</button>
                </div>
            </div>

            <!-- Section: Servidores Individuais -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg></span>
                    Servidores
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div class="drawer-card">
                        <div class="drawer-row"><span style="font-weight: 700; display: flex; align-items: center; gap: 6px;"><span class="status-dot" id="drawer-dot-login"></span> Login-Server</span><span class="drawer-val" id="drawer-uptime-login" style="font-size: 0.72rem; color: var(--accent-login);">OFFLINE</span></div>
                        <div class="drawer-row" style="font-size: 0.72rem; color: var(--text-muted);"><span>CPU: <b id="drawer-cpu-login" style="color:#fff;">0.0%</b></span><span>RAM: <b id="drawer-mem-login" style="color:#fff;">0.0 MB</b></span></div>
                        <div style="display: flex; gap: 4px; margin-top: 2px;">
                            <button class="btn-start" style="flex:1; padding: 4px;" onclick="controlServer('login', 'start')">Iniciar</button>
                            <button class="btn-stop" style="flex:1; padding: 4px;" onclick="controlServer('login', 'stop')">Parar</button>
                            <button class="btn-restart" style="flex:1; padding: 4px;" onclick="controlServer('login', 'restart')">Reiniciar</button>
                        </div>
                    </div>

                    <div class="drawer-card">
                        <div class="drawer-row"><span style="font-weight: 700; display: flex; align-items: center; gap: 6px;"><span class="status-dot" id="drawer-dot-game"></span> Game-Server</span><span class="drawer-val" id="drawer-uptime-game" style="font-size: 0.72rem; color: var(--accent-game);">OFFLINE</span></div>
                        <div class="drawer-row" style="font-size: 0.72rem; color: var(--text-muted);"><span>CPU: <b id="drawer-cpu-game" style="color:#fff;">0.0%</b></span><span>RAM: <b id="drawer-mem-game" style="color:#fff;">0.0 MB</b></span></div>
                        <div style="display: flex; gap: 4px; margin-top: 2px;">
                            <button class="btn-start" style="flex:1; padding: 4px;" onclick="controlServer('game', 'start')">Iniciar</button>
                            <button class="btn-stop" style="flex:1; padding: 4px;" onclick="controlServer('game', 'stop')">Parar</button>
                            <button class="btn-restart" style="flex:1; padding: 4px;" onclick="controlServer('game', 'restart')">Reiniciar</button>
                        </div>
                    </div>

                    <div class="drawer-card">
                        <div class="drawer-row"><span style="font-weight: 700; display: flex; align-items: center; gap: 6px;"><span class="status-dot" id="drawer-dot-chat"></span> Chat-Server</span><span class="drawer-val" id="drawer-uptime-chat" style="font-size: 0.72rem; color: var(--accent-chat);">OFFLINE</span></div>
                        <div class="drawer-row" style="font-size: 0.72rem; color: var(--text-muted);"><span>CPU: <b id="drawer-cpu-chat" style="color:#fff;">0.0%</b></span><span>RAM: <b id="drawer-mem-chat" style="color:#fff;">0.0 MB</b></span></div>
                        <div style="display: flex; gap: 4px; margin-top: 2px;">
                            <button class="btn-start" style="flex:1; padding: 4px;" onclick="controlServer('chat', 'start')">Iniciar</button>
                            <button class="btn-stop" style="flex:1; padding: 4px;" onclick="controlServer('chat', 'stop')">Parar</button>
                            <button class="btn-restart" style="flex:1; padding: 4px;" onclick="controlServer('chat', 'restart')">Reiniciar</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section: Acesso Mobile & LAN -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></span>
                    Acesso Mobile & Rede Local
                </div>
                <div class="drawer-card">
                    <div class="drawer-row"><span style="color: var(--text-muted);">IP Local (LAN):</span><span class="drawer-val" id="reg-lan-ip">127.0.0.1</span></div>
                    <div class="drawer-row"><span style="color: var(--text-muted);">URL do Painel:</span><span class="drawer-val" id="reg-ext-url" style="color: var(--accent-login); word-break: break-all;">http://127.0.0.1:18080</span></div>
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
                    <div class="drawer-row"><span style="color: var(--text-muted);">Taxa de Tick (TPS):</span><span class="drawer-val" style="color: var(--accent-game);">20.0 / 20.0 TPS (Fixo)</span></div>
                    <div class="drawer-row"><span style="color: var(--text-muted);">Banco de Dados:</span><span class="drawer-val" id="reg-db-size">aion.db (0 KB)</span></div>
                    <div class="drawer-row"><span style="color: var(--text-muted);">Memória Total do SO:</span><span class="drawer-val" id="reg-os-mem">0.0 / 0.0 GB</span></div>
                    <div class="drawer-row"><span style="color: var(--text-muted);">Uptime do Launcher:</span><span class="drawer-val" id="reg-uptime">00:00:00</span></div>
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
        </div>
    </div>

    <!-- Mobile Bottom Tab Bar -->
    <div class="mobile-bottom-bar">
        <button class="tab-btn active" id="tab-btn-telemetry" onclick="switchMobileTab('telemetry')">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></span>
            Gráfico
        </button>
        <button class="tab-btn" id="tab-btn-logs" onclick="switchMobileTab('logs')">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></span>
            Logs
        </button>
        <button class="tab-btn" id="tab-btn-servers" onclick="switchMobileTab('servers')">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg></span>
            Servidores
        </button>
        <button class="tab-btn" id="tab-btn-menu" onclick="switchMobileTab('menu')">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg></span>
            Menu
        </button>
    </div>

    <!-- Mobile FAB -->
    <button class="mobile-fab" onclick="toggleDrawer(true)" title="Menu e Servidores">
        <span class="btn-svg"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg></span>
    </button>

    <!-- Shutdown Modal -->
    <div class="modal-overlay" id="shutdown-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.7); backdrop-filter:blur(8px); z-index:2000; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:20px; width:90%; max-width:400px; display:flex; flex-direction:column; gap:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#f87171; display:flex; align-items:center; gap:8px;">
                <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                Encerrar Emulador Rust
            </div>
            <div style="color:var(--text-muted); font-size:0.78rem; line-height:1.4;">Esta ação finalizará com segurança o Game Server, Login Server e Chat Server, liberando todas as portas de rede.</div>
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeShutdownModal()">Cancelar</button>
                <button class="btn-danger" onclick="confirmShutdown()">Confirmar</button>
            </div>
        </div>
    </div>

    <script>
        let currentSrvFilter = 'all';
        let isPaused = false;
        let logBuffer = [];
        let historyData = [];
        let rawDashboardState = null;
        let chartMetric = 'cpu'; // 'cpu' or 'mem'
        let externalUrlStr = "http://127.0.0.1:18080";

        // Day-Trade Series Definitions
        const serverSeriesDefs = [
            { key: 'total', name: 'Total', color: '#ffffff', dash: [4, 3], val: d => chartMetric === 'cpu' ? d.total_cpu : d.total_mem_mb },
            { key: 'login', name: 'Login', color: '#38bdf8', dash: [], val: d => chartMetric === 'cpu' ? d.login_cpu : d.login_mem_mb },
            { key: 'game',  name: 'Game',  color: '#10b981', dash: [], val: d => chartMetric === 'cpu' ? d.game_cpu : d.game_mem_mb },
            { key: 'chat',  name: 'Chat',  color: '#a855f7', dash: [], val: d => chartMetric === 'cpu' ? d.chat_cpu : d.chat_mem_mb },
            { key: 'launcher', name: 'Launcher', color: '#eab308', dash: [], val: d => chartMetric === 'cpu' ? d.launcher_cpu : d.launcher_mem_mb }
        ];

        function setChartMetric(metric) {
            chartMetric = metric;
            document.getElementById('btn-mode-cpu').classList.toggle('active', metric === 'cpu');
            document.getElementById('btn-mode-mem').classList.toggle('active', metric === 'mem');
            drawDayTradeChart();
        }

        // Draw Day-Trade Multi-Curve Chart with Fibonacci levels
        function drawDayTradeChart() {
            const canvas = document.getElementById('telemetry-canvas');
            if (!canvas || !historyData || historyData.length < 2) return;

            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();

            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const w = rect.width;
            const h = rect.height;
            const padTop = 8;
            const padBottom = 8;
            const plotH = h - padTop - padBottom;

            ctx.clearRect(0, 0, w, h);

            let maxVal = chartMetric === 'cpu' ? 100.0 : 250.0;
            if (chartMetric === 'mem') {
                const maxInHist = Math.max(...historyData.map(d => {
                    return Math.max(...serverSeriesDefs.map(s => s.val(d) || 0));
                }));
                maxVal = Math.max(maxInHist * 1.3, 50.0);
            }

            const fibRatios = [
                { r: 1.0, label: chartMetric === 'cpu' ? '100%' : `${maxVal.toFixed(0)}MB` },
                { r: 0.618, label: '61.8%' },
                { r: 0.382, label: '38.2%' },
                { r: 0.0, label: '0.0%' }
            ];

            ctx.lineWidth = 1;
            ctx.font = '8px -apple-system, sans-serif';
            fibRatios.forEach(fib => {
                const y = h - padBottom - (fib.r * plotH);
                ctx.strokeStyle = fib.r === 0.618 ? 'rgba(234, 179, 8, 0.3)' : 'rgba(255, 255, 255, 0.04)';
                ctx.setLineDash(fib.r === 0.618 ? [4, 4] : [2, 4]);
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(w, y);
                ctx.stroke();

                ctx.fillStyle = fib.r === 0.618 ? '#eab308' : '#64748b';
                ctx.fillText(fib.label, 4, y - 2);
            });
            ctx.setLineDash([]);

            const step = w / (historyData.length - 1);
            serverSeriesDefs.forEach(s => {
                ctx.beginPath();
                ctx.strokeStyle = s.color;
                ctx.lineWidth = s.key === 'total' ? 2 : 1.7;
                ctx.setLineDash(s.dash || []);

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

            const totals = historyData.map(d => chartMetric === 'cpu' ? d.total_cpu : d.total_mem_mb);
            const minV = Math.min(...totals);
            const maxV = Math.max(...totals);
            const unit = chartMetric === 'cpu' ? '%' : ' MB';

            document.getElementById('stat-min-val').innerText = `${minV.toFixed(1)}${unit}`;
            document.getElementById('stat-max-val').innerText = `${maxV.toFixed(1)}${unit}`;
        }

        // Fetch Metrics & Update UI
        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                rawDashboardState = data;

                // 1. Update Server Cards
                if (data.servers) {
                    data.servers.forEach(s => {
                        const stateClass = s.status === 'Online' ? 'online' : (s.status === 'Starting' ? 'starting' : (s.status === 'Crashed' ? 'crashed' : ''));
                        
                        const dot = document.getElementById(`dot-${s.name}`);
                        const uptimeVal = document.getElementById(`val-uptime-${s.name}`);
                        const cpuVal = document.getElementById(`val-cpu-${s.name}`);
                        const cpuBar = document.getElementById(`bar-cpu-${s.name}`);
                        const memVal = document.getElementById(`val-mem-${s.name}`);
                        const memBar = document.getElementById(`bar-mem-${s.name}`);

                        const hdrDot = document.getElementById(`hdr-dot-${s.name}`);
                        const drawerDot = document.getElementById(`drawer-dot-${s.name}`);
                        const drawerUptime = document.getElementById(`drawer-uptime-${s.name}`);
                        const drawerCpu = document.getElementById(`drawer-cpu-${s.name}`);
                        const drawerMem = document.getElementById(`drawer-mem-${s.name}`);

                        if (dot) dot.className = 'status-dot ' + stateClass;
                        if (hdrDot) hdrDot.className = 'mini-dot ' + stateClass;
                        if (drawerDot) drawerDot.className = 'status-dot ' + stateClass;

                        let uptimeFormatted = s.status.toUpperCase();
                        if (s.status === 'Online') {
                            const hrs = Math.floor(s.uptime_secs / 3600).toString().padStart(2, '0');
                            const mins = Math.floor((s.uptime_secs % 3600) / 60).toString().padStart(2, '0');
                            const secs = (s.uptime_secs % 60).toString().padStart(2, '0');
                            uptimeFormatted = `ONLINE (${hrs}:${mins}:${secs})`;
                        }

                        if (uptimeVal) uptimeVal.innerText = uptimeFormatted;
                        if (drawerUptime) drawerUptime.innerText = uptimeFormatted;

                        if (cpuVal) cpuVal.innerText = `${s.cpu_percent.toFixed(1)}%`;
                        if (drawerCpu) drawerCpu.innerText = `${s.cpu_percent.toFixed(1)}%`;
                        if (cpuBar) cpuBar.style.width = `${Math.min(s.cpu_percent, 100)}%`;

                        if (memVal) memVal.innerText = `${s.memory_mb.toFixed(1)} MB`;
                        if (drawerMem) drawerMem.innerText = `${s.memory_mb.toFixed(1)} MB`;
                        if (memBar) memBar.style.width = `${Math.min((s.memory_mb / 2048) * 100, 100)}%`;
                    });
                }

                // 2. Update System Registers & Header IP Badge
                if (data.registers) {
                    const r = data.registers;
                    externalUrlStr = r.external_url;
                    document.getElementById('hdr-lan-ip').innerText = `${r.lan_ip}:${r.http_port}`;
                    document.getElementById('reg-lan-ip').innerText = r.lan_ip;
                    document.getElementById('reg-ext-url').innerText = r.external_url;
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

                if (data.history && data.history.length > 0) {
                    historyData = data.history;
                }

                drawDayTradeChart();
            } catch (e) {
                console.error("Error fetching metrics:", e);
            }
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

        function escapeHtml(str) { return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

        function setFilter(type, val, btn) {
            if (type === 'srv') {
                currentSrvFilter = val;
                document.querySelectorAll('.log-filter-scroll-row .filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderLogs();
            }
        }

        function clearLogs() { logBuffer = []; renderLogs(); }

        function togglePause() {
            isPaused = !isPaused;
            const btn = document.getElementById('pause-btn');
            btn.innerText = isPaused ? 'Continuar' : 'Pausar';
            btn.classList.toggle('active', isPaused);
        }

        function toggleDrawer(open) {
            document.getElementById('drawer-overlay').classList.toggle('open', open);
            document.getElementById('drawer-sidebar').classList.toggle('open', open);
        }

        function switchMobileTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            const btn = document.getElementById(`tab-btn-${tab}`);
            if (btn) btn.classList.add('active');

            if (tab === 'telemetry') {
                toggleDrawer(false);
                document.getElementById('section-telemetry').scrollIntoView({ behavior: 'smooth' });
            } else if (tab === 'logs') {
                toggleDrawer(false);
                document.getElementById('section-logs').scrollIntoView({ behavior: 'smooth' });
            } else if (tab === 'servers' || tab === 'menu') {
                toggleDrawer(true);
            }
        }

        function copyExternalUrl() {
            navigator.clipboard.writeText(externalUrlStr).then(() => {
                alert("Endereço copiado para a área de transferência: " + externalUrlStr);
            }).catch(() => {
                prompt("Copie o endereço manualmente:", externalUrlStr);
            });
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

        async function controlServer(name, action) {
            try {
                await fetch(`/api/control/${name}/${action}`, { method: 'POST' });
                setTimeout(fetchMetrics, 300);
            } catch (e) {}
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

        window.addEventListener('resize', drawDayTradeChart);
        setInterval(fetchMetrics, 1000);
        setInterval(fetchLogs, 800);
        fetchMetrics();
        fetchLogs();
    </script>
</body>
</html>
"##;
