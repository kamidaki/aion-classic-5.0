#![windows_subsystem = "windows"]

mod config;
mod logs;
mod supervisor;
mod tray;
mod ui;
mod webview;

use config::load_config;
use logs::LogCenter;
use supervisor::Supervisor;
use std::convert::Infallible;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tray::{TrayAction, TrayManager};
use warp::Filter;
use webview::{UserEvent, WebViewApp};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let _ = std::fs::create_dir_all("logs");
    std::panic::set_hook(Box::new(|info| {
        let msg = format!("[PANIC] {:?}\n", info);
        let _ = std::fs::write("logs/auto_start_panic.log", msg);
    }));

    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            let _ = std::env::set_current_dir(parent);
        }
    }


    // 1. Single Instance Protection via Named Mutex
    let _instance_guard = match commons::single_instance::SingleInstanceGuard::acquire(
        "Auto-Start EmuRust",
        "Local\\EmuRust_AutoStart_Mutex",
    ) {
        Some(g) => g,
        None => {
            std::process::exit(1);
        }
    };


    let cfg_path = "config/launcher.json";
    let cfg = load_config(cfg_path);

    let log_center = LogCenter::new(
        cfg.logging.retentionDays,
        &cfg.logging.loginServerPath,
        &cfg.logging.gameServerPath,
        &cfg.logging.chatServerPath,
    );

    let supervisor = Supervisor::new(cfg.clone(), log_center.clone());

    // 2. Initialize Tokio Runtime for background services
    let rt = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?;
    let _rt_guard = rt.enter();

    // 3. Initialize WebView App on main thread

    let webview_app = WebViewApp::new();
    let proxy = webview_app.get_proxy();

    let is_shutting_down = Arc::new(AtomicBool::new(false));

    // 4. Initialize Windows System Tray
    let proxy_for_tray = proxy.clone();
    let is_shutting_down_tray = is_shutting_down.clone();
    let sup_for_tray_shutdown = supervisor.clone();

    let tray_manager_arc = Arc::new(parking_lot::Mutex::new(
        TrayManager::init(Arc::new(move |action| match action {
            TrayAction::OpenDashboard => {
                let _ = proxy_for_tray.send_event(UserEvent::ShowDashboard);
            }
            TrayAction::RequestShutdown => {
                if !is_shutting_down_tray.swap(true, Ordering::SeqCst) {
                    let s = sup_for_tray_shutdown.clone();
                    let p = proxy_for_tray.clone();
                    tokio::spawn(async move {
                        s.graceful_shutdown().await;
                        let _ = p.send_event(UserEvent::RequestShutdown);
                    });
                }
            }
        }))
        .expect("Failed to initialize Windows System Tray"),
    ));

    // 5. Spawn background tasks inside Tokio runtime
    let sup_clone = supervisor.clone();
    let cfg_clone = cfg.clone();
    let log_center_clone = log_center.clone();
    let tray_manager_for_tooltip = tray_manager_arc.clone();
    let is_shutting_down_bg = is_shutting_down.clone();
    let proxy_for_web = proxy.clone();

    rt.spawn(async move {
        sup_clone.spawn_crash_monitor();
        sup_clone.spawn_metrics_sampler();

        // Auto-start servers if enabled in config
        if cfg_clone.launcher.autoStartLoginServer {
            let _ = sup_clone.start_server("login").await;
        }
        if cfg_clone.launcher.autoStartGameServer {
            let _ = sup_clone.start_server("game").await;
        }
        if cfg_clone.launcher.autoStartChatServer {
            let _ = sup_clone.start_server("chat").await;
        }

        // Periodic tray tooltip updater (1s interval)
        let sup_for_tip = sup_clone.clone();
        let is_shutting_down_tip = is_shutting_down_bg.clone();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_millis(1000)).await;
                if is_shutting_down_tip.load(Ordering::SeqCst) {
                    break;
                }
                let tip_text = sup_for_tip.get_tray_tooltip_text();
                tray_manager_for_tooltip.lock().update_tooltip(&tip_text);
            }
        });

        // Set up Warp web dashboard routes
        let sup_filter = {
            let s = sup_clone.clone();
            warp::any().map(move || s.clone())
        };

        let log_filter = {
            let lc = log_center_clone.clone();
            warp::any().map(move || lc.clone())
        };

        // Route: GET / -> Dashboard HTML
        let index_route = warp::path::end().map(|| warp::reply::html(ui::HTML_DASHBOARD));

        // Route: GET /api/metrics -> Full state JSON with metrics & Fibonacci history
        let metrics_route = warp::path!("api" / "metrics")
            .and(warp::get())
            .and(sup_filter.clone())
            .map(|sup: Supervisor| {
                let state = sup.get_dashboard_state();
                warp::reply::json(&state)
            });

        // Route: GET /api/players -> Online players & accounts list
        let players_route = warp::path!("api" / "players")
            .and(warp::get())
            .and(sup_filter.clone())
            .map(|sup: Supervisor| {
                let players = sup.get_online_players();
                warp::reply::json(&players)
            });

        // Route: GET /api/logs?server=all -> Centralized JSON recent logs
        let logs_route = warp::path!("api" / "logs")
            .and(warp::get())
            .and(warp::query::<std::collections::HashMap<String, String>>())
            .and(log_filter)
            .map(|params: std::collections::HashMap<String, String>, lc: LogCenter| {
                let srv = params.get("server").map(|s| s.as_str());
                let entries = lc.get_recent_entries(250, srv, None);
                warp::reply::json(&entries)
            });

        // Route: POST /api/control/:server/:action -> Control server (start, stop, restart)
        let control_route = warp::path!("api" / "control" / String / String)
            .and(warp::post())
            .and(sup_filter.clone())
            .and_then(|server: String, action: String, sup: Supervisor| async move {
                let res = match action.as_str() {
                    "start" => sup.start_server(&server).await,
                    "stop" => sup.stop_server(&server).await,
                    "restart" => sup.restart_server(&server).await,
                    _ => Err("Invalid action".to_string()),
                };

                match res {
                    Ok(_) => Ok::<_, Infallible>(warp::reply::json(&serde_json::json!({ "status": "ok" }))),
                    Err(e) => Ok::<_, Infallible>(warp::reply::json(&serde_json::json!({ "status": "error", "message": e }))),
                }
            });

        // Route: POST /api/shutdown -> Graceful shutdown trigger
        let is_shutting_down_api = is_shutting_down_bg.clone();
        let sup_shutdown_api = sup_clone.clone();
        let proxy_api = proxy_for_web.clone();
        let shutdown_route = warp::path!("api" / "shutdown")
            .and(warp::post())
            .and_then(move || {
                let flag = is_shutting_down_api.clone();
                let sup = sup_shutdown_api.clone();
                let prx = proxy_api.clone();
                async move {
                    if !flag.swap(true, Ordering::SeqCst) {
                        tokio::spawn(async move {
                            sup.graceful_shutdown().await;
                            let _ = prx.send_event(UserEvent::RequestShutdown);
                        });
                    }
                    Ok::<_, Infallible>(warp::reply::json(&serde_json::json!({ "status": "shutting_down" })))
                }
            });

        let routes = index_route
            .or(metrics_route)
            .or(players_route)
            .or(logs_route)
            .or(control_route)
            .or(shutdown_route);

        let port = cfg_clone.launcher.gui.http_port;
        warp::serve(routes).run(([0, 0, 0, 0], port)).await;
    });


    // 6. Run Embedded WebView Manager on main thread
    let port = cfg.launcher.gui.http_port;
    let url = format!("http://127.0.0.1:{}", port);

    let tray_for_exit = tray_manager_arc.clone();
    let sup_for_exit = supervisor.clone();

    webview_app.run(url, move || {
        // Shutdown handler when main event loop exits
        let sup = sup_for_exit.clone();
        let tray = tray_for_exit.clone();
        std::thread::spawn(move || {
            let rt = tokio::runtime::Runtime::new().unwrap();
            rt.block_on(async {
                sup.graceful_shutdown().await;
            });
            tray.lock().remove();
            std::process::exit(0);
        });
    });

    Ok(())
}
