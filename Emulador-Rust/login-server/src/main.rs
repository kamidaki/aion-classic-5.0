mod config;
mod crypto;
mod db;
mod net;
mod security;

use config::load_config;
use db::AuthDb;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let _instance_guard = match commons::single_instance::SingleInstanceGuard::acquire(
        "Login Server",
        "Local\\EmuRust_LoginServer_Mutex",
    ) {
        Some(g) => g,
        None => {
            std::process::exit(1);
        }
    };

    println!("INFO: [LoginServer] Starting Unified Aion Classic Login Server...");


    let cfg_path = "config/launcher.json";
    let cfg = load_config(cfg_path);

    if !cfg.enabled {
        println!("WARN: [LoginServer] Login server is disabled in config.");
        return Ok(());
    }

    println!("INFO: [LoginServer] Opening database at {}", cfg.database.path);
    let db = match AuthDb::open(&cfg.database.path) {
        Ok(d) => Arc::new(d),
        Err(e) => {
            eprintln!("ERROR: [LoginServer] Failed to open database {}: {}", cfg.database.path, e);
            return Err(e.into());
        }
    };

    let security = Arc::new(security::SecurityManager::new(
        cfg.security.enable_rate_limit,
        cfg.security.max_attempts_per_minute,
        cfg.security.temp_ban_minutes,
    ));

    // 1. Start Windows Named Pipe provider
    let pipe_name = r"\\.\pipe\GameforgeClientJSONRPC";
    net::pipe::spawn_named_pipe_provider(pipe_name, Arc::clone(&db), cfg.default_dev_username.clone());

    // 2. Spawn STS Server (Port 6600)
    let sts_bind = format!("{}:{}", cfg.bind_address, cfg.sts_port);
    let db_sts = Arc::clone(&db);
    let dev_user_sts = cfg.default_dev_username.clone();
    let sts_handle = tokio::spawn(async move {
        if let Err(e) = net::sts::run_sts_server(&sts_bind, db_sts, dev_user_sts).await {
            eprintln!("ERROR: [LoginServer-STS] Fatal error: {}", e);
        }
    });

    // 3. Spawn NCSoft Server (Port 2106)
    let ncsoft_bind = format!("{}:{}", cfg.bind_address, cfg.client_port);
    let db_ncsoft = Arc::clone(&db);
    let announce_ip_nc = cfg.announce_game_server_ip.clone();
    let announce_port_nc = cfg.announce_game_server_port;
    let srv_id_nc = cfg.default_server_id;
    let auto_create_nc = cfg.auto_create_accounts;
    let dev_user_nc = cfg.default_dev_username.clone();
    let sec_nc = Arc::clone(&security);
    let ncsoft_handle = tokio::spawn(async move {
        if let Err(e) = net::ncsoft::run_ncsoft_server(
            &ncsoft_bind,
            announce_ip_nc,
            announce_port_nc,
            srv_id_nc,
            db_ncsoft,
            auto_create_nc,
            dev_user_nc,
            sec_nc,
        )
        .await
        {
            eprintln!("ERROR: [LoginServer-NCSoft] Fatal error: {}", e);
        }
    });

    // 4. Run HQ Server (Port 13001)
    let hq_bind = format!("{}:{}", cfg.bind_address, cfg.hq_port);
    let db_hq = Arc::clone(&db);
    let announce_ip_hq = cfg.announce_game_server_ip.clone();
    let announce_port_hq = cfg.announce_game_server_port;
    let srv_id_hq = cfg.default_server_id;
    let auto_create_hq = cfg.auto_create_accounts;
    let dev_user_hq = cfg.default_dev_username.clone();
    let sec_hq = Arc::clone(&security);
    let hq_handle = tokio::spawn(async move {
        if let Err(e) = net::hq::run_hq_server(
            &hq_bind,
            announce_ip_hq,
            announce_port_hq,
            srv_id_hq,
            db_hq,
            auto_create_hq,
            dev_user_hq,
            sec_hq,
        )
        .await
        {
            eprintln!("ERROR: [LoginServer-HQ] Fatal error: {}", e);
        }
    });

    println!("INFO: [LoginServer] All sub-services initialized successfully with active SecurityManager.");

    // Keep all services running indefinitely
    std::future::pending::<()>().await;

    Ok(())
}
