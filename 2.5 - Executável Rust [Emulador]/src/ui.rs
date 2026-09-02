pub const HTML_DASHBOARD: &str = r##"<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Aion Classic - Classic Emu Dashboard</title>
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
            --accent-db: #3b82f6;
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
            -webkit-tap-highlight-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        }

        button, .tab-btn, .header, .drawer-header, .stat-pill, .status-badge, .filter-btn, .metric-box {
            user-select: none;
            -webkit-user-select: none;
        }

        .log-console, .log-line, .log-msg, .log-time, .log-tag, pre, code, .search-box, input, textarea {
            user-select: text !important;
            -webkit-user-select: text !important;
            cursor: text !important;
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

        .btn-db-studio {
            background: linear-gradient(135deg, #1d4ed8, #3b82f6);
            color: #fff;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.35);
        }
        .btn-db-studio:active, .btn-db-studio:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
        }

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

        /* 4 Top Cards Grid (Login, Game, Chat, Database) */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
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
        .card-db::before    { background: linear-gradient(90deg, transparent, var(--accent-db), transparent); }

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
        .fill-db    { background: linear-gradient(90deg, #1d4ed8, #3b82f6); }

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
            display: inline-flex;
            align-items: center;
            gap: 4px;
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
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            padding: 8px 10px;
            flex: 1;
            height: 100%;
            max-height: none;
            min-height: 0;
            overflow-y: auto;
            font-size: 0.74rem;
            line-height: 1.5;
            width: 100%;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
            -webkit-overflow-scrolling: touch;
            box-sizing: border-box;
        }

        .log-line {
            display: flex;
            gap: 8px;
            padding: 2px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
            align-items: flex-start;
        }

        .log-ts {
            color: #64748b;
            min-width: 68px;
            font-weight: 600;
            font-size: 0.7rem;
            flex-shrink: 0;
        }
        .log-badge {
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            flex-shrink: 0;
            display: inline-block;
            letter-spacing: 0.4px;
        }

        .badge-login {
            background: rgba(56, 189, 248, 0.18);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
        }
        .badge-game {
            background: rgba(16, 185, 129, 0.18);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .badge-chat {
            background: rgba(168, 85, 247, 0.18);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.4);
        }
        .badge-launcher {
            background: rgba(234, 179, 8, 0.18);
            color: #fbbf24;
            border: 1px solid rgba(234, 179, 8, 0.4);
        }

        .log-msg {
            word-break: break-word;
            overflow-wrap: anywhere;
            flex: 1;
            color: #e2e8f0;
        }
        .log-msg.srv-login { color: #bae6fd; }
        .log-msg.srv-game  { color: #a7f3d0; }
        .log-msg.srv-chat  { color: #e9d5ff; }
        .log-msg.srv-launcher { color: #fef08a; }
        .log-msg.lvl-warn  { color: #fde047 !important; font-weight: 600; }
        .log-msg.lvl-error { color: #fca5a5 !important; font-weight: 700; }

        /* Fullscreen Logs Button */
        .btn-fullscreen-logs {
            background: rgba(56, 189, 248, 0.12) !important;
            border: 1px solid rgba(56, 189, 248, 0.35) !important;
            color: var(--accent-login) !important;
            font-weight: 700 !important;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .btn-fullscreen-logs:hover {
            background: rgba(56, 189, 248, 0.25) !important;
            border-color: var(--accent-login) !important;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.35);
            color: #ffffff !important;
            transform: translateY(-1px);
        }

        /* Dedicated Fullscreen Logs View */
        .logs-fullscreen-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: #000000;
            z-index: 99999;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin: 0;
            padding: 0;
            border: none;
            box-sizing: border-box;
        }

        /* Top Central Floating Rounded Navbar (Glassmorphism) */
        .fs-navbar {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 100000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            background: rgba(10, 16, 30, 0.78);
            backdrop-filter: blur(24px) saturate(190%);
            -webkit-backdrop-filter: blur(24px) saturate(190%);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 9999px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.85), inset 0 1px 0 rgba(255, 255, 255, 0.18);
            padding: 6px 16px;
            max-width: calc(100vw - 28px);
            white-space: nowrap;
            animation: fsNavbarSlideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes fsNavbarSlideDown {
            from { opacity: 0; transform: translate(-50%, -20px); }
            to { opacity: 1; transform: translate(-50%, 0); }
        }

        .fs-nav-title {
            display: flex;
            align-items: center;
            gap: 7px;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: #f1f5f9;
        }

        .fs-fibonacci-hud {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 9999px;
            padding: 3px 8px 3px 6px;
        }

        .fs-fib-canvas {
            display: block;
            width: 76px;
            height: 24px;
            flex-shrink: 0;
        }

        .fs-metrics-group {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .fs-badge {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 2px 7px;
            border-radius: 12px;
            font-size: 0.68rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.07);
        }

        .fs-badge .fs-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .fs-badge .fs-name {
            font-weight: 700;
            opacity: 0.9;
        }

        .fs-badge .fs-val {
            font-weight: 700;
            color: #ffffff;
        }

        .fs-badge-login { border-color: rgba(56, 189, 248, 0.35); color: #38bdf8; background: rgba(56, 189, 248, 0.08); }
        .fs-badge-game { border-color: rgba(16, 185, 129, 0.35); color: #34d399; background: rgba(16, 185, 129, 0.08); }
        .fs-badge-chat { border-color: rgba(168, 85, 247, 0.35); color: #c084fc; background: rgba(168, 85, 247, 0.08); }
        .fs-badge-launcher { border-color: rgba(234, 179, 8, 0.35); color: #fbbf24; background: rgba(234, 179, 8, 0.08); }

        .fs-controls {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .fs-filter-group {
            display: flex;
            gap: 3px;
            background: rgba(0, 0, 0, 0.35);
            padding: 2px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .fs-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 2px 7px;
            border-radius: 6px;
            font-size: 0.68rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .fs-btn.active {
            background: rgba(56, 189, 248, 0.25);
            color: var(--accent-login);
            font-weight: 700;
        }

        .fs-search-box {
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 3px 10px;
            color: #fff;
            font-size: 0.7rem;
            outline: none;
            width: 130px;
            transition: width 0.2s ease, border-color 0.2s ease;
        }
        .fs-search-box:focus {
            width: 170px;
            border-color: var(--accent-login);
        }

        .fs-close-btn {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #fca5a5;
            padding: 3px 9px;
            border-radius: 12px;
            font-size: 0.68rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: all 0.15s ease;
        }
        .fs-close-btn:hover {
            background: rgba(239, 68, 68, 0.35);
            color: #ffffff;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
        }

        .fs-log-console {
            width: 100vw;
            height: 100vh;
            background: #000000;
            color: #f1f5f9;
            padding: 68px 24px 20px 24px;
            overflow-y: auto;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
            font-size: 0.82rem;
            line-height: 1.6;
            box-sizing: border-box;
            border: none;
            outline: none;
            scrollbar-width: thin;
            scrollbar-color: #334155 #000000;
        }

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

        /* Custom Global & Studio Scrollbars */
        ::-webkit-scrollbar {
            width: 7px;
            height: 7px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.25);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.18);
            border-radius: 6px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(56, 189, 248, 0.45);
        }
        * {
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 255, 255, 0.18) rgba(0, 0, 0, 0.25);
        }

        /* Database Studio Modal & Workbench (Full Glassmorphism & Responsive) */
        .db-modal-overlay {
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(4, 7, 15, 0.88);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            z-index: 1500;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 14px;
            box-sizing: border-box;
        }
        .db-modal-overlay.open { display: flex; }

        .db-window {
            width: 98vw;
            height: 94vh;
            max-width: 1440px;
            max-height: 94vh;
            background: #090e1a;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(56, 189, 248, 0.12);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-sizing: border-box;
        }

        .db-header {
            background: #0f172a;
            border-bottom: 1px solid var(--border-glass);
            padding: 10px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
            gap: 10px;
            flex-wrap: wrap;
            box-sizing: border-box;
        }

        .db-header-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.92rem;
            font-weight: 700;
            color: #f8fafc;
            min-width: 0;
        }
        .db-header-title span:nth-child(2) {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .db-header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .db-mobile-toggle-btn {
            display: none;
        }

        .db-body {
            flex: 1 1 0;
            display: flex;
            min-height: 0;
            min-width: 0;
            overflow: hidden;
            position: relative;
        }

        .db-sidebar {
            width: 290px;
            min-width: 250px;
            max-width: 320px;
            background: #070b14;
            border-right: 1px solid var(--border-glass);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            min-height: 0;
            height: 100%;
            overflow: hidden;
            position: relative;
            z-index: 5;
            box-sizing: border-box;
        }

        .db-sidebar-header {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-shrink: 0;
            background: rgba(11, 18, 33, 0.6);
        }

        .db-sidebar-title {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .db-sidebar-tools {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .db-btn-micro {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 0.65rem;
            color: #94a3b8;
            cursor: pointer;
            transition: all 0.15s;
            font-weight: 600;
        }
        .db-btn-micro:hover {
            background: rgba(56, 189, 248, 0.2);
            color: #fff;
            border-color: rgba(56, 189, 248, 0.4);
        }

        .db-table-search {
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid var(--border-glass);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 0.75rem;
            color: #fff;
            outline: none;
            width: 100%;
            transition: border-color 0.2s;
            box-sizing: border-box;
        }
        .db-table-search:focus {
            border-color: var(--accent-login);
        }

                /* Custom Scrollbars */
        .db-tables-list::-webkit-scrollbar,
        .db-grid-wrapper::-webkit-scrollbar,
        .db-sql-result-box::-webkit-scrollbar,
        .db-sql-editor::-webkit-scrollbar,
        .db-sidebar::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        .db-tables-list::-webkit-scrollbar-thumb,
        .db-grid-wrapper::-webkit-scrollbar-thumb,
        .db-sql-result-box::-webkit-scrollbar-thumb,
        .db-sql-editor::-webkit-scrollbar-thumb,
        .db-sidebar::-webkit-scrollbar-thumb {
            background: rgba(56, 189, 248, 0.25);
            border-radius: 4px;
        }
        .db-tables-list::-webkit-scrollbar-thumb:hover,
        .db-grid-wrapper::-webkit-scrollbar-thumb:hover,
        .db-sql-result-box::-webkit-scrollbar-thumb:hover,
        .db-sql-editor::-webkit-scrollbar-thumb:hover,
        .db-sidebar::-webkit-scrollbar-thumb:hover {
            background: rgba(56, 189, 248, 0.55);
        }

        .db-btn-micro {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 4px;
            color: #94a3b8;
            font-size: 0.65rem;
            padding: 2px 7px;
            cursor: pointer;
            transition: all 0.15s;
            display: inline-flex;
            align-items: center;
            gap: 3px;
        }
        .db-btn-micro:hover {
            background: rgba(56, 189, 248, 0.2);
            color: #fff;
            border-color: rgba(56, 189, 248, 0.4);
        }
        .db-btn-micro.danger:hover {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border-color: rgba(239, 68, 68, 0.4);
        }

        .db-action-btn-sm {
            opacity: 0.6;
            background: transparent;
            border: none;
            color: #94a3b8;
            cursor: pointer;
            padding: 2px 4px;
            border-radius: 3px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
            font-size: 0.65rem;
        }
        .db-action-btn-sm:hover {
            opacity: 1;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }
        .db-action-btn-sm.danger:hover {
            color: #f87171;
            background: rgba(239, 68, 68, 0.2);
        }
        .db-table-item:hover .db-action-btn-sm,
        .db-group-header:hover .db-action-btn-sm {
            opacity: 0.9;
        }

        .db-select-sm {
            background: #090d18;
            color: #fff;
            border: 1px solid var(--border-glass);
            border-radius: 4px;
            padding: 3px 6px;
            font-size: 0.72rem;
            outline: none;
        }
        .db-select-sm:focus {
            border-color: var(--accent-login);
        }

        .db-tables-list {
            flex: 1 1 0;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 8px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-height: 0;
            box-sizing: border-box;
        }

        /* Database Accordion Group - Fixed Overlap & Flex Layout */
        .db-group {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.65);
            overflow: hidden;
            transition: border-color 0.2s, box-shadow 0.2s;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            margin-bottom: 2px;
        }
        .db-group:hover {
            border-color: rgba(255, 255, 255, 0.15);
        }
        .db-group.open {
            border-color: rgba(56, 189, 248, 0.3);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
        }

        .db-group-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 9px 12px;
            cursor: pointer;
            user-select: none;
            background: rgba(15, 23, 42, 0.85);
            border-bottom: 1px solid transparent;
            transition: background 0.15s;
            flex-shrink: 0;
        }
        .db-group-header:hover {
            background: rgba(30, 41, 59, 0.95);
        }
        .db-group.open .db-group-header {
            border-bottom-color: rgba(255, 255, 255, 0.08);
            background: rgba(15, 23, 42, 0.95);
        }

        .db-group-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            color: #f1f5f9;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .db-group-meta {
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }
        .db-group-chevron {
            font-size: 0.65rem;
            color: #64748b;
            transition: transform 0.2s;
            display: inline-block;
        }
        .db-group.open .db-group-chevron {
            transform: rotate(90deg);
        }

        .db-group-content {
            display: none;
            padding: 6px;
            flex-direction: column;
            gap: 3px;
            background: rgba(7, 11, 20, 0.6);
        }
        .db-group.open .db-group-content {
            display: flex;
        }

        .db-table-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 10px;
            border-radius: 6px;
            color: #cbd5e1;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.15s;
            border: 1px solid transparent;
            min-height: 28px;
            box-sizing: border-box;
            gap: 6px;
        }
        .db-table-item:hover {
            background: rgba(255, 255, 255, 0.06);
            color: #fff;
        }
        .db-table-item.active {
            background: rgba(56, 189, 248, 0.16);
            border-color: rgba(56, 189, 248, 0.4);
            color: var(--accent-login);
            font-weight: 700;
        }

        .db-table-badge {
            font-size: 0.62rem;
            padding: 1px 5px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            font-weight: 600;
            flex-shrink: 0;
        }
        .db-table-item.active .db-table-badge {
            background: rgba(56, 189, 248, 0.25);
            color: var(--accent-login);
        }

        .db-main {
            flex: 1 1 0;
            display: flex;
            flex-direction: column;
            min-width: 0;
            min-height: 0;
            background: #0a0f1d;
            overflow: hidden;
        }

        .db-toolbar {
            padding: 8px 14px;
            background: #0d1424;
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            flex-shrink: 0;
            box-sizing: border-box;
        }

        .db-tab-group {
            display: flex;
            background: rgba(0, 0, 0, 0.4);
            padding: 2px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            flex-shrink: 0;
        }

        .db-tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.72rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            font-weight: 600;
            transition: all 0.15s;
        }
        .db-tab-btn.active {
            background: rgba(56, 189, 248, 0.25);
            color: var(--accent-login);
            font-weight: 700;
        }

        .db-content-area {
            flex: 1 1 0;
            min-height: 0;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        .db-grid-wrapper {
            flex: 1 1 0;
            min-height: 0;
            overflow: auto;
            background: #070a12;
            position: relative;
            -webkit-overflow-scrolling: touch;
        }

        .db-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.74rem;
            text-align: left;
            white-space: nowrap;
        }

        .db-table th {
            position: sticky;
            top: 0;
            background: #111a2e;
            color: #94a3b8;
            padding: 7px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            border-right: 1px solid rgba(255, 255, 255, 0.04);
            font-weight: 700;
            cursor: pointer;
            z-index: 10;
            user-select: none;
        }
        .db-table th:hover {
            color: #fff;
            background: #16223b;
        }

        .db-table td {
            padding: 6px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            border-right: 1px solid rgba(255, 255, 255, 0.02);
            color: #e2e8f0;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .db-table tr:hover td {
            background: rgba(56, 189, 248, 0.05);
        }

        .db-pk-tag {
            font-size: 0.6rem;
            color: #eab308;
            background: rgba(234, 179, 8, 0.15);
            padding: 1px 4px;
            border-radius: 3px;
            margin-left: 4px;
            font-weight: 700;
        }

        .db-null-val {
            color: #64748b;
            font-style: italic;
            font-size: 0.68rem;
        }

        .db-pagination-bar {
            padding: 6px 14px;
            background: #0d1424;
            border-top: 1px solid var(--border-glass);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.72rem;
            color: var(--text-muted);
            flex-shrink: 0;
            flex-wrap: wrap;
            gap: 8px;
            box-sizing: border-box;
        }

        .db-sql-container {
            flex: 1 1 0;
            display: flex;
            flex-direction: column;
            min-height: 0;
            padding: 12px;
            gap: 10px;
            box-sizing: border-box;
        }

        .db-sql-editor {
            width: 100%;
            height: 120px;
            min-height: 80px;
            max-height: 260px;
            background: #050811;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 10px;
            color: #38bdf8;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
            font-size: 0.78rem;
            line-height: 1.4;
            resize: vertical;
            outline: none;
            box-sizing: border-box;
        }

        .db-sql-result-box {
            flex: 1 1 0;
            min-height: 0;
            background: #070a12;
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            overflow: auto;
            padding: 6px;
            box-sizing: border-box;
        }

        .db-row-modal {
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.78);
            backdrop-filter: blur(8px);
            z-index: 1600;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 16px;
            box-sizing: border-box;
        }
        .db-row-modal.open { display: flex; }

        .db-row-card {
            width: 90%;
            max-width: 550px;
            max-height: 85vh;
            background: #0d1424;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            box-shadow: 0 16px 40px rgba(0,0,0,0.8);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-sizing: border-box;
        }

        .db-row-form {
            padding: 14px 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            flex: 1 1 0;
            min-height: 0;
            box-sizing: border-box;
        }

        .db-form-field {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .db-form-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }

        .db-form-input {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            padding: 6px 10px;
            color: #fff;
            font-size: 0.78rem;
            outline: none;
            box-sizing: border-box;
            width: 100%;
        }
        .db-form-input:focus {
            border-color: var(--accent-login);
        }

        /* Mobile & Tablet Responsive Design */
        @media (max-width: 900px) {
            html, body {
                overflow-y: auto !important;
                height: auto !important;
            }
            .cards-grid { grid-template-columns: 1fr !important; }
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

            /* Database Studio Responsive */
            .db-modal-overlay {
                padding: 0;
            }
            .db-window {
                width: 100vw;
                height: 100vh;
                max-width: 100vw;
                max-height: 100vh;
                border-radius: 0;
                border: none;
            }
            .db-header {
                padding: 8px 10px;
            }
            .db-mobile-toggle-btn {
                display: inline-flex;
            }
            .db-body {
                flex-direction: column;
            }
            .db-sidebar {
                width: 100%;
                max-width: 100%;
                height: auto;
                max-height: 220px;
                border-right: none;
                border-bottom: 1px solid var(--border-glass);
                display: none;
                flex-shrink: 0;
            }
            .db-sidebar.mobile-open {
                display: flex;
            }
            .db-toolbar {
                padding: 6px 10px;
                gap: 6px;
            }
            #db-grid-controls {
                width: 100%;
            }
            #db-row-search-input {
                flex: 1;
                width: auto !important;
            }
            #db-grid-actions {
                width: 100%;
                justify-content: flex-start;
                overflow-x: auto;
            }
            .db-pagination-bar {
                padding: 6px 10px;
            }
        }

        @media (max-width: 600px) {
            .db-header-title span:nth-child(2) {
                max-width: 140px;
            }
            .db-header-actions button span:not(.btn-svg) {
                display: none;
            }
            .db-tab-btn span:not(.btn-svg) {
                font-size: 0.68rem;
            }
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
                <div class="brand-text">Classic Emu</div>
                <div class="brand-pill">Classic 4.5</div>
            </div>
            <div class="header-status-pills">
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-login"></div> <span>Login</span></div>
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-game"></div> <span>Game</span></div>
                <div class="mini-stat-label"><div class="mini-dot" id="hdr-dot-chat"></div> <span>Chat</span></div>
            </div>
        </div>

        <div class="header-right">
            <!-- Database Studio Header Button -->
            <button class="btn-db-studio" onclick="openDbStudio()" title="Gerenciador e Editor do Banco de Dados SQLite (Workbench / Navicat)">
                <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></span>
                <span>Banco de Dados</span>
            </button>

            <!-- Simple Host:Port Text Display (Copy on click) -->
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
        <!-- Desktop 4 Cards (Login, Game, Chat, Database) -->
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

            <!-- Database Card -->
            <div class="card card-db" id="card-db">
                <div class="card-header">
                    <div class="card-title-box">
                        <div class="status-dot online" id="dot-db"></div>
                        <div class="card-title">Banco SQLite</div>
                    </div>
                    <div class="card-tag">SQLite (login / game / chat)</div>
                </div>
                <div class="metrics-box">
                    <div class="metric-row"><span class="metric-label">Engine / Modo:</span><span class="metric-value" style="color:var(--accent-game);">WAL (Ativo)</span></div>
                    <div class="metric-row"><span class="metric-label">Tabelas:</span><span class="metric-value" id="val-db-tables" style="color:var(--accent-db);">0 Tabelas (0 Bancos)</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-db" style="width: 100%;"></div></div>
                    <div class="metric-row" style="margin-top: 2px;"><span class="metric-label">Tamanho em Disco:</span><span class="metric-value" id="val-db-size">0 KB</span></div>
                    <div class="progress-bar-bg"><div class="progress-bar-fill fill-db" style="width: 100%;"></div></div>
                </div>
                <div class="card-actions">
                    <button class="btn-db-studio" onclick="openDbStudio()">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></span>
                        <span>Abrir Estúdio</span>
                    </button>
                    <button class="btn-danger" onclick="openCleanAllModal()">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></span>
                        <span>Limpar Tudo</span>
                    </button>
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
                        LOGS UNIFICADOS (LOGIN, GAME, CHAT)
                    </span>
                    <div style="display: flex; gap: 5px;">
                        <button class="filter-btn btn-fullscreen-logs" id="btn-fullscreen-logs" onclick="openFullscreenLogs()" title="Abrir Logs em Tela Cheia (F12 / ESC)">
                            <span class="btn-svg"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg></span>
                            <span>Tela Cheia</span>
                        </button>
                    </div>
                </div>

                <div class="log-filter-scroll-row">
                    <button class="filter-btn active" data-srv="all" onclick="setFilter('srv', 'all', this)">Todos</button>
                    <button class="filter-btn" data-srv="login" onclick="setFilter('srv', 'login', this)">Login</button>
                    <button class="filter-btn" data-srv="game" onclick="setFilter('srv', 'game', this)">Game</button>
                    <button class="filter-btn" data-srv="chat" onclick="setFilter('srv', 'chat', this)">Chat</button>
                    <button class="filter-btn" id="copy-logs-btn" style="margin-left: auto; border-color: rgba(56, 189, 248, 0.4); color: #38bdf8; display: inline-flex; align-items: center; gap: 5px;" onclick="copyVisibleLogs()">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        Copiar Logs
                    </button>
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
                Painel & Gestão
            </div>
            <button class="drawer-close-btn" onclick="toggleDrawer(false)">✕</button>
        </div>

        <div class="drawer-content">
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

            <!-- Section: Banco de Dados -->
            <div>
                <div class="drawer-section-title">
                    <span class="btn-svg"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></span>
                    Bancos de Dados (login / game / chat)
                </div>
                <div class="drawer-card">
                    <div style="display: flex; gap: 6px;">
                        <button class="btn-db-studio" style="flex:1;" onclick="toggleDrawer(false); openDbStudio();">
                            <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></span>
                            <span>Abrir Studio</span>
                        </button>
                        <button class="btn-danger" style="flex:1;" onclick="openCleanAllModal();">
                            <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg></span>
                            <span>Limpar Tudo</span>
                        </button>
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
                    <button class="btn-secondary" style="margin-top: 4px;" onclick="copyExternalUrl()">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></span>
                        <span>Copiar Link do Painel</span>
                    </button>
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
                    <div class="drawer-row"><span style="color: var(--text-muted);">Bancos SQLite:</span><span class="drawer-val" id="reg-db-size">login / game / chat (0 KB)</span></div>
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
        <button class="tab-btn" id="tab-btn-db" onclick="openDbStudio()">
            <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></span>
            Banco
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

    <!-- Database Studio Modal (MySQL Workbench / Navicat Style - SVG Icons Only) -->
        <div class="db-modal-overlay" id="db-studio-modal">
        <div class="db-window">
            <div class="db-header">
                <div class="db-header-title">
                    <span class="btn-svg" style="color: var(--accent-login);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></span>
                    <span>Database Studio & Workbench (SQLite)</span>
                    <span class="brand-pill" id="db-total-tables-pill">0 Tabelas</span>
                </div>
                <div class="db-header-actions">
                    <button class="btn-secondary db-mobile-toggle-btn" onclick="toggleMobileDbSidebar()" title="Alternar Lista de Tabelas">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg></span>
                        <span>Tabelas</span>
                    </button>
                    <button class="btn-start" onclick="openCreateDbModal()" title="Criar Novo Banco de Dados SQLite">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><line x1="12" y1="9" x2="12" y2="15"/><line x1="9" y1="12" x2="15" y2="12"/></svg></span>
                        <span>+ Novo Banco</span>
                    </button>
                    <button class="btn-start" onclick="openCreateTableModal()" title="Criar Nova Tabela">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="12" y1="12" x2="12" y2="18"/><line x1="9" y1="15" x2="15" y2="15"/></svg></span>
                        <span>+ Nova Tabela</span>
                    </button>
                    <button class="btn-secondary" onclick="loadDbSchema(true)" title="Atualizar Estrutura">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg></span>
                        <span>Recarregar</span>
                    </button>
                    <button class="btn-danger" onclick="openCleanAllModal()" title="Limpar/Truncate em Todas as Tabelas">
                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></span>
                        <span>Limpar Todas</span>
                    </button>
                    <button class="drawer-close-btn" onclick="closeDbStudio()">✕</button>
                </div>
            </div>

            <div class="db-body">
                <!-- Left Sidebar: Tables Explorer (Separated by Database) -->
                <div class="db-sidebar">
                    <div class="db-sidebar-header">
                        <div class="db-sidebar-title">
                            <span>Bancos & Tabelas</span>
                            <div class="db-sidebar-tools">
                                <button class="db-btn-micro" onclick="openCreateDbModal()" title="Adicionar Banco">+ Banco</button>
                                <button class="db-btn-micro" onclick="openCreateTableModal()" title="Adicionar Tabela">+ Tabela</button>
                                <button class="db-btn-micro" onclick="expandAllDbGroups(true)" title="Expandir Todos os Bancos">Expandir</button>
                                <button class="db-btn-micro" onclick="expandAllDbGroups(false)" title="Recolher Todos os Bancos">Recolher</button>
                            </div>
                        </div>
                        <input type="text" class="db-table-search" id="db-filter-table-input" placeholder="Buscar tabelas em todos os bancos..." onkeyup="filterTablesList()">
                    </div>
                    <div class="db-tables-list" id="db-tables-container"></div>
                </div>

                <!-- Main Area: Grid, Schema & SQL -->
                <div class="db-main">
                    <div class="db-toolbar">
                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            <div class="db-tab-group">
                                <button class="db-tab-btn active" id="db-tab-grid" onclick="switchDbTab('grid')">
                                    <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg></span>
                                    <span>Dados (Grid)</span>
                                </button>
                                <button class="db-tab-btn" id="db-tab-schema" onclick="switchDbTab('schema')">
                                    <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></span>
                                    <span>Estrutura</span>
                                </button>
                                <button class="db-tab-btn" id="db-tab-sql" onclick="switchDbTab('sql')">
                                    <span class="btn-svg"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></span>
                                    <span>Console SQL</span>
                                </button>
                            </div>

                            <div style="display: flex; align-items: center; gap: 6px;" id="db-grid-controls">
                                <input type="text" class="search-box" style="width: 180px;" id="db-row-search-input" placeholder="Buscar registros..." onkeyup="if(event.key==='Enter') executeRowSearch()">
                                <button class="btn-secondary" style="padding: 4px 8px;" onclick="executeRowSearch()">
                                    <span class="btn-svg"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
                                    <span>Buscar</span>
                                </button>
                            </div>
                        </div>

                        <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;" id="db-grid-actions">
                            <button class="btn-start" onclick="openInsertRowModal()">
                                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></span>
                                <span>Novo Registro</span>
                            </button>
                            <button class="btn-secondary" onclick="openAddColumnModal(currentDbTable, currentDbId)" title="Adicionar Coluna à Tabela">
                                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg></span>
                                <span>+ Coluna</span>
                            </button>
                            <button class="btn-secondary" onclick="openRenameTableModal(currentDbTable, currentDbId)" title="Renomear Tabela Atual">
                                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></span>
                                <span>Renomear</span>
                            </button>
                            <button class="btn-secondary" onclick="loadTableData(true)" title="Recarregar dados da tabela">
                                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg></span>
                                <span>Atualizar</span>
                            </button>
                            <button class="btn-stop" onclick="truncateCurrentTable()" title="Excluir todos os registros desta tabela">
                                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>
                                <span>Truncate Tabela</span>
                            </button>
                            <button class="btn-danger" onclick="openDropTableModal(currentDbTable, currentDbId)" title="Excluir permanentemente esta tabela (DROP)">
                                <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg></span>
                                <span>Excluir Tabela</span>
                            </button>
                        </div>
                    </div>

                    <div class="db-content-area">
                        <!-- Tab 1: Grid View -->
                        <div id="db-view-grid" style="display: flex; flex-direction: column; width: 100%; height: 100%;">
                            <div class="db-grid-wrapper" id="db-grid-scroll">
                                <table class="db-table" id="db-data-table">
                                    <thead id="db-table-head"></thead>
                                    <tbody id="db-table-body"></tbody>
                                </table>
                            </div>
                            <div class="db-pagination-bar" id="db-pagination-container">
                                <div>Total: <b id="db-total-rows-txt" style="color:#fff;">0</b> registros</div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span>Exibir:</span>
                                    <select id="db-limit-select" onchange="changePageLimit(this.value)" class="db-select-sm">
                                        <option value="25">25</option>
                                        <option value="50" selected>50</option>
                                        <option value="100">100</option>
                                        <option value="250">250</option>
                                    </select>
                                    <button class="filter-btn" id="db-prev-page-btn" onclick="prevPage()">◀ Anterior</button>
                                    <span id="db-page-info">Página 1 de 1</span>
                                    <button class="filter-btn" id="db-next-page-btn" onclick="nextPage()">Próxima ▶</button>
                                </div>
                            </div>
                        </div>

                        <!-- Tab 2: Schema View -->
                        <div id="db-view-schema" style="display: none; flex-direction: column; width: 100%; height: 100%; overflow: auto; padding: 12px; box-sizing: border-box;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <div style="font-weight: 700; font-size: 0.85rem; color: #f1f5f9;" id="db-schema-header-title">Colunas da Tabela</div>
                                <div style="display: flex; gap: 6px;">
                                    <button class="btn-start" onclick="openAddColumnModal(currentDbTable, currentDbId)">
                                        <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg></span>
                                        <span>+ Adicionar Coluna</span>
                                    </button>
                                    <button class="btn-secondary" onclick="openRenameTableModal(currentDbTable, currentDbId)">
                                        <span>Renomear Tabela</span>
                                    </button>
                                </div>
                            </div>
                            <table class="db-table" style="background:#070a12; border-radius:6px; border:1px solid rgba(255,255,255,0.06);">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Nome da Coluna</th>
                                        <th>Tipo de Dados</th>
                                        <th>Chave Primária (PK)</th>
                                        <th>Não Nulo (NOT NULL)</th>
                                        <th>Valor Padrão (DEFAULT)</th>
                                    </tr>
                                </thead>
                                <tbody id="db-schema-table-body"></tbody>
                            </table>
                        </div>

                        <!-- Tab 3: SQL Console -->
                        <div id="db-view-sql" style="display: none; flex-direction: column; width: 100%; height: 100%;">
                            <div class="db-sql-container">
                                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span style="font-size:0.75rem; color:var(--text-muted); display:flex; align-items:center; gap:5px;">
                                            <span class="btn-svg" style="color:var(--accent-login);"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></span>
                                            Banco:
                                        </span>
                                        <select id="db-sql-target-db" class="db-select-sm" onchange="onSqlDbChange()"></select>
                                    </div>
                                    <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                                        <input type="file" id="db-sql-file-input" accept=".sql,.txt" style="display:none;" onchange="loadSqlFile(this)">
                                        <button class="filter-btn" onclick="document.getElementById('db-sql-file-input').click()" title="Carregar arquivo SQL">📂 Carregar .SQL</button>
                                        <button class="filter-btn" onclick="setSqlTemplate('SELECT * FROM accounts LIMIT 50;')">accounts</button>
                                        <button class="filter-btn" onclick="setSqlTemplate('SELECT * FROM characters LIMIT 50;')">characters</button>
                                        <button class="filter-btn" onclick="setSqlTemplate('SELECT * FROM player_skills LIMIT 50;')">skills</button>
                                        <button class="filter-btn" onclick="setSqlTemplate('VACUUM;')">VACUUM</button>
                                        <button class="filter-btn" onclick="clearSqlConsole()" title="Limpar Console">Limpar</button>
                                        <button class="btn-start" onclick="executeCustomSql()">
                                            <span class="btn-svg"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg></span>
                                            <span>Executar SQL (F5)</span>
                                        </button>
                                        <button class="btn-secondary" onclick="exportSqlResultCsv()" title="Exportar resultado para CSV">CSV</button>
                                        <button class="btn-secondary" onclick="exportSqlResultJson()" title="Exportar resultado para JSON">JSON</button>
                                    </div>
                                </div>
                                <textarea class="db-sql-editor" id="db-sql-input" placeholder="Digite comandos SQL (suporta múltiplos comandos e scripts batch)..." onkeydown="handleSqlKeydown(event)">SELECT * FROM accounts LIMIT 50;</textarea>
                                <div id="db-sql-status-banner" style="font-size:0.72rem; padding:6px 10px; border-radius:4px; display:none;"></div>
                                <div class="db-sql-result-box" id="db-sql-results-box">
                                    <table class="db-table" id="db-sql-table">
                                        <thead id="db-sql-table-head"></thead>
                                        <tbody id="db-sql-table-body"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal: Create New Database -->
    <div class="modal-overlay" id="db-create-db-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:2100; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid rgba(56,189,248,0.3); border-radius:12px; padding:20px; width:90%; max-width:440px; display:flex; flex-direction:column; gap:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#f1f5f9; display:flex; align-items:center; gap:8px;">
                <span class="btn-svg" style="color:var(--accent-login);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg></span>
                <span>Criar Novo Banco de Dados SQLite</span>
            </div>
            <div style="color:var(--text-muted); font-size:0.78rem;">O novo arquivo SQLite será criado na pasta de dados do servidor com suporte a WAL mode.</div>
            <div class="db-form-field">
                <div class="db-form-label">Nome do Banco:</div>
                <input type="text" class="db-form-input" id="db-create-name-input" placeholder="ex: custom_events, analytics, backups">
            </div>
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeCreateDbModal()">Cancelar</button>
                <button class="btn-start" onclick="submitCreateDb()">Criar Banco</button>
            </div>
        </div>
    </div>

    <!-- Modal: Create New Table -->
    <div class="modal-overlay" id="db-create-table-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:2100; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid rgba(56,189,248,0.3); border-radius:12px; padding:20px; width:95%; max-width:680px; max-height:85vh; display:flex; flex-direction:column; gap:12px; overflow:hidden;">
            <div style="font-weight:700; font-size:0.95rem; color:#f1f5f9; display:flex; align-items:center; gap:8px;">
                <span class="btn-svg" style="color:var(--accent-game);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="3" x2="9" y2="21"/></svg></span>
                <span>Criar Nova Tabela</span>
            </div>
            <div style="display:flex; gap:10px;">
                <div style="flex:1;">
                    <div class="db-form-label">Banco de Destino:</div>
                    <select id="db-create-table-db-select" class="db-select-sm" style="width:100%; padding:6px; font-size:0.8rem;"></select>
                </div>
                <div style="flex:2;">
                    <div class="db-form-label">Nome da Tabela:</div>
                    <input type="text" class="db-form-input" id="db-create-table-name-input" placeholder="ex: guild_rewards, custom_shop">
                </div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                <span style="font-size:0.75rem; font-weight:700; color:#cbd5e1;">Definição de Colunas:</span>
                <button class="db-btn-micro" onclick="addTableColumnRow()">+ Adicionar Coluna</button>
            </div>

            <div style="overflow-y:auto; flex:1; min-height:120px; border:1px solid rgba(255,255,255,0.06); border-radius:6px; background:#070a12; padding:6px;">
                <table class="db-table" style="background:transparent;">
                    <thead>
                        <tr>
                            <th>Nome da Coluna</th>
                            <th>Tipo</th>
                            <th style="text-align:center;">PK</th>
                            <th style="text-align:center;">Not Null</th>
                            <th>Valor Padrão</th>
                            <th style="text-align:center;">Ação</th>
                        </tr>
                    </thead>
                    <tbody id="db-create-table-columns-tbody"></tbody>
                </table>
            </div>

            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeCreateTableModal()">Cancelar</button>
                <button class="btn-start" onclick="submitCreateTable()">Criar Tabela</button>
            </div>
        </div>
    </div>

    <!-- Modal: Add Column -->
    <div class="modal-overlay" id="db-add-col-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:2100; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid rgba(56,189,248,0.3); border-radius:12px; padding:20px; width:90%; max-width:440px; display:flex; flex-direction:column; gap:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#f1f5f9; display:flex; align-items:center; gap:8px;">
                <span class="btn-svg" style="color:var(--accent-login);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg></span>
                <span id="db-add-col-title">Adicionar Coluna</span>
            </div>
            <div class="db-form-field">
                <div class="db-form-label">Nome da Coluna:</div>
                <input type="text" class="db-form-input" id="db-add-col-name-input" placeholder="ex: created_by, is_active">
            </div>
            <div class="db-form-field">
                <div class="db-form-label">Tipo de Dados:</div>
                <select id="db-add-col-type-select" class="db-select-sm" style="width:100%; padding:6px;">
                    <option value="INTEGER">INTEGER (Numérico Inteiro)</option>
                    <option value="TEXT" selected>TEXT (Texto / String)</option>
                    <option value="REAL">REAL (Decimal / Float)</option>
                    <option value="BLOB">BLOB (Binário)</option>
                </select>
            </div>
            <div style="display:flex; gap:16px; align-items:center;">
                <label style="font-size:0.75rem; color:#cbd5e1; display:flex; align-items:center; gap:6px; cursor:pointer;">
                    <input type="checkbox" id="db-add-col-notnull-input"> NOT NULL
                </label>
            </div>
            <div class="db-form-field">
                <div class="db-form-label">Valor Padrão (Opcional):</div>
                <input type="text" class="db-form-input" id="db-add-col-dflt-input" placeholder="ex: 0, 'ativo'">
            </div>
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeAddColModal()">Cancelar</button>
                <button class="btn-start" onclick="submitAddColumn()">Adicionar Coluna</button>
            </div>
        </div>
    </div>

    <!-- Modal: Rename Table -->
    <div class="modal-overlay" id="db-rename-table-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:2100; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid rgba(56,189,248,0.3); border-radius:12px; padding:20px; width:90%; max-width:440px; display:flex; flex-direction:column; gap:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#f1f5f9; display:flex; align-items:center; gap:8px;">
                <span>Renomear Tabela</span>
            </div>
            <div class="db-form-field">
                <div class="db-form-label">Nome Atual:</div>
                <input type="text" class="db-form-input" id="db-rename-old-input" disabled style="opacity:0.7;">
            </div>
            <div class="db-form-field">
                <div class="db-form-label">Novo Nome:</div>
                <input type="text" class="db-form-input" id="db-rename-new-input" placeholder="Digite o novo nome da tabela">
            </div>
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeRenameTableModal()">Cancelar</button>
                <button class="btn-start" onclick="submitRenameTable()">Renomear</button>
            </div>
        </div>
    </div>

    <!-- Modal: Confirmation Modal (Delete DB / Drop Table) -->
    <div class="modal-overlay" id="db-confirm-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:2200; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid #ef4444; border-radius:12px; padding:20px; width:90%; max-width:440px; display:flex; flex-direction:column; gap:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#f87171; display:flex; align-items:center; gap:8px;">
                <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>
                <span id="db-confirm-title">Confirmar Ação</span>
            </div>
            <div style="color:var(--text-muted); font-size:0.8rem; line-height:1.4;" id="db-confirm-message"></div>
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeConfirmModal()">Cancelar</button>
                <button class="btn-danger" id="db-confirm-btn" onclick="executePendingConfirmAction()">Confirmar</button>
            </div>
        </div>
    </div>

    <!-- Row Insert/Edit Modal -->
    <div class="db-row-modal" id="db-row-modal">
        <div class="db-row-card">
            <div class="db-header">
                <div class="db-header-title">
                    <span class="btn-svg" style="color:var(--accent-login);"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg></span>
                    <span id="db-row-modal-title">Editar Registro</span>
                </div>
                <button class="drawer-close-btn" onclick="closeRowModal()">✕</button>
            </div>
            <div class="db-row-form" id="db-row-form-fields"></div>
            <div style="padding: 10px 16px; background:#0b111e; border-top:1px solid var(--border-glass); display:flex; justify-content:flex-end; gap:8px;">
                <button class="btn-secondary" onclick="closeRowModal()">Cancelar</button>
                <button class="btn-start" onclick="saveRowData()">
                    <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg></span>
                    <span>Salvar Alterações</span>
                </button>
            </div>
        </div>
    </div>

    <!-- Clean All Tables Confirmation Modal -->
    <div class="modal-overlay" id="clean-all-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); backdrop-filter:blur(8px); z-index:2100; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid #ef4444; border-radius:12px; padding:20px; width:90%; max-width:440px; display:flex; flex-direction:column; gap:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#f87171; display:flex; align-items:center; gap:8px;">
                <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>
                <span>Limpar / Resetar Todas as Tabelas</span>
            </div>
            <div style="color:var(--text-muted); font-size:0.8rem; line-height:1.4;">
                Tem certeza que deseja limpar completamente todas as tabelas em todos os bancos?<br><br>
                <span style="color:#fca5a5;">Esta ação apagará todos os dados de login.db, game.db, chat.db e resetará as sequências.</span>
            </div>
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeCleanAllModal()">Cancelar</button>
                <button class="btn-danger" onclick="confirmCleanAll()">
                    <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg></span>
                    <span>Sim, Limpar Tudo</span>
                </button>
            </div>
        </div>
    </div>

    <!-- Shutdown Modal -->
    <div class="modal-overlay" id="shutdown-modal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.7); backdrop-filter:blur(8px); z-index:2000; align-items:center; justify-content:center;">
        <div style="background:#0e1526; border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:20px; width:90%; max-width:400px; display:flex; flex-direction:column; gap:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#f87171; display:flex; align-items:center; gap:8px;">
                <span class="btn-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                Encerrar Emulador Java
            </div>
            <div style="color:var(--text-muted); font-size:0.78rem; line-height:1.4;">Esta ação finalizará com segurança o Game Server, Login Server e Chat Server, liberando todas as portas de rede.</div>
            <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top:4px;">
                <button class="btn-secondary" onclick="closeShutdownModal()">Cancelar</button>
                <button class="btn-danger" onclick="confirmShutdown()">Confirmar</button>
            </div>
        </div>
    </div>

    <!-- Dedicated Pure Black Fullscreen Logs View -->
    <div id="logs-fullscreen-overlay" class="logs-fullscreen-overlay" style="display:none;">
        <!-- Top Central Floating Rounded Navbar (Glassmorphism) with Fibonacci Telemetry -->
        <div class="fs-navbar">
            <div class="fs-nav-title">
                <span class="status-dot online" style="width:7px; height:7px; box-shadow:0 0 8px #10b981;"></span>
                <span class="fs-title-text">LOGS EM TEMPO REAL</span>
            </div>

            <!-- Fibonacci Real-Time Telemetry HUD -->
            <div class="fs-fibonacci-hud">
                <canvas id="fs-fibonacci-canvas" class="fs-fib-canvas"></canvas>
                <div class="fs-metrics-group">
                    <div class="fs-badge fs-badge-login" title="Login Server">
                        <span class="fs-dot" style="background:#38bdf8; box-shadow:0 0 6px #38bdf8;"></span>
                        <span class="fs-name">LOGIN:</span>
                        <span class="fs-val" id="fs-metric-login">0.0% · 0 MB</span>
                    </div>
                    <div class="fs-badge fs-badge-game" title="Game Server">
                        <span class="fs-dot" style="background:#10b981; box-shadow:0 0 6px #10b981;"></span>
                        <span class="fs-name">GAME:</span>
                        <span class="fs-val" id="fs-metric-game">0.0% · 0 MB</span>
                    </div>
                    <div class="fs-badge fs-badge-chat" title="Chat Server">
                        <span class="fs-dot" style="background:#a855f7; box-shadow:0 0 6px #a855f7;"></span>
                        <span class="fs-name">CHAT:</span>
                        <span class="fs-val" id="fs-metric-chat">0.0% · 0 MB</span>
                    </div>
                    <div class="fs-badge fs-badge-launcher" title="Sistema / Host">
                        <span class="fs-dot" style="background:#eab308; box-shadow:0 0 6px #eab308;"></span>
                        <span class="fs-name">SISTEMA:</span>
                        <span class="fs-val" id="fs-metric-launcher">0.0% · 0 MB</span>
                    </div>
                </div>
            </div>

            <!-- Fullscreen Filter & Search Controls -->
            <div class="fs-controls">
                <div class="fs-filter-group">
                    <button class="fs-btn active" data-srv="all" onclick="setFilter('srv', 'all', this)">Todos</button>
                    <button class="fs-btn" data-srv="login" onclick="setFilter('srv', 'login', this)">Login</button>
                    <button class="fs-btn" data-srv="game" onclick="setFilter('srv', 'game', this)">Game</button>
                    <button class="fs-btn" data-srv="chat" onclick="setFilter('srv', 'chat', this)">Chat</button>
                </div>
                <input type="text" class="fs-search-box" id="fs-search-input" placeholder="Filtrar logs..." onkeyup="renderLogs()">
                <button class="fs-close-btn" onclick="closeFullscreenLogs()" title="Sair da Tela Cheia (ESC ou F12)">
                    <span class="btn-svg"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></span>
                    <span>ESC / F12</span>
                </button>
            </div>
        </div>

        <!-- Pure Black Fullscreen Log Console -->
        <div class="fs-log-console" id="fs-log-console"></div>
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

        // Draw Day-Trade Multi-Curve Chart with Fibonacci levels and In-Canvas HUD Legend
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
            const padTop = 22;
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

            // 1. Fibonacci Guideline Levels
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

            // 2. Plot Curves
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

            // 3. In-Canvas Glass HUD Legend (Integrated inside the chart, Non-Clickable)
            const latest = historyData[historyData.length - 1] || {};
            const legendChips = [
                { name: 'Total', color: '#ffffff', dash: [4, 3], val: chartMetric === 'cpu' ? `${(latest.total_cpu || 0).toFixed(1)}%` : `${(latest.total_mem_mb || 0).toFixed(0)} MB` },
                { name: 'Login', color: '#38bdf8', dash: [], val: chartMetric === 'cpu' ? `${(latest.login_cpu || 0).toFixed(1)}%` : `${(latest.login_mem_mb || 0).toFixed(0)} MB` },
                { name: 'Game', color: '#10b981', dash: [], val: chartMetric === 'cpu' ? `${(latest.game_cpu || 0).toFixed(1)}%` : `${(latest.game_mem_mb || 0).toFixed(0)} MB` },
                { name: 'Chat', color: '#a855f7', dash: [], val: chartMetric === 'cpu' ? `${(latest.chat_cpu || 0).toFixed(1)}%` : `${(latest.chat_mem_mb || 0).toFixed(0)} MB` },
                { name: 'Launcher', color: '#eab308', dash: [], val: chartMetric === 'cpu' ? `${(latest.launcher_cpu || 0).toFixed(1)}%` : `${(latest.launcher_mem_mb || 0).toFixed(0)} MB` },
            ];

            let chipX = 8;
            const chipY = 11;
            ctx.font = 'bold 8.5px ui-monospace, SFMono-Regular, Menlo, monospace';
            ctx.textBaseline = 'middle';

            legendChips.forEach(chip => {
                const label = `${chip.name}: ${chip.val}`;
                const textWidth = ctx.measureText(label).width;
                const chipW = textWidth + 24;

                // Glass Pill Background
                ctx.fillStyle = 'rgba(7, 12, 23, 0.72)';
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                if (ctx.roundRect) {
                    ctx.roundRect(chipX, chipY - 8, chipW, 16, 4);
                } else {
                    ctx.rect(chipX, chipY - 8, chipW, 16);
                }
                ctx.fill();
                ctx.stroke();

                // Color Indicator Line
                ctx.strokeStyle = chip.color;
                ctx.lineWidth = 2;
                ctx.setLineDash(chip.dash || []);
                ctx.beginPath();
                ctx.moveTo(chipX + 5, chipY);
                ctx.lineTo(chipX + 15, chipY);
                ctx.stroke();
                ctx.setLineDash([]);

                // Text Label
                ctx.fillStyle = chip.color;
                ctx.textAlign = 'left';
                ctx.fillText(label, chipX + 19, chipY);

                chipX += chipW + 5;
            });

            // 4. Update Min/Max Stats
            const totals = historyData.map(d => chartMetric === 'cpu' ? d.total_cpu : d.total_mem_mb);
            const minV = Math.min(...totals);
            const maxV = Math.max(...totals);
            const unit = chartMetric === 'cpu' ? '%' : ' MB';

            const minEl = document.getElementById('stat-min-val');
            const maxEl = document.getElementById('stat-max-val');
            if (minEl) minEl.innerText = `${minV.toFixed(1)}${unit}`;
            if (maxEl) maxEl.innerText = `${maxV.toFixed(1)}${unit}`;
        }

        // Helper to format long uptime text: e.g. "2 minutos e 2 segundos" (sem parênteses)
        function formatLongUptime(totalSecs) {
            if (!totalSecs || totalSecs <= 0) return '0 segundos';
            const days = Math.floor(totalSecs / 86400);
            const hrs = Math.floor((totalSecs % 86400) / 3600);
            const mins = Math.floor((totalSecs % 3600) / 60);
            const secs = totalSecs % 60;

            const parts = [];
            if (days > 0) parts.push(`${days} ${days === 1 ? 'dia' : 'dias'}`);
            if (hrs > 0) parts.push(`${hrs} ${hrs === 1 ? 'hora' : 'horas'}`);
            if (mins > 0) parts.push(`${mins} ${mins === 1 ? 'minuto' : 'minutos'}`);
            if (secs > 0 || parts.length === 0) parts.push(`${secs} ${secs === 1 ? 'segundo' : 'segundos'}`);

            if (parts.length === 1) return parts[0];
            if (parts.length === 2) return `${parts[0]} e ${parts[1]}`;
            return `${parts.slice(0, -1).join(', ')} e ${parts[parts.length - 1]}`;
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

                        let uptimeFormatted = '';
                        if (s.status === 'Online') {
                            const longTime = formatLongUptime(s.uptime_secs);
                            uptimeFormatted = `<span class="status-dot online" style="display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:middle;"></span> ${longTime}`;
                        } else if (s.status === 'Starting') {
                            uptimeFormatted = `<span class="status-dot starting" style="display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:middle;"></span> Iniciando...`;
                        } else if (s.status === 'Crashed') {
                            uptimeFormatted = `<span class="status-dot crashed" style="display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:middle;"></span> Falhou`;
                        } else {
                            uptimeFormatted = `<span class="status-dot" style="display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:middle;"></span> Offline`;
                        }

                        if (uptimeVal) uptimeVal.innerHTML = uptimeFormatted;
                        if (drawerUptime) drawerUptime.innerHTML = uptimeFormatted;

                        if (cpuVal) cpuVal.innerText = `${s.cpu_percent.toFixed(1)}%`;
                        if (drawerCpu) drawerCpu.innerText = `${s.cpu_percent.toFixed(1)}%`;
                        if (cpuBar) cpuBar.style.width = `${Math.min(s.cpu_percent, 100)}%`;

                        if (memVal) memVal.innerText = `${s.memory_mb.toFixed(1)} MB`;
                        if (drawerMem) drawerMem.innerText = `${s.memory_mb.toFixed(1)} MB`;
                        if (memBar) memBar.style.width = `${Math.min((s.memory_mb / 2048) * 100, 100)}%`;
                    });
                }

                // 2. Update System Registers & DB Card
                if (data.registers) {
                    const r = data.registers;
                    externalUrlStr = r.external_url;
                    document.getElementById('hdr-lan-ip').innerText = `${r.lan_ip}:${r.http_port}`;
                    document.getElementById('reg-lan-ip').innerText = r.lan_ip;
                    document.getElementById('reg-ext-url').innerText = r.external_url;
                    
                    const dbSizeMB = (r.active_db_size_kb / 1024).toFixed(2);
                    document.getElementById('reg-db-size').innerText = `SQLite (${dbSizeMB} MB)`;
                    
                    const valDbSize = document.getElementById('val-db-size');
                    if (valDbSize) valDbSize.innerText = `${dbSizeMB} MB`;

                    const totalTbls = r.total_tables_count || 0;
                    const totalDbs = r.total_databases_count || 0;
                    const valDbTables = document.getElementById('val-db-tables');
                    if (valDbTables) {
                        valDbTables.innerText = `${totalTbls} Tabelas (${totalDbs} Bancos)`;
                    }

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
                updateFullscreenMetrics(data);
            } catch (e) {
                console.error("Error fetching metrics:", e);
            }
        }

        // Live Log Stream
        async function fetchLogs() {
            try {
                const srvParam = currentSrvFilter === 'all' ? 'all' : currentSrvFilter;
                const res = await fetch(`/api/logs?server=${srvParam}`);
                const data = await res.json();
                logBuffer = data;
                renderLogs();
            } catch (e) {
                console.error("Error fetching logs:", e);
            }
        }

        function renderLogs() {
            const consoleBox = document.getElementById('log-console');
            const fsConsoleBox = document.getElementById('fs-log-console');
            
            const search1 = (document.getElementById('search-input')?.value || '').toLowerCase();
            const search2 = (document.getElementById('fs-search-input')?.value || '').toLowerCase();
            const search = search1 || search2;

            const filtered = logBuffer.filter(entry => {
                const srv = (entry.server || '').toLowerCase();
                if (currentSrvFilter !== 'all' && srv !== currentSrvFilter) return false;
                if (search && !entry.message.toLowerCase().includes(search)) return false;
                return true;
            });

            const html = filtered.map(entry => {
                const time = entry.timestamp.split('T')[1]?.split('.')[0] || entry.timestamp;
                const srv = (entry.server || 'game').toLowerCase();
                const lvl = (entry.level || 'info').toLowerCase();
                return `<div class="log-line">
                    <span class="log-ts">[${time}]</span>
                    <span class="log-badge badge-${srv}">${entry.server.toUpperCase()}</span>
                    <span class="log-msg srv-${srv} lvl-${lvl}">${escapeHtml(entry.message)}</span>
                </div>`;
            }).join('');

            if (consoleBox) {
                const shouldScroll = consoleBox.scrollTop + consoleBox.clientHeight >= consoleBox.scrollHeight - 30;
                consoleBox.innerHTML = html;
                if (shouldScroll) {
                    consoleBox.scrollTop = consoleBox.scrollHeight;
                }
            }

            if (fsConsoleBox) {
                const shouldScrollFs = fsConsoleBox.scrollTop + fsConsoleBox.clientHeight >= fsConsoleBox.scrollHeight - 30;
                fsConsoleBox.innerHTML = html;
                if (shouldScrollFs) {
                    fsConsoleBox.scrollTop = fsConsoleBox.scrollHeight;
                }
            }
        }

        function setFilter(type, val, btn) {
            if (type === 'srv') {
                currentSrvFilter = val.toLowerCase();
                document.querySelectorAll('.log-filter-scroll-row .filter-btn, .fs-filter-group .fs-btn').forEach(b => {
                    const bVal = (b.getAttribute('data-srv') || b.innerText).toLowerCase();
                    const isTarget = bVal === currentSrvFilter || (currentSrvFilter === 'all' && (b.innerText === 'Todos' || bVal === 'all'));
                    b.classList.toggle('active', isTarget);
                });
                renderLogs();
            }
        }

        function setServerFilter(srv) {
            setFilter('srv', srv, null);
        }

        function copyVisibleLogs() {
            const consoleBox = document.getElementById('log-console');
            if (!consoleBox) return;
            const text = consoleBox.innerText || consoleBox.textContent || '';
            if (!text.trim()) {
                return;
            }
            const btn = document.getElementById('copy-logs-btn');
            const onDone = () => {
                if (btn) {
                    const originalHtml = btn.innerHTML;
                    btn.innerHTML = '<span>Copiado!</span>';
                    btn.style.color = '#34d399';
                    btn.style.borderColor = '#34d399';
                    setTimeout(() => {
                        btn.innerHTML = originalHtml;
                        btn.style.color = '#38bdf8';
                        btn.style.borderColor = 'rgba(56, 189, 248, 0.4)';
                    }, 2000);
                }
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(onDone).catch(() => {
                    fallbackCopyText(text, onDone);
                });
            } else {
                fallbackCopyText(text, onDone);
            }
        }

        function fallbackCopyText(text, cb) {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.top = '-9999px';
            document.body.appendChild(ta);
            ta.focus();
            ta.select();
            try {
                document.execCommand('copy');
                if (cb) cb();
            } catch (e) {}
            document.body.removeChild(ta);
        }

        // ==========================================
        // DEDICATED FULLSCREEN LOGS & FIBONACCI HUD
        // ==========================================
        function openFullscreenLogs() {
            const overlay = document.getElementById('logs-fullscreen-overlay');
            if (!overlay) return;
            overlay.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            renderLogs();
            drawFullscreenFibonacciChart();

            // Scroll to bottom
            const fsConsole = document.getElementById('fs-log-console');
            if (fsConsole) fsConsole.scrollTop = fsConsole.scrollHeight;
        }

        function closeFullscreenLogs() {
            const overlay = document.getElementById('logs-fullscreen-overlay');
            if (!overlay) return;
            overlay.style.display = 'none';
            document.body.style.overflow = '';
        }

        function isFullscreenLogsOpen() {
            const overlay = document.getElementById('logs-fullscreen-overlay');
            return overlay && overlay.style.display === 'flex';
        }

        function toggleFullscreenLogs() {
            if (isFullscreenLogsOpen()) {
                closeFullscreenLogs();
            } else {
                openFullscreenLogs();
            }
        }

        function updateFullscreenMetrics(data) {
            if (!data) return;
            if (data.servers) {
                data.servers.forEach(s => {
                    const el = document.getElementById(`fs-metric-${s.name}`);
                    if (el) {
                        el.innerText = `${s.cpu_percent.toFixed(1)}% · ${s.memory_mb.toFixed(0)} MB`;
                    }
                });
            }
            if (data.registers) {
                const el = document.getElementById('fs-metric-launcher');
                if (el) {
                    const cpu = data.registers.launcher_cpu_percent || 0.0;
                    const mem = data.registers.launcher_mem_mb || 0.0;
                    el.innerText = `${cpu.toFixed(1)}% · ${mem.toFixed(0)} MB`;
                }
            }
            drawFullscreenFibonacciChart();
        }

        function drawFullscreenFibonacciChart() {
            const canvas = document.getElementById('fs-fibonacci-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            const w = rect.width > 0 ? rect.width : 76;
            const h = rect.height > 0 ? rect.height : 24;

            canvas.width = w * dpr;
            canvas.height = h * dpr;
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, w, h);

            let loginV = 1.0, gameV = 1.0, chatV = 1.0, launcherV = 1.0;
            if (rawDashboardState && rawDashboardState.servers) {
                rawDashboardState.servers.forEach(s => {
                    if (s.name === 'login') loginV = Math.max(s.cpu_percent, 1.0);
                    if (s.name === 'game') gameV = Math.max(s.cpu_percent, 1.0);
                    if (s.name === 'chat') chatV = Math.max(s.cpu_percent, 1.0);
                });
            }
            if (rawDashboardState && rawDashboardState.registers) {
                launcherV = Math.max(rawDashboardState.registers.launcher_cpu_percent || 1.0, 1.0);
            }

            const cx = w / 2;
            const cy = h / 2;

            // Fibonacci Golden Arcs Radii: 3.5, 6, 8.5, 11 (golden proportion)
            const fibArcs = [
                { r: 3.5, color: '#a855f7', val: chatV, max: 100 },      // Chat (Purple)
                { r: 6.0, color: '#38bdf8', val: loginV, max: 100 },     // Login (Blue)
                { r: 8.5, color: '#10b981', val: gameV, max: 100 },      // Game (Green)
                { r: 11.0, color: '#eab308', val: launcherV, max: 100 },  // Launcher (Yellow)
            ];

            fibArcs.forEach(a => {
                const pct = Math.min(Math.max(a.val / a.max, 0.08), 1.0);
                const endAngle = -Math.PI / 2 + (pct * Math.PI * 2);

                // Background Ring
                ctx.beginPath();
                ctx.arc(cx, cy, a.r, 0, Math.PI * 2);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
                ctx.lineWidth = 1.4;
                ctx.stroke();

                // Glowing Active Arc
                ctx.beginPath();
                ctx.arc(cx, cy, a.r, -Math.PI / 2, endAngle);
                ctx.strokeStyle = a.color;
                ctx.lineWidth = 1.6;
                ctx.lineCap = 'round';
                ctx.stroke();
            });
        }

        async function controlServer(server, action) {
            try {
                await fetch(`/api/control/${server}/${action}`, { method: 'POST' });
                fetchMetrics();
            } catch (e) {
                console.error(`Error controlling ${server} (${action}):`, e);
            }
        }

        async function controlAll(action) {
            try {
                await fetch(`/api/control/all/${action}`, { method: 'POST' });
                fetchMetrics();
            } catch (e) {
                console.error(`Error controlling all servers (${action}):`, e);
            }
        }

        function toggleDrawer(open) {
            const drawer = document.getElementById('drawer-sidebar');
            const overlay = document.getElementById('drawer-overlay');
            if (!drawer || !overlay) return;
            if (open) {
                drawer.classList.add('open');
                overlay.classList.add('open');
            } else {
                drawer.classList.remove('open');
                overlay.classList.remove('open');
            }
        }

        function openSubsystemsDrawer() {
            const drawer = document.getElementById('subsystems-drawer');
            const overlay = document.getElementById('subsystems-overlay');
            if (drawer && overlay) {
                drawer.classList.add('open');
                overlay.classList.add('open');
                renderSubsystemsList();
            }
        }

        function closeSubsystemsDrawer() {
            const drawer = document.getElementById('subsystems-drawer');
            const overlay = document.getElementById('subsystems-overlay');
            if (drawer && overlay) {
                drawer.classList.remove('open');
                overlay.classList.remove('open');
            }
        }

        function renderSubsystemsList() {
            const container = document.getElementById('subsystems-list-container');
            if (!container || !rawDashboardState || !rawDashboardState.subsystems) return;

            const filter = (document.getElementById('subsystem-search-input')?.value || '').toLowerCase().trim();
            const list = rawDashboardState.subsystems.filter(s => {
                if (!filter) return true;
                return s.name.toLowerCase().includes(filter) || s.category.toLowerCase().includes(filter) || s.file_source.toLowerCase().includes(filter);
            });

            container.innerHTML = list.map((s, idx) => {
                const isOnline = s.status.includes('Ativo');
                const dotClass = isOnline ? 'online' : '';
                return `<div class="subsystem-item">
                    <div class="subsystem-item-header">
                        <div class="subsystem-item-title">
                            <div class="status-dot ${dotClass}" style="width:7px; height:7px;"></div>
                            <span>${idx + 1}. ${s.name}</span>
                        </div>
                        <span class="subsystem-cat-tag" style="background:${s.color}22; color:${s.color}; border:1px solid ${s.color}44;">${s.category}</span>
                    </div>
                    <div class="subsystem-item-body">
                        <div>Fonte: <code>${s.file_source}</code></div>
                        <div style="display:flex; justify-content:space-between; margin-top:4px;">
                            <span>Métrica: <b style="color:#e2e8f0;">${s.count_metric}</b></span>
                            <span>CPU: <b>${s.cpu_percent.toFixed(1)}%</b> | RAM: <b>${s.memory_mb.toFixed(1)}MB</b></span>
                        </div>
                    </div>
                </div>`;
            }).join('');
        }

        function filterSubsystems() {
            renderSubsystemsList();
        }

        function openOnlinePlayersModal() {
            const modal = document.getElementById('players-modal');
            if (modal) {
                modal.classList.add('open');
                fetchOnlinePlayers();
            }
        }

        function closeOnlinePlayersModal() {
            const modal = document.getElementById('players-modal');
            if (modal) modal.classList.remove('open');
        }

        async function fetchOnlinePlayers() {
            try {
                const res = await fetch('/api/players');
                const data = await res.json();
                const tbody = document.getElementById('players-table-body');
                const badge = document.getElementById('players-count-badge');
                if (badge) badge.innerText = `${data.length} Online`;

                if (tbody) {
                    if (!data || data.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:24px; color:#64748b;">Nenhum jogador conectado no momento.</td></tr>`;
                    } else {
                        tbody.innerHTML = data.map((p, i) => {
                            const hrs = Math.floor(p.duration_secs / 3600);
                            const mins = Math.floor((p.duration_secs % 3600) / 60);
                            const dur = `${hrs}h ${mins}m`;
                            return `<tr>
                                <td>${i + 1}</td>
                                <td><b>${escapeHtml(p.character_name)}</b></td>
                                <td>${escapeHtml(p.account_name)}</td>
                                <td><span class="brand-pill" style="background:rgba(16,185,129,0.15); color:#34d399;">${escapeHtml(p.server)}</span></td>
                                <td>${p.login_time}</td>
                                <td>${dur}</td>
                            </tr>`;
                        }).join('');
                    }
                }
            } catch (e) {
                console.error("Error fetching online players:", e);
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
                document.body.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; background:#070a12; color:#fff; font-family:sans-serif; gap:16px;">
                    <div style="font-size:1.5rem; font-weight:700; color:#38bdf8;">Emulador Java Encerrado</div>
                    <div style="color:#94a3b8; font-size:0.9rem;">Todos os servidores foram finalizados com segurança. Pode fechar esta janela.</div>
                </div>`;
            } catch (e) {
                console.error("Error shutting down:", e);
            }
        }

        // ==========================================
        // DATABASE STUDIO WORKBENCH FULL LOGIC
        // ==========================================
        let dbDatabases = [];
        let currentDbId = "game";
        let currentDbTable = null;
        let currentDbPage = 1;
        let currentDbLimit = 50;
        let currentDbSearch = "";
        let currentDbSortCol = null;
        let currentDbSortOrder = "ASC";
        let currentDbTab = "grid";
        let dbGroupCollapsed = {}; // Empty means ALL EXPANDED BY DEFAULT
        let isInsertingRow = false;
        let editingRowPk = null;
        let pendingConfirmAction = null;

        function openDbStudio() {
            document.getElementById('db-studio-modal').classList.add('open');
            dbGroupCollapsed = {}; // Expand all groups on open
            loadDbSchema();
        }

        function closeDbStudio() {
            document.getElementById('db-studio-modal').classList.remove('open');
        }

        function toggleMobileDbSidebar() {
            const sidebar = document.querySelector('.db-sidebar');
            if (sidebar) {
                sidebar.classList.toggle('mobile-open');
            }
        }

        async function loadDbSchema(preserveSelection = false) {
            try {
                const res = await fetch('/api/db/schema');
                const data = await res.json();
                if (data.status === 'ok') {
                    dbDatabases = data.databases || [];
                    const totalTables = data.total_tables || dbDatabases.reduce((acc, d) => acc + (d.table_count || 0), 0);
                    
                    const pill = document.getElementById('db-total-tables-pill');
                    if (pill) pill.innerText = `${totalTables} Tabelas (${dbDatabases.length} Bancos)`;
                    
                    const dbTablesEl = document.getElementById('val-db-tables');
                    if (dbTablesEl) dbTablesEl.innerText = `${totalTables} Tabelas (${dbDatabases.length} Bancos)`;

                    updateDbDropdowns();
                    renderTablesList();

                    if (!preserveSelection || !currentDbTable) {
                        let selected = false;
                        for (const db of dbDatabases) {
                            if (db.tables && db.tables.length > 0) {
                                selectDbTable(db.id, db.tables[0].name);
                                selected = true;
                                break;
                            }
                        }
                    } else {
                        loadTableData();
                    }
                }
            } catch (e) {
                console.error("Error loading DB schema:", e);
            }
        }

        function updateDbDropdowns() {
            const sqlTarget = document.getElementById('db-sql-target-db');
            const createTableTarget = document.getElementById('db-create-table-db-select');
            
            if (sqlTarget) {
                const prev = sqlTarget.value;
                sqlTarget.innerHTML = dbDatabases.map(d => `<option value="${d.id}">${d.filename} (${d.name})</option>`).join('');
                if (prev && dbDatabases.some(d => d.id === prev)) sqlTarget.value = prev;
                else if (dbDatabases.length > 0) sqlTarget.value = currentDbId || dbDatabases[0].id;
            }

            if (createTableTarget) {
                createTableTarget.innerHTML = dbDatabases.map(d => `<option value="${d.id}">${d.filename}</option>`).join('');
                if (currentDbId) createTableTarget.value = currentDbId;
            }
        }

        function onSqlDbChange() {
            const sel = document.getElementById('db-sql-target-db');
            if (sel) currentDbId = sel.value;
        }

        function toggleDbGroup(dbId) {
            dbGroupCollapsed[dbId] = !dbGroupCollapsed[dbId];
            renderTablesList();
        }

        function expandAllDbGroups(expand) {
            if (expand) {
                dbGroupCollapsed = {};
            } else {
                dbDatabases.forEach(db => {
                    dbGroupCollapsed[db.id] = true;
                });
            }
            renderTablesList();
        }

        function renderTablesList() {
            const filter = (document.getElementById('db-filter-table-input')?.value || '').toLowerCase().trim();
            const container = document.getElementById('db-tables-container');
            if (!container) return;

            const groupColors = {
                'login': 'var(--accent-login)',
                'game': 'var(--accent-game)',
                'chat': 'var(--accent-chat)',
                
            };

            let html = '';

            dbDatabases.forEach(db => {
                const color = groupColors[db.id] || 'var(--accent-login)';
                const matchingTables = (db.tables || []).filter(t => !filter || t.name.toLowerCase().includes(filter));
                
                if (filter && matchingTables.length === 0) return;

                const isCollapsed = filter ? false : (dbGroupCollapsed[db.id] === true);
                const openClass = isCollapsed ? '' : 'open';

                let tablesHtml = matchingTables.map(t => {
                    const activeClass = (currentDbId === db.id && currentDbTable === t.name) ? 'active' : '';
                    return `<div class="db-table-item ${activeClass}" onclick="selectDbTable('${db.id}', '${t.name}')">
                        <span style="display:flex; align-items:center; gap:6px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1;">
                            <span class="btn-svg" style="color:${color};"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg></span>
                            <span style="overflow:hidden; text-overflow:ellipsis;">${t.name}</span>
                        </span>
                        <div style="display:flex; align-items:center; gap:3px;">
                            <span class="db-table-badge">${t.row_count}</span>
                            <button class="db-action-btn-sm" onclick="event.stopPropagation(); openAddColumnModal('${t.name}', '${db.id}')" title="Adicionar Coluna">+C</button>
                            <button class="db-action-btn-sm" onclick="event.stopPropagation(); openRenameTableModal('${t.name}', '${db.id}')" title="Renomear Tabela">✎</button>
                            <button class="db-action-btn-sm danger" onclick="event.stopPropagation(); openDropTableModal('${t.name}', '${db.id}')" title="Excluir Tabela (DROP)">✕</button>
                        </div>
                    </div>`;
                }).join('');

                if (matchingTables.length === 0) {
                    tablesHtml = `<div style="padding:6px 12px; font-size:0.7rem; color:#64748b;">Nenhuma tabela encontrada</div>`;
                }

                const isCoreDb = ['login', 'game', 'chat'].includes(db.id);
                const deleteDbBtn = !isCoreDb ? `<button class="db-action-btn-sm danger" onclick="event.stopPropagation(); openDeleteDbModal('${db.id}', '${db.filename}')" title="Excluir Banco">✕</button>` : '';

                const sizeKB = (db.size_bytes / 1024).toFixed(0);

                html += `<div class="db-group ${openClass}">
                    <div class="db-group-header" onclick="toggleDbGroup('${db.id}')">
                        <div class="db-group-title">
                            <span class="btn-svg" style="color:${color};"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg></span>
                            <span>${db.name}</span>
                        </div>
                        <div class="db-group-meta">
                            <span class="db-table-badge" style="background:rgba(255,255,255,0.06); color:${color}; font-weight:700;">${db.table_count}</span>
                            <button class="db-action-btn-sm" onclick="event.stopPropagation(); openCreateTableModal('${db.id}')" title="Criar Tabela neste Banco">+T</button>
                            ${deleteDbBtn}
                            <span class="db-group-chevron">▶</span>
                        </div>
                    </div>
                    <div class="db-group-content">
                        ${tablesHtml}
                    </div>
                </div>`;
            });

            container.innerHTML = html || `<div style="text-align:center; padding:20px; font-size:0.75rem; color:#64748b;">Nenhum banco ou tabela encontrado.</div>`;
        }

        function filterTablesList() {
            renderTablesList();
        }

        function selectDbTable(dbId, tableName) {
            currentDbId = dbId;
            currentDbTable = tableName;
            currentDbPage = 1;
            currentDbSearch = "";
            currentDbSortCol = null;
            currentDbSortOrder = "ASC";
            if (document.getElementById('db-row-search-input')) {
                document.getElementById('db-row-search-input').value = "";
            }
            const sqlTarget = document.getElementById('db-sql-target-db');
            if (sqlTarget) sqlTarget.value = dbId;

            const schemaTitle = document.getElementById('db-schema-header-title');
            if (schemaTitle) schemaTitle.innerText = `Estrutura de '${tableName}' em '${dbId}.db'`;

            const sidebar = document.querySelector('.db-sidebar');
            if (sidebar && window.innerWidth <= 900) {
                sidebar.classList.remove('mobile-open');
            }
            renderTablesList();
            loadTableData();
            renderSchemaTab();
        }

        async function loadTableData(resetPage = false) {
            if (!currentDbTable) return;
            if (resetPage) currentDbPage = 1;

            try {
                let url = `/api/db/table/${encodeURIComponent(currentDbTable)}/rows?db=${encodeURIComponent(currentDbId)}&page=${currentDbPage}&limit=${currentDbLimit}`;
                if (currentDbSearch) url += `&search=${encodeURIComponent(currentDbSearch)}`;
                if (currentDbSortCol) url += `&sort=${encodeURIComponent(currentDbSortCol)}&order=${currentDbSortOrder}`;

                const res = await fetch(url);
                const json = await res.json();

                if (json.status === 'ok') {
                    renderGridData(json.data);
                } else {
                    alert("Erro ao carregar dados: " + json.message);
                }
            } catch (e) {
                console.error("Error loading table rows:", e);
            }
        }

        function renderGridData(data) {
            const thead = document.getElementById('db-table-head');
            const tbody = document.getElementById('db-table-body');
            if (!thead || !tbody) return;

            // Render Header
            let thHtml = `<th style="width:70px; text-align:center;">Ações</th>`;
            data.columns.forEach(col => {
                const isPk = col.pk;
                const pkBadge = isPk ? `<span class="db-pk-tag">PK</span>` : '';
                const sortIcon = (currentDbSortCol === col.name) ? (currentDbSortOrder === 'ASC' ? ' ▲' : ' ▼') : '';
                thHtml += `<th onclick="sortTableBy('${col.name}')">
                    ${col.name} ${pkBadge} <span style="font-size:0.62rem; color:#64748b;">(${col.type_name})</span><span style="color:var(--accent-login);">${sortIcon}</span>
                </th>`;
            });
            thead.innerHTML = `<tr>${thHtml}</tr>`;

            // Render Rows
            if (!data.rows || data.rows.length === 0) {
                tbody.innerHTML = `<tr><td colspan="${data.columns.length + 1}" style="text-align:center; padding:30px; color:#64748b;">Nenhum registro encontrado nesta tabela.</td></tr>`;
            } else {
                tbody.innerHTML = data.rows.map(row => {
                    const rowEncoded = encodeURIComponent(JSON.stringify(row));
                    let tdHtml = `<td style="text-align:center;">
                        <button class="filter-btn" style="padding:2px 5px; font-size:0.65rem;" onclick="openEditRowModal('${rowEncoded}')" title="Editar Linha">
                            <span class="btn-svg"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg></span>
                        </button>
                        <button class="filter-btn" style="padding:2px 5px; font-size:0.65rem; color:#f87171;" onclick="deleteRow('${rowEncoded}')" title="Excluir Linha">
                            <span class="btn-svg"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg></span>
                        </button>
                    </td>`;

                    data.columns.forEach(col => {
                        const val = row[col.name];
                        if (val === null || val === undefined) {
                            tdHtml += `<td><span class="db-null-val">NULL</span></td>`;
                        } else {
                            tdHtml += `<td title="${escapeHtml(String(val))}">${escapeHtml(String(val))}</td>`;
                        }
                    });

                    return `<tr>${tdHtml}</tr>`;
                }).join('');
            }

            // Update Pagination
            document.getElementById('db-total-rows-txt').innerText = data.total_rows;
            document.getElementById('db-page-info').innerText = `Página ${data.page} de ${data.total_pages}`;
            document.getElementById('db-prev-page-btn').disabled = data.page <= 1;
            document.getElementById('db-next-page-btn').disabled = data.page >= data.total_pages;
        }

        function sortTableBy(colName) {
            if (currentDbSortCol === colName) {
                currentDbSortOrder = currentDbSortOrder === 'ASC' ? 'DESC' : 'ASC';
            } else {
                currentDbSortCol = colName;
                currentDbSortOrder = 'ASC';
            }
            loadTableData(true);
        }

        function executeRowSearch() {
            currentDbSearch = (document.getElementById('db-row-search-input')?.value || '').trim();
            loadTableData(true);
        }

        function prevPage() {
            if (currentDbPage > 1) {
                currentDbPage--;
                loadTableData();
            }
        }

        function nextPage() {
            currentDbPage++;
            loadTableData();
        }

        function changePageLimit(limit) {
            currentDbLimit = parseInt(limit, 10);
            loadTableData(true);
        }

        function switchDbTab(tab) {
            currentDbTab = tab;
            document.querySelectorAll('.db-tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(`db-tab-${tab}`).classList.add('active');

            document.getElementById('db-view-grid').style.display = tab === 'grid' ? 'flex' : 'none';
            document.getElementById('db-view-schema').style.display = tab === 'schema' ? 'flex' : 'none';
            document.getElementById('db-view-sql').style.display = tab === 'sql' ? 'flex' : 'none';

            const gridControls = document.getElementById('db-grid-controls');
            const gridActions = document.getElementById('db-grid-actions');
            if (gridControls) gridControls.style.display = tab === 'grid' ? 'flex' : 'none';
            if (gridActions) gridActions.style.display = tab === 'grid' ? 'flex' : 'none';

            if (tab === 'schema') renderSchemaTab();
        }

        function renderSchemaTab() {
            if (!currentDbTable) return;
            const dbGroup = dbDatabases.find(d => d.id === currentDbId);
            const schema = dbGroup?.tables.find(s => s.name === currentDbTable);
            const tbody = document.getElementById('db-schema-table-body');
            if (!schema || !tbody) return;

            tbody.innerHTML = schema.columns.map((c, i) => {
                return `<tr>
                    <td>${i + 1}</td>
                    <td><b>${c.name}</b></td>
                    <td><span style="color:var(--accent-login); font-weight:600;">${c.type_name}</span></td>
                    <td>${c.pk ? '<span class="db-pk-tag">SIM (CHAVE PRIMÁRIA)</span>' : '<span style="color:#64748b;">NÃO</span>'}</td>
                    <td>${c.notnull ? '<span style="color:#f87171; font-weight:700;">SIM</span>' : '<span style="color:#64748b;">NÃO</span>'}</td>
                    <td>${c.dflt_value !== null ? `<code>${escapeHtml(c.dflt_value)}</code>` : '<span class="db-null-val">NULL</span>'}</td>
                </tr>`;
            }).join('');
        }

        // ==========================================
        // DATABASE & TABLE MANAGEMENT MODALS
        // ==========================================
        function openCreateDbModal() {
            document.getElementById('db-create-name-input').value = "";
            document.getElementById('db-create-db-modal').style.display = 'flex';
        }
        function closeCreateDbModal() {
            document.getElementById('db-create-db-modal').style.display = 'none';
        }
        async function submitCreateDb() {
            const name = (document.getElementById('db-create-name-input').value || '').trim();
            if (!name) {
                alert("Digite o nome do novo banco de dados.");
                return;
            }
            try {
                const res = await fetch('/api/db/database/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    closeCreateDbModal();
                    loadDbSchema(true);
                } else {
                    alert("Erro ao criar banco: " + json.message);
                }
            } catch (e) {
                alert("Erro de conexão: " + e);
            }
        }

        function openDeleteDbModal(dbId, filename) {
            openConfirmModal(
                "Excluir Banco de Dados",
                `Tem certeza que deseja excluir permanentemente o arquivo SQLite <b>${filename}</b>? Todos os dados gravados nele serão apagados.`,
                async () => {
                    try {
                        const res = await fetch(`/api/db/database/${encodeURIComponent(dbId)}`, { method: 'DELETE' });
                        const json = await res.json();
                        if (json.status === 'ok') {
                            loadDbSchema();
                        } else {
                            alert("Erro ao excluir banco: " + json.message);
                        }
                    } catch (e) {
                        alert("Erro: " + e);
                    }
                }
            );
        }

        function openCreateTableModal(preselectedDbId) {
            updateDbDropdowns();
            const dbSel = document.getElementById('db-create-table-db-select');
            if (dbSel && preselectedDbId) dbSel.value = preselectedDbId;
            else if (dbSel && currentDbId) dbSel.value = currentDbId;

            document.getElementById('db-create-table-name-input').value = "";
            
            const tbody = document.getElementById('db-create-table-columns-tbody');
            tbody.innerHTML = "";
            // Add default ID PK column
            addTableColumnRow("id", "INTEGER", true, true, "");
            addTableColumnRow("name", "TEXT", false, false, "");

            document.getElementById('db-create-table-modal').style.display = 'flex';
        }
        function closeCreateTableModal() {
            document.getElementById('db-create-table-modal').style.display = 'none';
        }

        function addTableColumnRow(name = "", type = "TEXT", isPk = false, notNull = false, dflt = "") {
            const tbody = document.getElementById('db-create-table-columns-tbody');
            const rowId = "col-row-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
            const tr = document.createElement('tr');
            tr.id = rowId;
            tr.innerHTML = `
                <td><input type="text" class="db-form-input col-name-in" style="padding:3px 6px; font-size:0.75rem;" value="${escapeHtml(name)}" placeholder="nome_coluna"></td>
                <td>
                    <select class="db-select-sm col-type-in" style="padding:3px;">
                        <option value="INTEGER" ${type==='INTEGER'?'selected':''}>INTEGER</option>
                        <option value="TEXT" ${type==='TEXT'?'selected':''}>TEXT</option>
                        <option value="REAL" ${type==='REAL'?'selected':''}>REAL</option>
                        <option value="BLOB" ${type==='BLOB'?'selected':''}>BLOB</option>
                    </select>
                </td>
                <td style="text-align:center;"><input type="checkbox" class="col-pk-in" ${isPk?'checked':''}></td>
                <td style="text-align:center;"><input type="checkbox" class="col-nn-in" ${notNull?'checked':''}></td>
                <td><input type="text" class="db-form-input col-dflt-in" style="padding:3px 6px; font-size:0.75rem;" value="${escapeHtml(dflt)}" placeholder="Padrão"></td>
                <td style="text-align:center;">
                    <button class="db-action-btn-sm danger" onclick="document.getElementById('${rowId}').remove()">✕</button>
                </td>
            `;
            tbody.appendChild(tr);
        }

        async function submitCreateTable() {
            const db = document.getElementById('db-create-table-db-select').value;
            const name = (document.getElementById('db-create-table-name-input').value || '').trim();
            if (!name) {
                alert("Digite o nome da tabela.");
                return;
            }

            const rows = document.querySelectorAll('#db-create-table-columns-tbody tr');
            const columns = [];
            rows.forEach(tr => {
                const colName = (tr.querySelector('.col-name-in')?.value || '').trim();
                const colType = tr.querySelector('.col-type-in')?.value || 'TEXT';
                const isPk = tr.querySelector('.col-pk-in')?.checked || false;
                const notNull = tr.querySelector('.col-nn-in')?.checked || false;
                const dflt = (tr.querySelector('.col-dflt-in')?.value || '').trim();

                if (colName) {
                    columns.push({
                        name: colName,
                        type_name: colType,
                        pk: isPk,
                        notnull: notNull,
                        dflt_value: dflt ? dflt : null
                    });
                }
            });

            if (columns.length === 0) {
                alert("Adicione ao menos uma coluna.");
                return;
            }

            try {
                const res = await fetch('/api/db/table/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ db, name, columns })
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    closeCreateTableModal();
                    currentDbId = db;
                    currentDbTable = name;
                    loadDbSchema(true);
                } else {
                    alert("Erro ao criar tabela: " + json.message);
                }
            } catch (e) {
                alert("Erro: " + e);
            }
        }

        function openDropTableModal(table, dbId) {
            if (!table) return;
            const targetDb = dbId || currentDbId;
            openConfirmModal(
                "Excluir Tabela (DROP TABLE)",
                `Tem certeza que deseja EXCLUIR permanentemente a tabela <b>${table}</b> do banco <b>${targetDb}.db</b>? Todos os registros e a estrutura serão apagados.`,
                async () => {
                    try {
                        const res = await fetch(`/api/db/table/${encodeURIComponent(table)}/drop?db=${encodeURIComponent(targetDb)}`, { method: 'DELETE' });
                        const json = await res.json();
                        if (json.status === 'ok') {
                            if (currentDbTable === table) currentDbTable = null;
                            loadDbSchema();
                        } else {
                            alert("Erro ao excluir tabela: " + json.message);
                        }
                    } catch (e) {
                        alert("Erro: " + e);
                    }
                }
            );
        }

        function openAddColumnModal(table, dbId) {
            if (!table) return;
            currentDbTable = table;
            currentDbId = dbId || currentDbId;
            document.getElementById('db-add-col-title').innerText = `Adicionar Coluna em '${table}' (${currentDbId}.db)`;
            document.getElementById('db-add-col-name-input').value = "";
            document.getElementById('db-add-col-type-select').value = "TEXT";
            document.getElementById('db-add-col-notnull-input').checked = false;
            document.getElementById('db-add-col-dflt-input').value = "";
            document.getElementById('db-add-col-modal').style.display = 'flex';
        }
        function closeAddColModal() {
            document.getElementById('db-add-col-modal').style.display = 'none';
        }
        async function submitAddColumn() {
            const name = (document.getElementById('db-add-col-name-input').value || '').trim();
            if (!name) {
                alert("Digite o nome da coluna.");
                return;
            }
            const type_name = document.getElementById('db-add-col-type-select').value;
            const notnull = document.getElementById('db-add-col-notnull-input').checked;
            const dflt = (document.getElementById('db-add-col-dflt-input').value || '').trim();

            const column = {
                name,
                type_name,
                pk: false,
                notnull,
                dflt_value: dflt ? dflt : null
            };

            try {
                const res = await fetch(`/api/db/table/${encodeURIComponent(currentDbTable)}/add_column`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ db: currentDbId, column })
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    closeAddColModal();
                    loadDbSchema(true);
                } else {
                    alert("Erro ao adicionar coluna: " + json.message);
                }
            } catch (e) {
                alert("Erro: " + e);
            }
        }

        function openRenameTableModal(table, dbId) {
            if (!table) return;
            currentDbTable = table;
            currentDbId = dbId || currentDbId;
            document.getElementById('db-rename-old-input').value = table;
            document.getElementById('db-rename-new-input').value = "";
            document.getElementById('db-rename-table-modal').style.display = 'flex';
        }
        function closeRenameTableModal() {
            document.getElementById('db-rename-table-modal').style.display = 'none';
        }
        async function submitRenameTable() {
            const new_name = (document.getElementById('db-rename-new-input').value || '').trim();
            if (!new_name) {
                alert("Digite o novo nome da tabela.");
                return;
            }
            try {
                const res = await fetch(`/api/db/table/${encodeURIComponent(currentDbTable)}/rename`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ db: currentDbId, new_name })
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    closeRenameTableModal();
                    currentDbTable = new_name;
                    loadDbSchema(true);
                } else {
                    alert("Erro ao renomear tabela: " + json.message);
                }
            } catch (e) {
                alert("Erro: " + e);
            }
        }

        function openConfirmModal(title, message, onConfirm) {
            document.getElementById('db-confirm-title').innerText = title;
            document.getElementById('db-confirm-message').innerHTML = message;
            pendingConfirmAction = onConfirm;
            document.getElementById('db-confirm-modal').style.display = 'flex';
        }
        function closeConfirmModal() {
            document.getElementById('db-confirm-modal').style.display = 'none';
            pendingConfirmAction = null;
        }
        function executePendingConfirmAction() {
            if (pendingConfirmAction) pendingConfirmAction();
            closeConfirmModal();
        }

        // Add / Edit Row Modal
        function openInsertRowModal() {
            if (!currentDbTable) return;
            isInsertingRow = true;
            editingRowPk = null;
            document.getElementById('db-row-modal-title').innerText = `Novo Registro em '${currentDbTable}' (${currentDbId}.db)`;

            const dbGroup = dbDatabases.find(d => d.id === currentDbId);
            const schema = dbGroup?.tables.find(s => s.name === currentDbTable);
            if (!schema) return;

            const form = document.getElementById('db-row-form-fields');
            form.innerHTML = schema.columns.map(col => {
                const isAutoPk = col.pk && col.type_name.toUpperCase().includes('INT');
                const placeholder = isAutoPk ? '(Auto-Increment)' : (col.dflt_value ? `Padrão: ${col.dflt_value}` : '');
                return `<div class="db-form-field">
                    <div class="db-form-label">
                        <span>${col.name} ${col.pk ? '<span class="db-pk-tag">PK</span>' : ''}</span>
                        <span style="font-size:0.65rem; color:#64748b;">${col.type_name}</span>
                    </div>
                    <input type="text" class="db-form-input" id="db-input-${col.name}" placeholder="${placeholder}">
                </div>`;
            }).join('');

            document.getElementById('db-row-modal').classList.add('open');
        }

        function openEditRowModal(encodedRowJson) {
            if (!currentDbTable) return;
            const row = JSON.parse(decodeURIComponent(encodedRowJson));
            const dbGroup = dbDatabases.find(d => d.id === currentDbId);
            const schema = dbGroup?.tables.find(s => s.name === currentDbTable);
            if (!schema) return;

            isInsertingRow = false;
            editingRowPk = {};
            schema.columns.filter(c => c.pk).forEach(c => {
                editingRowPk[c.name] = row[c.name];
            });

            document.getElementById('db-row-modal-title').innerText = `Editar Registro em '${currentDbTable}' (${currentDbId}.db)`;

            const form = document.getElementById('db-row-form-fields');
            form.innerHTML = schema.columns.map(col => {
                const val = row[col.name] !== null && row[col.name] !== undefined ? row[col.name] : '';
                return `<div class="db-form-field">
                    <div class="db-form-label">
                        <span>${col.name} ${col.pk ? '<span class="db-pk-tag">PK</span>' : ''}</span>
                        <span style="font-size:0.65rem; color:#64748b;">${col.type_name}</span>
                    </div>
                    <input type="text" class="db-form-input" id="db-input-${col.name}" value="${escapeHtml(String(val))}">
                </div>`;
            }).join('');

            document.getElementById('db-row-modal').classList.add('open');
        }

        function closeRowModal() {
            document.getElementById('db-row-modal').classList.remove('open');
        }

        async function saveRowData() {
            if (!currentDbTable) return;
            const dbGroup = dbDatabases.find(d => d.id === currentDbId);
            const schema = dbGroup?.tables.find(s => s.name === currentDbTable);
            if (!schema) return;

            const rowData = {};
            schema.columns.forEach(col => {
                const el = document.getElementById(`db-input-${col.name}`);
                if (el) {
                    let v = el.value.trim();
                    if (isInsertingRow && col.pk && col.type_name.toUpperCase().includes('INT') && v === '') {
                        return; // Let SQLite autoincrement
                    }
                    if (v === '' && !col.notnull) {
                        rowData[col.name] = null;
                    } else if (col.type_name.toUpperCase().includes('INT')) {
                        const num = parseInt(v, 10);
                        rowData[col.name] = isNaN(num) ? v : num;
                    } else if (col.type_name.toUpperCase().includes('REAL') || col.type_name.toUpperCase().includes('FLOAT')) {
                        const flt = parseFloat(v);
                        rowData[col.name] = isNaN(flt) ? v : flt;
                    } else {
                        rowData[col.name] = v;
                    }
                }
            });

            try {
                if (isInsertingRow) {
                    const res = await fetch(`/api/db/table/${encodeURIComponent(currentDbTable)}/row?db=${encodeURIComponent(currentDbId)}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(rowData)
                    });
                    const json = await res.json();
                    if (json.status === 'ok') {
                        closeRowModal();
                        loadDbSchema(true);
                    } else {
                        alert("Erro ao inserir registro: " + json.message);
                    }
                } else {
                    const res = await fetch(`/api/db/table/${encodeURIComponent(currentDbTable)}/row`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ db: currentDbId, pk: editingRowPk, updates: rowData })
                    });
                    const json = await res.json();
                    if (json.status === 'ok') {
                        closeRowModal();
                        loadTableData();
                    } else {
                        alert("Erro ao atualizar registro: " + json.message);
                    }
                }
            } catch (e) {
                alert("Erro ao comunicar com o servidor: " + e);
            }
        }

        async function deleteRow(encodedRowJson) {
            if (!currentDbTable) return;
            const row = JSON.parse(decodeURIComponent(encodedRowJson));
            const dbGroup = dbDatabases.find(d => d.id === currentDbId);
            const schema = dbGroup?.tables.find(s => s.name === currentDbTable);
            if (!schema) return;

            const pk = {};
            schema.columns.filter(c => c.pk).forEach(c => {
                pk[c.name] = row[c.name];
            });

            if (!confirm(`Tem certeza que deseja excluir o registro selecionado de '${currentDbTable}' (${currentDbId}.db)?`)) {
                return;
            }

            try {
                const res = await fetch(`/api/db/table/${encodeURIComponent(currentDbTable)}/row`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ db: currentDbId, pk })
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    loadDbSchema(true);
                } else {
                    alert("Erro ao excluir registro: " + json.message);
                }
            } catch (e) {
                alert("Erro ao excluir registro: " + e);
            }
        }

        async function truncateCurrentTable() {
            if (!currentDbTable) return;
            if (!confirm(`ATENÇÃO: Tem certeza que deseja limpar TODOS os registros da tabela '${currentDbTable}' em '${currentDbId}.db'?`)) {
                return;
            }

            try {
                const res = await fetch(`/api/db/table/${encodeURIComponent(currentDbTable)}/truncate?db=${encodeURIComponent(currentDbId)}`, {
                    method: 'POST'
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    loadDbSchema(true);
                } else {
                    alert("Erro ao limpar tabela: " + json.message);
                }
            } catch (e) {
                alert("Erro: " + e);
            }
        }

        function openCleanAllModal() {
            document.getElementById('clean-all-modal').style.display = 'flex';
        }
        function closeCleanAllModal() {
            document.getElementById('clean-all-modal').style.display = 'none';
        }

        async function confirmCleanAll() {
            closeCleanAllModal();
            try {
                const res = await fetch('/api/db/clean_all', { method: 'POST' });
                const json = await res.json();
                if (json.status === 'ok') {
                    alert("Todas as tabelas foram limpas com sucesso!");
                    loadDbSchema();
                } else {
                    alert("Erro ao limpar tabelas: " + json.message);
                }
            } catch (e) {
                alert("Erro ao comunicar com o servidor: " + e);
            }
        }

        // ==========================================
        // CUSTOM SQL CONSOLE & SCRIPT RUNNER
        // ==========================================
        let lastQueryColumns = [];
        let lastQueryRows = [];

        function setSqlTemplate(sql) {
            const input = document.getElementById('db-sql-input');
            if (input) input.value = sql;
            executeCustomSql();
        }

        function clearSqlConsole() {
            const input = document.getElementById('db-sql-input');
            if (input) input.value = "";
            const banner = document.getElementById('db-sql-status-banner');
            if (banner) banner.style.display = 'none';
            document.getElementById('db-sql-table-head').innerHTML = "";
            document.getElementById('db-sql-table-body').innerHTML = "";
            lastQueryColumns = [];
            lastQueryRows = [];
        }

        function handleSqlKeydown(e) {
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'Enter')) {
                e.preventDefault();
                executeCustomSql();
            }
        }

        function loadSqlFile(input) {
            if (!input.files || input.files.length === 0) return;
            const file = input.files[0];
            const reader = new FileReader();
            reader.onload = function(e) {
                const text = e.target.result;
                const editor = document.getElementById('db-sql-input');
                if (editor) editor.value = text;
            };
            reader.readAsText(file);
            input.value = "";
        }

        async function executeCustomSql() {
            const sql = (document.getElementById('db-sql-input')?.value || '').trim();
            if (!sql) return;

            const targetDb = document.getElementById('db-sql-target-db')?.value || currentDbId || 'game';
            const banner = document.getElementById('db-sql-status-banner');
            const thead = document.getElementById('db-sql-table-head');
            const tbody = document.getElementById('db-sql-table-body');

            try {
                const res = await fetch('/api/db/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ db: targetDb, sql })
                });
                const data = await res.json();

                if (data.status === 'ok') {
                    const r = data.result;
                    if (r.error) {
                        banner.style.display = 'block';
                        banner.style.background = 'rgba(239, 68, 68, 0.2)';
                        banner.style.color = '#fca5a5';
                        banner.innerText = `Erro na execução (${r.execution_time_ms.toFixed(1)}ms): ${r.error}`;
                        thead.innerHTML = '';
                        tbody.innerHTML = '';
                        lastQueryColumns = [];
                        lastQueryRows = [];
                    } else if (r.is_select) {
                        banner.style.display = 'block';
                        banner.style.background = 'rgba(16, 185, 129, 0.2)';
                        banner.style.color = '#a7f3d0';
                        banner.innerText = `Sucesso: ${r.rows.length} registros retornados em ${r.execution_time_ms.toFixed(1)}ms (${targetDb}.db)`;

                        lastQueryColumns = r.columns;
                        lastQueryRows = r.rows;

                        thead.innerHTML = `<tr>${r.columns.map(c => `<th>${c}</th>`).join('')}</tr>`;
                        tbody.innerHTML = r.rows.map(row => {
                            return `<tr>${row.map(v => `<td>${escapeHtml(v !== null ? String(v) : 'NULL')}</td>`).join('')}</tr>`;
                        }).join('');
                    } else {
                        banner.style.display = 'block';
                        banner.style.background = 'rgba(16, 185, 129, 0.2)';
                        banner.style.color = '#a7f3d0';
                        banner.innerText = `Script executado com sucesso: ${r.affected_rows} linha(s) modificada(s) em ${r.execution_time_ms.toFixed(1)}ms (${targetDb}.db)`;
                        thead.innerHTML = '';
                        tbody.innerHTML = '';
                        lastQueryColumns = [];
                        lastQueryRows = [];
                        loadDbSchema(true);
                    }
                }
            } catch (e) {
                banner.style.display = 'block';
                banner.style.background = 'rgba(239, 68, 68, 0.2)';
                banner.style.color = '#fca5a5';
                banner.innerText = `Erro de conexão: ${e}`;
            }
        }

        function exportSqlResultCsv() {
            if (!lastQueryColumns || lastQueryColumns.length === 0 || !lastQueryRows || lastQueryRows.length === 0) {
                alert("Nenhum resultado SQL disponível para exportar.");
                return;
            }
            let csv = lastQueryColumns.map(c => `"${c.replace(/"/g, '""')}"`).join(',') + '\n';
            lastQueryRows.forEach(row => {
                csv += row.map(v => `"${(v !== null ? String(v) : '').replace(/"/g, '""')}"`).join(',') + '\n';
            });
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `query_result_${Date.now()}.csv`;
            link.click();
        }

        function exportSqlResultJson() {
            if (!lastQueryColumns || lastQueryColumns.length === 0 || !lastQueryRows || lastQueryRows.length === 0) {
                alert("Nenhum resultado SQL disponível para exportar.");
                return;
            }
            const jsonArray = lastQueryRows.map(row => {
                const obj = {};
                lastQueryColumns.forEach((col, idx) => {
                    obj[col] = row[idx];
                });
                return obj;
            });
            const blob = new Blob([JSON.stringify(jsonArray, null, 2)], { type: 'application/json;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `query_result_${Date.now()}.json`;
            link.click();
        }

        function escapeHtml(text) {
            if (text === null || text === undefined) return "";
            return String(text)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        // Global Shortcuts: ESC / F12 to enter/exit Fullscreen Logs
        window.addEventListener('keydown', (e) => {
            if (e.key === 'F12' || e.code === 'F12') {
                e.preventDefault();
                toggleFullscreenLogs();
            } else if (e.key === 'Escape' || e.code === 'Escape') {
                if (isFullscreenLogsOpen()) {
                    e.preventDefault();
                    closeFullscreenLogs();
                }
            }
        });

        window.addEventListener('resize', () => {
            drawDayTradeChart();
            drawFullscreenFibonacciChart();
        });
        setInterval(fetchMetrics, 1000);
        setInterval(fetchLogs, 800);
        fetchMetrics();
        fetchLogs();
    </script>
</body>
</html>
"##;
