pub const HTML_DASHBOARD: &str = r##"<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aion Classic 5.0 - EMULADOR</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%230a101f'/><path d='M8 24 L16 8 L24 24 M11 19 L21 19' stroke='%2338bdf8' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/><circle cx='16' cy='14' r='2' fill='%23f59e0b'/></svg>">
    <style>
        :root {
            --bg-deep: #060913;
            --bg-surface: #0c1222;
            --bg-card: rgba(16, 24, 45, 0.75);
            --bg-card-hover: rgba(22, 34, 64, 0.9);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-focus: rgba(56, 189, 248, 0.4);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-cyan: #38bdf8;
            --accent-blue: #3b82f6;
            --accent-purple: #a855f7;
            --accent-amber: #f59e0b;
            --accent-emerald: #10b981;
            --accent-rose: #f43f5e;
            --accent-danger: #ef4444;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-full: 9999px;
            --font-main: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            --font-mono: "Cascadia Code", "Consolas", "Fira Code", monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-deep);
            color: var(--text-primary);
            font-family: var(--font-main);
            overflow: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
            user-select: none;
        }

        /* SVG icon sizing helper */
        .svg-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            fill: none;
            stroke: currentColor;
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
            flex-shrink: 0;
        }
        .svg-icon-sm { width: 13px; height: 13px; }
        .svg-icon-lg { width: 20px; height: 20px; }

        /* Top Header */
        header {
            height: 58px;
            background: rgba(10, 16, 31, 0.95);
            border-bottom: 1px solid var(--border-subtle);
            backdrop-filter: blur(12px);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 50;
        }
        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .brand-badge {
            background: linear-gradient(135deg, #1e3a8a, #0284c7);
            color: #fff;
            font-weight: 800;
            font-size: 0.8rem;
            padding: 5px 9px;
            border-radius: var(--radius-sm);
            letter-spacing: 0.5px;
            box-shadow: 0 0 12px rgba(2, 132, 199, 0.4);
        }
        .brand-title {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.8px;
            background: linear-gradient(90deg, #ffffff, #93c5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-tag {
            font-size: 0.68rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: var(--radius-full);
            background: rgba(56, 189, 248, 0.12);
            color: var(--accent-cyan);
            border: 1px solid rgba(56, 189, 248, 0.25);
            letter-spacing: 0.5px;
        }
        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 7px 14px;
            border-radius: var(--radius-sm);
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.15s ease;
            outline: none;
        }
        .btn:disabled, .btn.disabled {
            opacity: 0.35 !important;
            cursor: not-allowed !important;
            pointer-events: none !important;
            filter: grayscale(0.8) !important;
        }
        .btn-primary {
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: #ffffff;
            border-color: rgba(56, 189, 248, 0.3);
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.3);
        }
        .btn-primary:hover:not(:disabled) {
            background: linear-gradient(135deg, #0369a1, #075985);
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.5);
            transform: translateY(-1px);
        }
        .btn-danger {
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border-color: rgba(239, 68, 68, 0.3);
        }
        .btn-danger:hover:not(:disabled) {
            background: rgba(239, 68, 68, 0.25);
            color: #fee2e2;
            border-color: rgba(239, 68, 68, 0.5);
            transform: translateY(-1px);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-secondary);
            border-color: var(--border-subtle);
        }
        .btn-secondary:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.09);
            color: var(--text-primary);
        }
        .btn-compact {
            background: rgba(168, 85, 247, 0.12);
            color: #d8b4fe;
            border-color: rgba(168, 85, 247, 0.3);
        }
        .btn-compact:hover:not(:disabled) {
            background: rgba(168, 85, 247, 0.22);
            color: #f3e8ff;
            transform: translateY(-1px);
        }

        /* Layout Container */
        .app-body {
            display: flex;
            flex: 1;
            height: calc(100vh - 58px);
            overflow: hidden;
        }

        /* Left Sidebar */
        aside {
            width: 230px;
            background: rgba(10, 15, 29, 0.95);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 16px 10px;
            flex-shrink: 0;
        }
        .nav-list {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .nav-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 12px;
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            font-size: 0.82rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
        }
        .nav-item:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.04);
        }
        .nav-item.active {
            color: var(--accent-cyan);
            background: rgba(56, 189, 248, 0.1);
            font-weight: 600;
            border-left: 3px solid var(--accent-cyan);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        }

        /* Sidebar Bottom KPIs */
        .side-kpis {
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 0.74rem;
        }
        .side-kpi-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .side-kpi-row span { color: var(--text-muted); }
        .side-kpi-row b { font-family: var(--font-mono); color: var(--text-primary); }

        /* Main Content Stage */
        main {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 18px 24px;
            display: flex;
            flex-direction: column;
            background: radial-gradient(circle at 85% 10%, rgba(30, 58, 138, 0.15), transparent 40%),
                        radial-gradient(circle at 15% 90%, rgba(16, 185, 129, 0.08), transparent 35%);
        }
        main::-webkit-scrollbar { width: 6px; height: 6px; }
        main::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
        main::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 3px; }
        main::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

        .tab-content { display: none; height: 100%; flex-direction: column; gap: 18px; }
        .tab-content.active { display: flex; }

        /* Header Info Row */
        .stage-header {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        .stage-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 0.3px;
        }
        .stage-subtitle {
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        /* 4 KPI Cards Grid */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
        }
        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 14px 16px;
            backdrop-filter: blur(8px);
            display: flex;
            flex-direction: column;
            gap: 4px;
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, var(--border-focus), transparent);
        }
        .kpi-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 0.6px;
        }
        .kpi-value {
            font-size: 1.4rem;
            font-weight: 700;
            font-family: var(--font-mono);
            color: #ffffff;
        }
        .kpi-sub {
            font-size: 0.72rem;
            color: var(--text-muted);
        }

        /* Server Cards Grid */
        .section-label {
            font-size: 0.84rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .servers-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
            gap: 14px;
        }
        .server-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: all 0.2s ease;
            position: relative;
        }
        .server-card:hover {
            border-color: rgba(255, 255, 255, 0.15);
            background: var(--bg-card-hover);
        }
        .server-card.border-chat { border-top: 3px solid #00CED1; }
        .server-card.border-login { border-top: 3px solid #FFD700; }
        .server-card.border-remake { border-top: 3px solid #10B981; }
        .server-card.border-battleroyale { border-top: 3px solid #F97316; }
        .server-card.border-gameforge { border-top: 3px solid #38BDF8; }

        .sc-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        .sc-title-group {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .sc-title {
            font-size: 0.92rem;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .sc-tag {
            font-size: 0.68rem;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
        }
        .sc-tag-gsid {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 1px 5px;
            border-radius: 4px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .sc-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }

        /* Status Badge */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 3px 8px;
            border-radius: var(--radius-full);
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            border: 1px solid var(--border-subtle);
        }
        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--text-muted);
        }
        .status-pill.online {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border-color: rgba(16, 185, 129, 0.3);
        }
        .status-pill.online .status-dot {
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
        }
        .status-pill.starting {
            background: rgba(245, 158, 11, 0.12);
            color: #fbbf24;
            border-color: rgba(245, 158, 11, 0.3);
        }
        .status-pill.starting .status-dot {
            background: #f59e0b;
            box-shadow: 0 0 8px #f59e0b;
        }
        .status-pill.crashed {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border-color: rgba(239, 68, 68, 0.35);
        }
        .status-pill.crashed .status-dot {
            background: #ef4444;
            box-shadow: 0 0 8px #ef4444;
        }

        /* Card Metrics Grid */
        .sc-metrics {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px 12px;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: var(--radius-sm);
            padding: 8px 10px;
        }
        .sc-metric-item {
            display: flex;
            flex-direction: column;
            gap: 1px;
        }
        .sc-metric-label {
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }
        .sc-metric-val {
            font-size: 0.84rem;
            font-weight: 700;
            font-family: var(--font-mono);
            color: #ffffff;
        }

        /* Card Actions */
        .sc-actions {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 6px;
        }
        .sc-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            padding: 6px 8px;
            font-size: 0.72rem;
            font-weight: 600;
            border-radius: var(--radius-sm);
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.12s ease;
        }
        .sc-btn:disabled, .sc-btn.disabled {
            opacity: 0.3 !important;
            cursor: not-allowed !important;
            pointer-events: none !important;
            filter: grayscale(1) !important;
        }
        .sc-btn-start {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border-color: rgba(16, 185, 129, 0.35);
        }
        .sc-btn-start:hover:not(:disabled) {
            background: rgba(16, 185, 129, 0.28);
            color: #6ee7b7;
        }
        .sc-btn-stop {
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border-color: rgba(239, 68, 68, 0.35);
        }
        .sc-btn-stop:hover:not(:disabled) {
            background: rgba(239, 68, 68, 0.28);
            color: #fee2e2;
        }
        .sc-btn-restart {
            background: rgba(245, 158, 11, 0.15);
            color: #fcd34d;
            border-color: rgba(245, 158, 11, 0.35);
        }
        .sc-btn-restart:hover:not(:disabled) {
            background: rgba(245, 158, 11, 0.28);
            color: #fef08a;
        }

        /* Integrated Terminal Console (Dashboard Bottom) */
        .dash-terminal-container {
            flex: 1;
            min-height: 260px;
            background: rgba(6, 10, 20, 0.95);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
        }
        .term-header {
            height: 38px;
            background: rgba(12, 18, 36, 0.9);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 14px;
            flex-shrink: 0;
        }
        .term-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.74rem;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .term-filters {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .term-pill {
            font-size: 0.68rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: var(--radius-full);
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.12s ease;
        }
        .term-pill:hover { color: var(--text-primary); background: rgba(255, 255, 255, 0.09); }
        .term-pill.active {
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-cyan);
            border-color: rgba(56, 189, 248, 0.35);
        }
        .term-actions {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .term-action-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .term-action-btn:hover { color: var(--text-primary); background: rgba(255, 255, 255, 0.08); }
        .term-action-btn.active { color: var(--accent-cyan); }

        .term-body {
            flex: 1;
            overflow-y: auto;
            padding: 10px 14px;
            font-family: var(--font-mono);
            font-size: 0.73rem;
            line-height: 1.5;
            color: #e2e8f0;
            background: #050811;
        }
        .term-body::-webkit-scrollbar { width: 6px; }
        .term-body::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 3px; }

        .log-entry {
            display: flex;
            gap: 8px;
            margin-bottom: 2px;
            word-break: break-all;
        }
        .log-time { color: var(--text-muted); flex-shrink: 0; }
        .log-tag {
            font-weight: 700;
            padding: 0 4px;
            border-radius: 3px;
            flex-shrink: 0;
            font-size: 0.68rem;
        }
        .log-tag-chat { background: rgba(0, 206, 209, 0.15); color: #00CED1; }
        .log-tag-login { background: rgba(255, 215, 0, 0.15); color: #FFD700; }
        .log-tag-remake { background: rgba(16, 185, 129, 0.15); color: #10B981; }
        .log-tag-gameforge { background: rgba(56, 189, 248, 0.15); color: #38BDF8; }
        .log-tag-battleroyale { background: rgba(249, 115, 22, 0.15); color: #F97316; }
        .log-tag-launcher { background: rgba(168, 85, 247, 0.15); color: #C084FC; }

        .log-text { color: #cbd5e1; flex: 1; }
        .log-text.warn { color: #fde047; }
        .log-text.error { color: #f87171; font-weight: 600; }
        .log-text.info { color: #93c5fd; }
        .log-text.success { color: #86efac; }

        /* Fibonacci GS View */
        .fib-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 16px;
            height: 100%;
        }
        .fib-chart-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .fib-chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .fib-canvas-wrap {
            flex: 1;
            position: relative;
            background: #050811;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--radius-sm);
            overflow: hidden;
        }
        canvas.fib-canvas {
            width: 100%;
            height: 100%;
            display: block;
        }
        .fib-levels {
            display: flex;
            gap: 12px;
            font-size: 0.68rem;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }
        .fib-level-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

        /* Properties Manager Segregated UI */
        .prop-wrap {
            display: flex;
            flex-direction: column;
            gap: 12px;
            height: 100%;
        }
        .prop-server-tabs {
            display: flex;
            gap: 6px;
            border-bottom: 1px solid var(--border-subtle);
            padding-bottom: 8px;
        }
        .prop-srv-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            font-size: 0.78rem;
            font-weight: 600;
            border-radius: var(--radius-sm);
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-secondary);
            border: 1px solid var(--border-subtle);
            cursor: pointer;
            transition: all 0.12s ease;
        }
        .prop-srv-btn:hover { color: var(--text-primary); background: rgba(255, 255, 255, 0.08); }
        .prop-srv-btn.active {
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-cyan);
            border-color: rgba(56, 189, 248, 0.4);
        }

        .prop-main-stage {
            display: grid;
            grid-template-columns: 260px 1fr;
            gap: 14px;
            flex: 1;
            min-height: 0;
        }
        .prop-file-list {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .prop-search-box {
            padding: 10px;
            border-bottom: 1px solid var(--border-subtle);
        }
        .prop-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-sm);
            color: #ffffff;
            padding: 6px 10px;
            font-size: 0.74rem;
            outline: none;
        }
        .prop-input:focus { border-color: var(--accent-cyan); }
        .prop-files-scroll {
            flex: 1;
            overflow-y: auto;
            padding: 6px;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        .prop-file-item {
            padding: 8px 10px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 2px;
            transition: all 0.12s ease;
        }
        .prop-file-item:hover { background: rgba(255, 255, 255, 0.05); }
        .prop-file-item.active { background: rgba(56, 189, 248, 0.15); border-left: 3px solid var(--accent-cyan); }
        .prop-file-name { font-size: 0.76rem; font-weight: 600; color: #ffffff; }
        .prop-file-cat { font-size: 0.65rem; color: var(--text-muted); }

        .prop-editor-pane {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .prop-editor-top {
            height: 44px;
            padding: 0 16px;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(12, 18, 36, 0.7);
        }
        .prop-editor-scroll {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .prop-category-block {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--radius-sm);
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .prop-category-title {
            font-size: 0.74rem;
            font-weight: 700;
            color: var(--accent-cyan);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .prop-row {
            display: grid;
            grid-template-columns: 220px 1fr;
            gap: 10px;
            align-items: center;
        }
        .prop-key {
            font-size: 0.73rem;
            font-family: var(--font-mono);
            color: #e2e8f0;
            word-break: break-all;
        }
        .prop-val-input {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-sm);
            color: #ffffff;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            padding: 6px 10px;
            outline: none;
        }
        .prop-val-input:focus { border-color: var(--accent-cyan); }

        /* Database Studio Embedded UI */
        .db-studio-wrap {
            display: flex;
            flex-direction: column;
            gap: 12px;
            height: 100%;
        }
        .db-srv-tabs {
            display: flex;
            gap: 6px;
            border-bottom: 1px solid var(--border-subtle);
            padding-bottom: 8px;
        }
        .db-stage-grid {
            display: grid;
            grid-template-columns: 240px 1fr;
            gap: 14px;
            flex: 1;
            min-height: 0;
        }
        .db-schema-panel {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .db-tables-list {
            flex: 1;
            overflow-y: auto;
            padding: 6px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .db-table-item {
            padding: 7px 10px;
            border-radius: var(--radius-sm);
            font-size: 0.74rem;
            font-family: var(--font-mono);
            color: #cbd5e1;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .db-table-item:hover { background: rgba(255, 255, 255, 0.05); color: #fff; }
        .db-table-item.active { background: rgba(2, 132, 199, 0.2); color: var(--accent-cyan); font-weight: 600; }
        .db-table-cnt { font-size: 0.65rem; color: var(--text-muted); }

        .db-data-panel {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .db-data-top {
            height: 42px;
            background: rgba(12, 18, 36, 0.7);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 14px;
        }
        .db-grid-scroll {
            flex: 1;
            overflow: auto;
            background: #050811;
        }
        .db-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.72rem;
            font-family: var(--font-mono);
        }
        .db-table th {
            position: sticky;
            top: 0;
            background: #0d1527;
            color: var(--accent-cyan);
            padding: 7px 10px;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
            font-weight: 600;
            white-space: nowrap;
            z-index: 10;
        }
        .db-table td {
            padding: 6px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            color: #e2e8f0;
            white-space: nowrap;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .db-table tr:hover td { background: rgba(255, 255, 255, 0.03); }

        .db-sql-console {
            height: 120px;
            background: #070b16;
            border-top: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            padding: 8px 12px;
            gap: 6px;
        }
        .db-sql-textarea {
            flex: 1;
            background: transparent;
            border: none;
            color: #a5f3fc;
            font-family: var(--font-mono);
            font-size: 0.74rem;
            resize: none;
            outline: none;
        }

        /* Compact Mode Widget Container */
        #compact-widget-container {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(10, 15, 29, 0.88);
            backdrop-filter: blur(16px);
            padding: 14px;
            flex-direction: column;
            justify-content: space-between;
            z-index: 9999;
        }
        body.compact-mode #compact-widget-container { display: flex; }
        body.compact-mode header,
        body.compact-mode aside,
        body.compact-mode main { display: none !important; }

        .cw-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .cw-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .cw-grid {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin: 10px 0;
        }
        .cw-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--radius-sm);
            padding: 6px 10px;
        }
        .cw-server-info {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .cw-metrics {
            font-size: 0.7rem;
            font-family: var(--font-mono);
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .cw-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.7rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-subtle);
            padding-top: 8px;
        }

        /* Toast notifications */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #0f172a;
            border: 1px solid var(--accent-cyan);
            border-radius: var(--radius-sm);
            padding: 10px 16px;
            color: #fff;
            font-size: 0.78rem;
            font-weight: 600;
            display: none;
            align-items: center;
            gap: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            z-index: 10000;
        }
    </style>
</head>
<body>

    <!-- SVG Definitions -->
    <svg style="display:none;">
      <defs>
        <g id="icon-dash"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></g>
        <g id="icon-server"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></g>
        <g id="icon-config"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></g>
        <g id="icon-db"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></g>
        <g id="icon-terminal"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></g>
        <g id="icon-network"><rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/><line x1="12" y1="12" x2="12" y2="8"/></g>
        <g id="icon-play"><polygon points="5 3 19 12 5 21 5 3"/></g>
        <g id="icon-stop"><rect x="4" y="4" width="16" height="16" rx="2"/></g>
        <g id="icon-refresh"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></g>
        <g id="icon-compact"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/></g>
        <g id="icon-expand"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></g>
        <g id="icon-copy"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></g>
        <g id="icon-trash"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></g>
        <g id="icon-search"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></g>
        <g id="icon-download"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></g>
        <g id="icon-check"><polyline points="20 6 9 17 4 12"/></g>
        <g id="icon-save"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></g>
        <g id="icon-activity"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></g>
        <g id="icon-cpu"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></g>
      </defs>
    </svg>

    <!-- Header -->
    <header>
        <div class="header-brand">
            <div class="brand-badge">A5</div>
            <div class="brand-title">AION CLASSIC 5.0</div>
            <div class="brand-tag">MULTI-GAMESERVER</div>
        </div>
        <div class="header-actions">
            <button id="btn-orchestrate" class="btn btn-primary" onclick="startOrchestrated()">
                <svg class="svg-icon svg-icon-sm"><use href="#icon-play"/></svg>
                <span>Iniciar Orquestrado (CS → LS → GS)</span>
            </button>
            <button id="btn-stop-all" class="btn btn-danger" onclick="stopAllServers()">
                <svg class="svg-icon svg-icon-sm"><use href="#icon-stop"/></svg>
                <span>Parar Todos</span>
            </button>
            <button id="btn-restart-all" class="btn btn-secondary" onclick="restartAllServers()">
                <svg class="svg-icon svg-icon-sm"><use href="#icon-refresh"/></svg>
                <span>Reiniciar</span>
            </button>
            <button class="btn btn-compact" onclick="toggleCompactMode()" title="Alternar Modo Compacto (Mini Widget)">
                <svg class="svg-icon svg-icon-sm"><use href="#icon-compact"/></svg>
                <span>Modo Compacto</span>
            </button>
        </div>
    </header>

    <!-- App Body -->
    <div class="app-body">
        <!-- Sidebar -->
        <aside>
            <nav class="nav-list">
                <a class="nav-item active" onclick="switchTab('dashboard', this)">
                    <svg class="svg-icon"><use href="#icon-dash"/></svg>
                    <span>Visão Geral</span>
                </a>
                <a class="nav-item" onclick="switchTab('gs-servers', this)">
                    <svg class="svg-icon"><use href="#icon-server"/></svg>
                    <span>Servidores GS</span>
                </a>
                <a class="nav-item" onclick="switchTab('properties', this)">
                    <svg class="svg-icon"><use href="#icon-config"/></svg>
                    <span>Configurações</span>
                </a>
                <a class="nav-item" onclick="switchTab('database', this)">
                    <svg class="svg-icon"><use href="#icon-db"/></svg>
                    <span>Banco de Dados</span>
                </a>
                <a class="nav-item" onclick="switchTab('logs', this)">
                    <svg class="svg-icon"><use href="#icon-terminal"/></svg>
                    <span>Logs & Console</span>
                </a>
                <a class="nav-item" onclick="switchTab('network', this)">
                    <svg class="svg-icon"><use href="#icon-network"/></svg>
                    <span>Arquitetura & Portas</span>
                </a>
            </nav>

            <div class="side-kpis">
                <div class="side-kpi-row"><span>CPU Total:</span><b id="side-cpu">0.0%</b></div>
                <div class="side-kpi-row"><span>RAM Total:</span><b id="side-ram">0 MB</b></div>
                <div class="side-kpi-row"><span>Jogadores:</span><b id="side-players">0</b></div>
                <div class="side-kpi-row"><span>Tempo Ativo:</span><b id="side-uptime">00:00:00</b></div>
            </div>
        </aside>

        <!-- Main Content -->
        <main>
            <!-- Tab 1: Dashboard -->
            <div id="tab-dashboard" class="tab-content active">
                <div class="stage-header">
                    <div class="stage-title">Painel Geral de Operações</div>
                    <div class="stage-subtitle">Monitoramento em tempo real dos serviços ativos e GameServers independentes</div>
                </div>

                <!-- 4 KPI Cards -->
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">Status do Cluster</div>
                        <div class="kpi-value" id="kpi-cluster-status">Serviços Parados</div>
                        <div class="kpi-sub" id="kpi-cluster-count">0 de 4 serviços online</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Uso de CPU Host</div>
                        <div class="kpi-value" id="kpi-cpu-text">0.0%</div>
                        <div class="kpi-sub">Alocação dinâmica do cluster</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Uso de Memória RAM</div>
                        <div class="kpi-value" id="kpi-ram-text">0 MB</div>
                        <div class="kpi-sub" id="kpi-host-ram">RAM Host: 0 / 0 MB</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Jogadores Conectados</div>
                        <div class="kpi-value" id="kpi-players-count">0</div>
                        <div class="kpi-sub">Sincronização MySQL em tempo real</div>
                    </div>
                </div>

                <!-- Server Instances Grid -->
                <div class="section-label">
                    <svg class="svg-icon svg-icon-sm"><use href="#icon-server"/></svg>
                    <span>Instâncias de Servidores Habilitadas</span>
                </div>
                <div class="servers-grid" id="servers-container">
                    <!-- Populated by renderMetrics -->
                </div>

                <!-- Integrated Real-Time Terminal Console -->
                <div class="section-label" style="margin-top: 4px;">
                    <svg class="svg-icon svg-icon-sm"><use href="#icon-terminal"/></svg>
                    <span>Terminal de Logs Centralizado</span>
                </div>
                <div class="dash-terminal-container">
                    <div class="term-header">
                        <div class="term-title">
                            <span class="status-dot online"></span>
                            <span>Console de Eventos ao Vivo</span>
                        </div>
                        <div class="term-filters" id="term-filters-pills">
                            <button class="term-pill active" onclick="setLogFilter('all', this)">Todos</button>
                            <button class="term-pill" onclick="setLogFilter('chat', this)">Chat</button>
                            <button class="term-pill" onclick="setLogFilter('login', this)">Login</button>
                            <button class="term-pill" onclick="setLogFilter('remake', this)">Remake</button>
                            <button class="term-pill" onclick="setLogFilter('battleroyale', this)">BattleRoyale</button>
                            <button class="term-pill" onclick="setLogFilter('launcher', this)">Launcher</button>
                        </div>
                        <div class="term-actions">
                            <button class="term-action-btn" id="btn-autoscroll" onclick="toggleAutoScroll()" title="Fixar rolagem automática">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-activity"/></svg>
                            </button>
                            <button class="term-action-btn" onclick="clearLogsConsole()" title="Limpar console">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-trash"/></svg>
                            </button>
                            <button class="term-action-btn" onclick="copyConsoleLogs()" title="Copiar logs">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-copy"/></svg>
                            </button>
                        </div>
                    </div>
                    <div class="term-body" id="dash-log-body">
                        <!-- Populated by fetchLogs -->
                    </div>
                </div>
            </div>

            <!-- Tab 2: Servidores GS (Fibonacci Telemetry) -->
            <div id="tab-gs-servers" class="tab-content">
                <div class="stage-header">
                    <div class="stage-title">Servidores GS & Telemetria Fibonacci</div>
                    <div class="stage-subtitle">Análise avançada por proporção áurea, latência de tick e taxa de transferência</div>
                </div>
                <div class="fib-container">
                    <div class="fib-chart-card">
                        <div class="fib-chart-header">
                            <div class="section-label">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-activity"/></svg>
                                <span>Retração de Fibonacci (Throughput & Tick Rate)</span>
                            </div>
                            <div class="fib-levels">
                                <span><span class="fib-level-dot" style="background:#ef4444;"></span> 100.0%</span>
                                <span><span class="fib-level-dot" style="background:#f97316;"></span> 61.8%</span>
                                <span><span class="fib-level-dot" style="background:#eab308;"></span> 50.0%</span>
                                <span><span class="fib-level-dot" style="background:#10b981;"></span> 38.2%</span>
                                <span><span class="fib-level-dot" style="background:#38bdf8;"></span> 23.6%</span>
                            </div>
                        </div>
                        <div class="fib-canvas-wrap">
                            <canvas id="fib-canvas" class="fib-canvas"></canvas>
                        </div>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <div class="kpi-card">
                            <div class="kpi-label">Proporção Áurea de Loop (Tick)</div>
                            <div class="kpi-value" id="fib-tick-val">16.18 ms</div>
                            <div class="kpi-sub">Target ideal: 16.0ms (60 TPS MMORPG)</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Throughput de Pacotes</div>
                            <div class="kpi-value" id="fib-packet-rate">0 pkt/s</div>
                            <div class="kpi-sub">Game Loop Network I/O</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Heap Memory Tiering</div>
                            <div class="kpi-value">1GB → 4GB</div>
                            <div class="kpi-sub">JVM Xms 1024M / Xmx 4096M</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 3: Configurações (.properties) -->
            <div id="tab-properties" class="tab-content">
                <div class="stage-header">
                    <div class="stage-title">Gerenciador de Configurações (.properties)</div>
                    <div class="stage-subtitle">Isolamento rigoroso por servidor com backup automático (.bak)</div>
                </div>
                <div class="prop-wrap">
                    <div class="prop-server-tabs" id="prop-srv-tabs">
                        <button class="prop-srv-btn active" onclick="selectPropServer('remake', this)">[RM] Remake (GSID 2)</button>
                        <button class="prop-srv-btn" onclick="selectPropServer('gameforge', this)">[GF] GameForge (GSID 1)</button>
                        <button class="prop-srv-btn" onclick="selectPropServer('battleroyale', this)">[BR] BattleRoyale (GSID 3)</button>
                        <button class="prop-srv-btn" onclick="selectPropServer('login', this)">[LS] Login Server</button>
                        <button class="prop-srv-btn" onclick="selectPropServer('chat', this)">[CS] Chat Server</button>
                    </div>
                    <div class="prop-main-stage">
                        <div class="prop-file-list">
                            <div class="prop-search-box">
                                <input type="text" class="prop-input" id="prop-file-search" placeholder="Buscar arquivo..." oninput="filterPropFiles()">
                            </div>
                            <div class="prop-files-scroll" id="prop-files-list">
                                <!-- Populated dynamically -->
                            </div>
                        </div>
                        <div class="prop-editor-pane">
                            <div class="prop-editor-top">
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <svg class="svg-icon svg-icon-sm"><use href="#icon-config"/></svg>
                                    <span id="prop-current-filename" style="font-size:0.8rem; font-weight:700; color:#fff;">Selecione um arquivo</span>
                                </div>
                                <button class="btn btn-primary" onclick="saveCurrentProperties()">
                                    <svg class="svg-icon svg-icon-sm"><use href="#icon-save"/></svg>
                                    <span>Salvar Alterações (.bak)</span>
                                </button>
                            </div>
                            <div class="prop-editor-scroll" id="prop-editor-content">
                                <div style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding-top:40px;">
                                    Selecione um arquivo de configuração na lista lateral para editar.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 4: Banco de Dados (Database Studio) -->
            <div id="tab-database" class="tab-content">
                <div class="stage-header">
                    <div class="stage-title">Database Studio & Workbench</div>
                    <div class="stage-subtitle">Editor visual e console SQL para os 5 bancos de dados do ecossistema</div>
                </div>
                <div class="db-studio-wrap">
                    <div class="db-srv-tabs" id="db-srv-tabs">
                        <button class="prop-srv-btn active" onclick="selectDbStudio('cs', this)">[CS] aionclassic_cs</button>
                        <button class="prop-srv-btn" onclick="selectDbStudio('ls', this)">[LS] aionclassic_ls</button>
                        <button class="prop-srv-btn" onclick="selectDbStudio('remake', this)">[RM] aionclassic_gs2</button>
                        <button class="prop-srv-btn" onclick="selectDbStudio('gameforge', this)">[GF] aionclassic_gs</button>
                        <button class="prop-srv-btn" onclick="selectDbStudio('battleroyale', this)">[BR] aionclassic_gs3</button>
                    </div>
                    <div class="db-stage-grid">
                        <div class="db-schema-panel">
                            <div class="prop-search-box">
                                <input type="text" class="prop-input" id="db-table-search" placeholder="Filtrar tabelas..." oninput="filterDbTables()">
                            </div>
                            <div class="db-tables-list" id="db-tables-list">
                                <!-- Populated dynamically -->
                            </div>
                        </div>
                        <div class="db-data-panel">
                            <div class="db-data-top">
                                <span id="db-active-table-name" style="font-size:0.8rem; font-weight:700; font-family:var(--font-mono); color:#fff;">Tabela: --</span>
                                <div style="display:flex; gap:6px;">
                                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:0.7rem;" onclick="exportTableData('csv')">
                                        <svg class="svg-icon svg-icon-sm"><use href="#icon-download"/></svg> CSV
                                    </button>
                                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:0.7rem;" onclick="exportTableData('json')">
                                        <svg class="svg-icon svg-icon-sm"><use href="#icon-download"/></svg> JSON
                                    </button>
                                    <button class="btn btn-primary" style="padding:4px 10px; font-size:0.7rem;" onclick="executeCustomSql()">
                                        <svg class="svg-icon svg-icon-sm"><use href="#icon-play"/></svg> Executar SQL
                                    </button>
                                </div>
                            </div>
                            <div class="db-grid-scroll" id="db-grid-scroll">
                                <table class="db-table" id="db-data-table">
                                    <thead><tr id="db-table-head"><th>Nenhuma tabela selecionada</th></tr></thead>
                                    <tbody id="db-table-body"></tbody>
                                </table>
                            </div>
                            <div class="db-sql-console">
                                <div style="display:flex; justify-content:space-between; font-size:0.68rem; color:var(--text-muted);">
                                    <span>Console SQL (SELECT / UPDATE / INSERT)</span>
                                    <span id="db-query-status">Pronto</span>
                                </div>
                                <textarea class="db-sql-textarea" id="db-sql-input" placeholder="Digite sua consulta SQL aqui (ex: SELECT * FROM players LIMIT 50;)..."></textarea>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 5: Logs Fullscreen -->
            <div id="tab-logs" class="tab-content">
                <div class="stage-header">
                    <div class="stage-title">Logs & Console Geral</div>
                    <div class="stage-subtitle">Visualização de alta densidade de mensagens de processo</div>
                </div>
                <div class="dash-terminal-container" style="height:100%;">
                    <div class="term-header">
                        <div class="term-title">
                            <span class="status-dot online"></span>
                            <span>Registro Consolidado</span>
                        </div>
                        <div class="term-actions">
                            <button class="btn btn-secondary" style="padding:3px 8px; font-size:0.7rem;" onclick="copyConsoleLogs()">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-copy"/></svg> Copiar
                            </button>
                        </div>
                    </div>
                    <div class="term-body" id="fs-log-body"></div>
                </div>
            </div>

            <!-- Tab 6: Arquitetura & Portas -->
            <div id="tab-network" class="tab-content">
                <div class="stage-header">
                    <div class="stage-title">Arquitetura de Rede & Mapeamento de Portas</div>
                    <div class="stage-subtitle">Topologia dos 3 GameServers independentes compartilhando LoginServer e ChatServer</div>
                </div>
                <div style="background:var(--bg-card); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:16px;">
                    <table class="db-table">
                        <thead>
                            <tr>
                                <th>Serviço</th>
                                <th>GSID</th>
                                <th>Porta Cliente</th>
                                <th>Porta Interna</th>
                                <th>Banco MySQL</th>
                                <th>Alocação JVM</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="color:#00CED1; font-weight:700;">[CS] Chat Server</td>
                                <td>--</td>
                                <td>10241</td>
                                <td>9021</td>
                                <td>aionclassic_cs</td>
                                <td>512M</td>
                            </tr>
                            <tr>
                                <td style="color:#FFD700; font-weight:700;">[LS] Login Server</td>
                                <td>--</td>
                                <td>2106</td>
                                <td>9014</td>
                                <td>aionclassic_ls</td>
                                <td>512M</td>
                            </tr>
                            <tr>
                                <td style="color:#38BDF8; font-weight:700;">[GF] GameForge</td>
                                <td>1</td>
                                <td>7777</td>
                                <td>9014 (LS)</td>
                                <td>aionclassic_gs</td>
                                <td>Xms 1G / Xmx 4G</td>
                            </tr>
                            <tr>
                                <td style="color:#10B981; font-weight:700;">[RM] Remake</td>
                                <td>2</td>
                                <td>7778</td>
                                <td>9014 (LS)</td>
                                <td>aionclassic_gs2</td>
                                <td>Xms 1G / Xmx 4G</td>
                            </tr>
                            <tr>
                                <td style="color:#F97316; font-weight:700;">[BR] BattleRoyale</td>
                                <td>3</td>
                                <td>7779</td>
                                <td>9014 (LS)</td>
                                <td>aionclassic_gs3</td>
                                <td>Xms 1G / Xmx 4G</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <!-- Compact Mini Widget -->
    <div id="compact-widget-container">
        <div class="cw-header">
            <div class="cw-title">
                <span class="brand-badge" style="padding:2px 6px; font-size:0.7rem;">A5</span>
                <span>AION CLASSIC 5.0</span>
            </div>
            <button class="term-action-btn" onclick="toggleCompactMode()" title="Restaurar Painel Completo">
                <svg class="svg-icon svg-icon-sm"><use href="#icon-expand"/></svg>
            </button>
        </div>
        <div class="cw-grid" id="cw-grid-rows">
            <!-- Populated dynamically -->
        </div>
        <div class="cw-footer">
            <span>CPU: <b id="cw-cpu" style="color:#fff;">0.0%</b></span>
            <span>RAM: <b id="cw-ram" style="color:#fff;">0 MB</b></span>
            <span>Online: <b id="cw-online" style="color:#10b981;">0/4</b></span>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast-msg">
        <svg class="svg-icon svg-icon-sm" style="color:var(--accent-cyan);"><use href="#icon-check"/></svg>
        <span id="toast-text">Operação realizada com sucesso!</span>
    </div>

    <script>
        // Memory formatting helper (Item 10)
        function formatMemory(mb) {
            if (!mb || mb <= 0) return '0 MB';
            if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB';
            return Math.round(mb) + ' MB';
        }

        function formatUptime(secs) {
            const h = String(Math.floor(secs / 3600)).padStart(2, '0');
            const m = String(Math.floor((secs % 3600) / 60)).padStart(2, '0');
            const s = String(secs % 60).padStart(2, '0');
            return `${h}:${m}:${s}`;
        }

        function showToast(msg) {
            const t = document.getElementById('toast-msg');
            document.getElementById('toast-text').textContent = msg;
            t.style.display = 'flex';
            setTimeout(() => { t.style.display = 'none'; }, 3200);
        }

        // Tab Navigation
        function switchTab(tabId, el) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            const target = document.getElementById('tab-' + tabId);
            if (target) target.classList.add('active');
            if (el) el.classList.add('active');

            if (tabId === 'gs-servers') {
                setTimeout(drawFibonacciChart, 50);
            } else if (tabId === 'properties') {
                loadPropertiesFiles();
            } else if (tabId === 'database') {
                loadDbSchema();
            }
        }

        // State & Polling
        let currentState = null;
        let isAutoScroll = true;
        let activeLogFilter = 'all';

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                if (!res.ok) return;
                const data = await res.json();
                currentState = data;
                renderMetrics(data);
            } catch (e) {
                // Ignore transient errors
            }
        }

        function renderMetrics(data) {
            // Sidebar KPIs
            document.getElementById('side-cpu').textContent = data.total_cpu.toFixed(1) + '%';
            document.getElementById('side-ram').textContent = formatMemory(data.total_memory_mb);
            document.getElementById('side-players').textContent = data.online_players_count;
            document.getElementById('side-uptime').textContent = formatUptime(data.uptime_secs);

            // Dashboard KPIs
            document.getElementById('kpi-cpu-text').textContent = data.total_cpu.toFixed(1) + '%';
            document.getElementById('kpi-ram-text').textContent = formatMemory(data.total_memory_mb);
            document.getElementById('kpi-host-ram').textContent = `RAM Host: ${formatMemory(data.os_used_memory_mb)} / ${formatMemory(data.os_total_memory_mb)}`;
            document.getElementById('kpi-players-count').textContent = data.online_players_count;

            const onlineCount = data.servers.filter(s => s.status === 'Online').length;
            const totalCount = data.servers.length;
            document.getElementById('kpi-cluster-count').textContent = `${onlineCount} de ${totalCount} serviços online`;
            document.getElementById('kpi-cluster-status').textContent = onlineCount === totalCount ? 'Todos Operacionais' : (onlineCount > 0 ? 'Parcialmente Online' : 'Serviços Parados');

            // Header Button States (Item 10)
            const btnOrch = document.getElementById('btn-orchestrate');
            const btnStopAll = document.getElementById('btn-stop-all');
            const btnRestartAll = document.getElementById('btn-restart-all');

            if (btnOrch) btnOrch.disabled = (onlineCount === totalCount && totalCount > 0);
            if (btnStopAll) btnStopAll.disabled = (onlineCount === 0);
            if (btnRestartAll) btnRestartAll.disabled = (onlineCount === 0);

            // Render Server Cards
            const container = document.getElementById('servers-container');
            const cwGrid = document.getElementById('cw-grid-rows');
            let cardsHtml = '';
            let cwRowsHtml = '';

            data.servers.forEach(s => {
                const isOnline = s.status === 'Online';
                const isStarting = s.status === 'Starting';
                const isOffline = s.status === 'Offline';
                const isCrashed = s.status === 'Crashed';

                let statusClass = 'offline';
                let statusLabel = 'Offline';
                if (isOnline) { statusClass = 'online'; statusLabel = 'Online'; }
                else if (isStarting) { statusClass = 'starting'; statusLabel = 'Iniciando'; }
                else if (isCrashed) { statusClass = 'crashed'; statusLabel = 'Falhou'; }

                let borderClass = 'border-remake';
                if (s.name === 'chat') borderClass = 'border-chat';
                else if (s.name === 'login') borderClass = 'border-login';
                else if (s.name === 'gameforge') borderClass = 'border-gameforge';
                else if (s.name === 'battleroyale') borderClass = 'border-battleroyale';

                // State-aware button checks (Item 10)
                const startDisabled = (!isOffline && !isCrashed) ? 'disabled' : '';
                const stopDisabled = !isOnline ? 'disabled' : '';
                const restartDisabled = !isOnline ? 'disabled' : '';

                cardsHtml += `
                    <div class="server-card ${borderClass}">
                        <div class="sc-head">
                            <div class="sc-title-group">
                                <div class="sc-title">
                                    <span class="sc-tag">${s.tag}</span>
                                    <span>${s.label}</span>
                                    ${s.gsid ? `<span class="sc-tag-gsid">GSID ${s.gsid}</span>` : ''}
                                </div>
                                <div class="sc-meta">DB: ${s.db_name} | Porta: ${s.port || '--'}</div>
                            </div>
                            <div class="status-pill ${statusClass}">
                                <span class="status-dot"></span>
                                <span>${statusLabel}</span>
                            </div>
                        </div>

                        <div class="sc-metrics">
                            <div class="sc-metric-item">
                                <span class="sc-metric-label">Uso de CPU</span>
                                <span class="sc-metric-val" style="color:${isOnline ? (s.cpu_percent > 60 ? '#f87171' : '#38bdf8') : '#64748b'};">${isOnline ? s.cpu_percent.toFixed(1) + '%' : '0.0%'}</span>
                            </div>
                            <div class="sc-metric-item">
                                <span class="sc-metric-label">Memória</span>
                                <span class="sc-metric-val">${formatMemory(s.memory_mb)}</span>
                            </div>
                            <div class="sc-metric-item">
                                <span class="sc-metric-label">PID</span>
                                <span class="sc-metric-val">${s.pid || '--'}</span>
                            </div>
                            <div class="sc-metric-item">
                                <span class="sc-metric-label">Tempo Ativo</span>
                                <span class="sc-metric-val">${formatUptime(s.uptime_secs)}</span>
                            </div>
                        </div>

                        <div class="sc-actions">
                            <button class="sc-btn sc-btn-start" ${startDisabled} onclick="controlServer('${s.name}', 'start')">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-play"/></svg> Iniciar
                            </button>
                            <button class="sc-btn sc-btn-stop" ${stopDisabled} onclick="controlServer('${s.name}', 'stop')">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-stop"/></svg> Parar
                            </button>
                            <button class="sc-btn sc-btn-restart" ${restartDisabled} onclick="controlServer('${s.name}', 'restart')">
                                <svg class="svg-icon svg-icon-sm"><use href="#icon-refresh"/></svg> Reiniciar
                            </button>
                        </div>
                    </div>
                `;

                // Compact Mode Row
                cwRowsHtml += `
                    <div class="cw-row">
                        <div class="cw-server-info">
                            <span class="status-dot ${statusClass}"></span>
                            <span>[${s.tag}] ${s.label}</span>
                        </div>
                        <div class="cw-metrics">
                            <span>${isOnline ? s.cpu_percent.toFixed(1) + '%' : '0.0%'}</span>
                            <span>${formatMemory(s.memory_mb)}</span>
                        </div>
                    </div>
                `;
            });

            if (container) container.innerHTML = cardsHtml;
            if (cwGrid) cwGrid.innerHTML = cwRowsHtml;

            // Compact Mode footer
            document.getElementById('cw-cpu').textContent = data.total_cpu.toFixed(1) + '%';
            document.getElementById('cw-ram').textContent = formatMemory(data.total_memory_mb);
            document.getElementById('cw-online').textContent = `${onlineCount}/${totalCount}`;
        }

        // Server Controls
        async function controlServer(name, action) {
            try {
                showToast(`Executando ${action} em ${name}...`);
                const res = await fetch(`/api/control/${name}/${action}`, { method: 'POST' });
                const json = await res.json();
                if (json.status === 'ok') {
                    showToast(`Comando executado com sucesso!`);
                } else {
                    alert(`Falha: ${json.message || 'Erro desconhecido'}`);
                }
                fetchMetrics();
            } catch (e) {
                alert(`Erro de conexão: ${e.message}`);
            }
        }

        function startOrchestrated() { controlServer('all', 'start'); }
        function stopAllServers() { controlServer('all', 'stop'); }
        function restartAllServers() { controlServer('all', 'restart'); }

        // Logs Console
        let logsCache = [];
        async function fetchLogs() {
            try {
                const srvParam = activeLogFilter === 'all' ? '' : `?server=${activeLogFilter}`;
                const res = await fetch(`/api/logs${srvParam}`);
                if (!res.ok) return;
                const entries = await res.json();
                logsCache = entries;
                renderLogs(entries);
            } catch (e) {}
        }

        function renderLogs(entries) {
            const body = document.getElementById('dash-log-body');
            const fsBody = document.getElementById('fs-log-body');
            if (!body) return;

            let html = '';
            entries.forEach(e => {
                let tagClass = 'log-tag-launcher';
                if (e.server === 'chat') tagClass = 'log-tag-chat';
                else if (e.server === 'login') tagClass = 'log-tag-login';
                else if (e.server === 'remake') tagClass = 'log-tag-remake';
                else if (e.server === 'gameforge') tagClass = 'log-tag-gameforge';
                else if (e.server === 'battleroyale') tagClass = 'log-tag-battleroyale';

                let textClass = '';
                const lower = e.message.toLowerCase();
                if (lower.includes('erro') || lower.includes('error') || lower.includes('fatal') || lower.includes('exception')) {
                    textClass = 'error';
                } else if (lower.includes('aviso') || lower.includes('warn')) {
                    textClass = 'warn';
                } else if (lower.includes('ok') || lower.includes('sucesso') || lower.includes('online')) {
                    textClass = 'success';
                } else if (lower.includes('iniciando') || lower.includes('ready')) {
                    textClass = 'info';
                }

                html += `
                    <div class="log-entry">
                        <span class="log-time">${e.timestamp}</span>
                        <span class="log-tag ${tagClass}">[${e.server.toUpperCase()}]</span>
                        <span class="log-text ${textClass}">${escapeHtml(e.message)}</span>
                    </div>
                `;
            });

            body.innerHTML = html;
            if (fsBody) fsBody.innerHTML = html;

            if (isAutoScroll) {
                body.scrollTop = body.scrollHeight;
                if (fsBody) fsBody.scrollTop = fsBody.scrollHeight;
            }
        }

        function escapeHtml(str) {
            return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }

        function setLogFilter(filter, el) {
            activeLogFilter = filter;
            document.querySelectorAll('#term-filters-pills .term-pill').forEach(p => p.classList.remove('active'));
            if (el) el.classList.add('active');
            fetchLogs();
        }

        function toggleAutoScroll() {
            isAutoScroll = !isAutoScroll;
            const btn = document.getElementById('btn-autoscroll');
            if (btn) btn.classList.toggle('active', isAutoScroll);
        }

        function clearLogsConsole() {
            document.getElementById('dash-log-body').innerHTML = '';
            const fs = document.getElementById('fs-log-body');
            if (fs) fs.innerHTML = '';
        }

        function copyConsoleLogs() {
            const text = logsCache.map(e => `[${e.timestamp}] [${e.server}] ${e.message}`).join('\n');
            navigator.clipboard.writeText(text).then(() => showToast('Logs copiados para a área de transferência!'));
        }

        // Fibonacci Canvas Chart
        function drawFibonacciChart() {
            const canvas = document.getElementById('fib-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            const w = rect.width;
            const h = rect.height;
            ctx.clearRect(0, 0, w, h);

            // Fibonacci Golden Retracement levels
            const levels = [
                { p: 1.0, color: 'rgba(239, 68, 68, 0.4)', label: '100.0%' },
                { p: 0.786, color: 'rgba(244, 63, 94, 0.35)', label: '78.6%' },
                { p: 0.618, color: 'rgba(249, 115, 22, 0.35)', label: '61.8% (Golden)' },
                { p: 0.50, color: 'rgba(234, 179, 8, 0.3)', label: '50.0%' },
                { p: 0.382, color: 'rgba(16, 185, 129, 0.35)', label: '38.2%' },
                { p: 0.236, color: 'rgba(56, 189, 248, 0.35)', label: '23.6%' },
                { p: 0.0, color: 'rgba(148, 163, 184, 0.2)', label: '0.0%' }
            ];

            levels.forEach(lvl => {
                const y = h - (lvl.p * (h - 20)) - 10;
                ctx.strokeStyle = lvl.color;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(30, y);
                ctx.lineTo(w - 10, y);
                ctx.stroke();

                ctx.fillStyle = lvl.color;
                ctx.font = '9px monospace';
                ctx.fillText(lvl.label, 2, y + 3);
            });
            ctx.setLineDash([]);

            // Plot real history curves if available
            if (currentState && currentState.history && currentState.history.length > 1) {
                const hist = currentState.history;
                const stepX = (w - 40) / Math.max(hist.length - 1, 1);

                // Total Memory curve
                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 2;
                ctx.beginPath();
                hist.forEach((pt, idx) => {
                    const x = 30 + idx * stepX;
                    const maxMem = 8192; // 8GB scale
                    const y = h - ((pt.total_mem_mb / maxMem) * (h - 20)) - 10;
                    if (idx === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                });
                ctx.stroke();

                // Total CPU curve
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                hist.forEach((pt, idx) => {
                    const x = 30 + idx * stepX;
                    const y = h - ((pt.total_cpu / 100.0) * (h - 20)) - 10;
                    if (idx === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                });
                ctx.stroke();
            }
        }

        // Properties Manager Segregation (Item 6)
        let allPropertiesFiles = [];
        let activePropServer = 'remake';
        let currentPropFile = null;

        async function loadPropertiesFiles() {
            try {
                const res = await fetch('/api/properties/list');
                const data = await res.json();
                allPropertiesFiles = data.files || [];
                renderPropFilesList();
            } catch (e) {}
        }

        function selectPropServer(srvId, el) {
            activePropServer = srvId;
            document.querySelectorAll('#prop-srv-tabs .prop-srv-btn').forEach(b => b.classList.remove('active'));
            if (el) el.classList.add('active');
            renderPropFilesList();
        }

        function renderPropFilesList() {
            const listEl = document.getElementById('prop-files-list');
            const search = (document.getElementById('prop-file-search').value || '').toLowerCase();
            if (!listEl) return;

            const filtered = allPropertiesFiles.filter(f => f.server_id === activePropServer && f.name.toLowerCase().includes(search));

            let html = '';
            filtered.forEach(f => {
                const isActive = currentPropFile && currentPropFile.full_path === f.full_path ? 'active' : '';
                html += `
                    <div class="prop-file-item ${isActive}" onclick="openPropertyFile('${encodeURIComponent(f.full_path)}')">
                        <div class="prop-file-name">${f.name}</div>
                        <div class="prop-file-cat">${f.category} (${(f.size_bytes / 1024).toFixed(1)} KB)</div>
                    </div>
                `;
            });

            listEl.innerHTML = html || '<div style="color:var(--text-muted); font-size:0.75rem; padding:10px;">Nenhum arquivo encontrado</div>';
        }

        function filterPropFiles() { renderPropFilesList(); }

        async function openPropertyFile(encodedPath) {
            const fullPath = decodeURIComponent(encodedPath);
            try {
                const res = await fetch(`/api/properties/file?path=${encodeURIComponent(fullPath)}&server=${activePropServer}`);
                const data = await res.json();
                currentPropFile = data;
                document.getElementById('prop-current-filename').textContent = data.rel_path.split('\\\\').pop().split('/').pop();
                renderPropertiesEditor(data.items);
                renderPropFilesList();
            } catch (e) {
                alert('Erro ao carregar arquivo: ' + e.message);
            }
        }

        function renderPropertiesEditor(items) {
            const pane = document.getElementById('prop-editor-content');
            if (!pane) return;

            // Group by category
            const groups = {};
            items.forEach((item, idx) => {
                const cat = item.category || 'Geral';
                if (!groups[cat]) groups[cat] = [];
                groups[cat].push({ item, idx });
            });

            let html = '';
            for (const [catName, catItems] of Object.entries(groups)) {
                html += `
                    <div class="prop-category-block">
                        <div class="prop-category-title">
                            <svg class="svg-icon svg-icon-sm"><use href="#icon-config"/></svg>
                            <span>${catName}</span>
                        </div>
                `;

                catItems.forEach(({ item, idx }) => {
                    html += `
                        <div class="prop-row">
                            <div class="prop-key" title="${item.comment || ''}">${escapeHtml(item.key)}</div>
                            <input type="text" class="prop-val-input" id="prop-input-${idx}" data-key="${escapeHtml(item.key)}" value="${escapeHtml(item.value)}">
                        </div>
                    `;
                });

                html += `</div>`;
            }

            pane.innerHTML = html;
        }

        async function saveCurrentProperties() {
            if (!currentPropFile) return;

            const updates = {};
            currentPropFile.items.forEach((item, idx) => {
                const input = document.getElementById(`prop-input-${idx}`);
                if (input) updates[item.key] = input.value;
            });

            try {
                const res = await fetch('/api/properties/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        path: currentPropFile.full_path,
                        server: activePropServer,
                        updates
                    })
                });
                const json = await res.json();
                if (json.status === 'ok') {
                    showToast(`Salvo com sucesso! Backup criado: ${json.backup_path}`);
                } else {
                    alert('Erro ao salvar: ' + (json.message || 'Falha'));
                }
            } catch (e) {
                alert('Erro de rede: ' + e.message);
            }
        }

        // Database Studio (Item 7)
        let activeStudioDb = 'cs';
        let currentDbTables = [];
        let activeTableName = null;
        let currentTableData = null;

        function selectDbStudio(dbId, el) {
            activeStudioDb = dbId;
            document.querySelectorAll('#db-srv-tabs .prop-srv-btn').forEach(b => b.classList.remove('active'));
            if (el) el.classList.add('active');
            loadDbSchema();
        }

        async function loadDbSchema() {
            try {
                const res = await fetch('/api/db/schema');
                const data = await res.json();
                if (data.status === 'ok') {
                    const dbObj = data.databases.find(d => d.id === activeStudioDb);
                    currentDbTables = dbObj ? dbObj.tables : [];
                    renderDbTablesList();
                }
            } catch (e) {}
        }

        function renderDbTablesList() {
            const listEl = document.getElementById('db-tables-list');
            const search = (document.getElementById('db-table-search').value || '').toLowerCase();
            if (!listEl) return;

            const filtered = currentDbTables.filter(t => t.name.toLowerCase().includes(search));
            let html = '';
            filtered.forEach(t => {
                const isActive = activeTableName === t.name ? 'active' : '';
                html += `
                    <div class="db-table-item ${isActive}" onclick="loadTableRows('${t.name}')">
                        <span>${t.name}</span>
                        <span class="db-table-cnt">${t.estimated_rows} linhas</span>
                    </div>
                `;
            });
            listEl.innerHTML = html || '<div style="color:var(--text-muted); font-size:0.75rem; padding:10px;">Nenhuma tabela</div>';
        }

        function filterDbTables() { renderDbTablesList(); }

        async function loadTableRows(tblName) {
            activeTableName = tblName;
            document.getElementById('db-active-table-name').textContent = `Tabela: ${tblName} (${activeStudioDb})`;
            renderDbTablesList();

            try {
                const res = await fetch(`/api/db/table/${tblName}/rows?db=${activeStudioDb}&page=1&limit=50`);
                const json = await res.json();
                if (json.status === 'ok') {
                    currentTableData = json.data;
                    renderDataGrid(json.data);
                }
            } catch (e) {
                alert('Erro ao carregar dados: ' + e.message);
            }
        }

        function renderDataGrid(data) {
            const thead = document.getElementById('db-table-head');
            const tbody = document.getElementById('db-table-body');
            if (!thead || !tbody) return;

            let headHtml = '';
            data.columns.forEach(col => {
                headHtml += `<th>${col.name}</th>`;
            });
            thead.innerHTML = headHtml;

            let bodyHtml = '';
            data.rows.forEach(row => {
                bodyHtml += '<tr>';
                data.columns.forEach(col => {
                    const val = row[col.name];
                    bodyHtml += `<td title="${escapeHtml(String(val))}">${escapeHtml(String(val !== null ? val : 'NULL'))}</td>`;
                });
                bodyHtml += '</tr>';
            });
            tbody.innerHTML = bodyHtml;
        }

        async function executeCustomSql() {
            const sql = document.getElementById('db-sql-input').value.trim();
            if (!sql) return;

            const statusEl = document.getElementById('db-query-status');
            statusEl.textContent = 'Executando...';

            try {
                const res = await fetch('/api/db/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ db: activeStudioDb, sql })
                });
                const json = await res.json();
                if (json.status === 'ok' && json.result) {
                    const r = json.result;
                    statusEl.textContent = `${r.execution_time_ms.toFixed(1)}ms | ${r.affected_rows} afetadas`;
                    if (r.is_select && r.columns && r.rows) {
                        const fakeData = {
                            columns: r.columns.map(name => ({ name })),
                            rows: r.rows.map(rowVals => {
                                const obj = {};
                                r.columns.forEach((c, idx) => obj[c] = rowVals[idx]);
                                return obj;
                            })
                        };
                        renderDataGrid(fakeData);
                    } else {
                        showToast(`Sucesso! ${r.affected_rows} linhas afetadas.`);
                    }
                } else {
                    statusEl.textContent = 'Erro!';
                    alert('Erro na consulta: ' + (json.message || 'Falha'));
                }
            } catch (e) {
                statusEl.textContent = 'Falha de rede';
            }
        }

        function exportTableData(type) {
            if (!currentTableData || !currentTableData.rows.length) {
                alert('Nenhum dado para exportar');
                return;
            }
            if (type === 'json') {
                const blob = new Blob([JSON.stringify(currentTableData.rows, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${activeTableName}_export.json`;
                a.click();
            } else if (type === 'csv') {
                const cols = currentTableData.columns.map(c => c.name);
                let csv = cols.join(',') + '\n';
                currentTableData.rows.forEach(r => {
                    csv += cols.map(c => JSON.stringify(r[c] !== null ? r[c] : '')).join(',') + '\n';
                });
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${activeTableName}_export.csv`;
                a.click();
            }
        }

        // Compact Mode Switcher (Item 13)
        async function toggleCompactMode() {
            try {
                await fetch('/api/ui/compact', { method: 'POST' });
            } catch (e) {}
        }

        function setCompactMode(isCompact) {
            document.body.classList.toggle('compact-mode', isCompact);
        }

        // Init
        window.addEventListener('DOMContentLoaded', () => {
            fetchMetrics();
            fetchLogs();
            setInterval(fetchMetrics, 1000);
            setInterval(fetchLogs, 1500);
            window.addEventListener('resize', drawFibonacciChart);
        });
    </script>
</body>
</html>
"##;
