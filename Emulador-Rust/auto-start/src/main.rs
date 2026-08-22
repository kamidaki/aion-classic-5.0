mod config;
mod logs;
mod supervisor;
mod ui;

use config::load_config;
use logs::LogCenter;
use supervisor::Supervisor;
use std::convert::Infallible;
use std::sync::Arc;
use warp::Filter;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            let _ = std::env::set_current_dir(parent);
        }
    }

    println!("=========================================================================");
    println!("  AION CLASSIC EU — AUTO-START EMURUST (MANAGER & OBSERVABILITY HUB)");
    println!("=========================================================================");

    let cfg_path = "config/launcher.json";
    let cfg = load_config(cfg_path);

    let log_center = LogCenter::new(
        cfg.logging.retentionDays,
        &cfg.logging.loginServerPath,
        &cfg.logging.gameServerPath,
        &cfg.logging.chatServerPath,
    );

    let supervisor = Supervisor::new(cfg.clone(), log_center.clone());
    supervisor.spawn_crash_monitor();

    // Auto-start servers if enabled in configuration
    if cfg.launcher.autoStartLoginServer {
        let _ = supervisor.start_server("login").await;
    }
    if cfg.launcher.autoStartGameServer {
        let _ = supervisor.start_server("game").await;
    }
    if cfg.launcher.autoStartChatServer {
        let _ = supervisor.start_server("chat").await;
    }

    let sup_filter = {
        let s = supervisor.clone();
        warp::any().map(move || s.clone())
    };

    let log_filter = {
        let lc = log_center.clone();
        warp::any().map(move || lc.clone())
    };

    // Route: GET / -> Dashboard HTML
    let index_route = warp::path::end().map(|| warp::reply::html(ui::HTML_DASHBOARD));

    // Route: GET /api/metrics -> JSON metrics
    let metrics_route = warp::path!("api" / "metrics")
        .and(warp::get())
        .and(sup_filter.clone())
        .map(|sup: Supervisor| {
            let metrics = sup.get_metrics();
            warp::reply::json(&metrics)
        });

    // Route: GET /api/logs?server=all -> JSON recent logs
    let logs_route = warp::path!("api" / "logs")
        .and(warp::get())
        .and(warp::query::<std::collections::HashMap<String, String>>())
        .and(log_filter)
        .map(|params: std::collections::HashMap<String, String>, lc: LogCenter| {
            let srv = params.get("server").map(|s| s.as_str());
            let entries = lc.get_recent_entries(200, srv, None);
            warp::reply::json(&entries)
        });

    // Route: POST /api/control/:server/:action -> Control server (start, stop, restart)
    let control_route = warp::path!("api" / "control" / String / String)
        .and(warp::post())
        .and(sup_filter)
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

    let routes = index_route
        .or(metrics_route)
        .or(logs_route)
        .or(control_route);

    let port = cfg.launcher.gui.http_port;
    let url = format!("http://127.0.0.1:{}", port);
    println!("INFO: [AutoStart] Dashboard web interface listening at {}", url);

    // Open dashboard in browser
    let _ = open::that(&url);

    warp::serve(routes).run(([0, 0, 0, 0], port)).await;

    Ok(())
}
