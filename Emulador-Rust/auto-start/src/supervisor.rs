use crate::config::RootConfig;
use crate::logs::LogCenter;
use parking_lot::Mutex;
use serde::Serialize;
use std::collections::{HashMap, VecDeque};
use std::process::Stdio;
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use sysinfo::{Pid, ProcessRefreshKind, RefreshKind, System};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, Command};

const CREATE_NO_WINDOW: u32 = 0x08000000;
const MAX_HISTORY_POINTS: usize = 60;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum ServerStatus {
    Online,
    Offline,
    Starting,
    Stopping,
    Crashed,
}

#[derive(Debug, Clone, Serialize)]
pub struct ServerMetrics {
    pub name: String,
    pub status: ServerStatus,
    pub pid: Option<u32>,
    pub uptime_secs: u64,
    pub cpu_percent: f32,
    pub memory_mb: f32,
    pub min_cpu: f32,
    pub max_cpu: f32,
    pub avg_cpu: f32,
    pub trend: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct HistoryPoint {
    pub timestamp: String,
    pub total_cpu: f32,
    pub total_mem_mb: f32,
    pub login_cpu: f32,
    pub game_cpu: f32,
    pub chat_cpu: f32,
    pub players_count: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct OnlinePlayerInfo {
    pub account_name: String,
    pub character_name: String,
    pub login_time: String,
    pub duration_secs: u64,
    pub server: String,
    pub status: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct DashboardStateResponse {
    pub servers: Vec<ServerMetrics>,
    pub total_cpu_percent: f32,
    pub total_memory_mb: f32,
    pub history: Vec<HistoryPoint>,
    pub online_players: Vec<OnlinePlayerInfo>,
    pub online_count: usize,
    pub launcher_uptime_secs: u64,
}

struct ManagedServer {
    name: String,
    executable: String,
    child: Option<Child>,
    pid: Option<u32>,
    status: ServerStatus,
    start_time: Option<Instant>,
    user_stopped: bool,
    cpu_history: VecDeque<f32>,
}

#[derive(Clone)]
pub struct Supervisor {
    servers: Arc<Mutex<HashMap<String, ManagedServer>>>,
    log_center: LogCenter,
    config: RootConfig,
    system: Arc<Mutex<System>>,
    start_time: Instant,
    history: Arc<Mutex<VecDeque<HistoryPoint>>>,
}

impl Supervisor {
    pub fn new(config: RootConfig, log_center: LogCenter) -> Self {
        let mut servers = HashMap::new();

        servers.insert(
            "login".to_string(),
            ManagedServer {
                name: "login".to_string(),
                executable: "login-server.exe".to_string(),
                child: None,
                pid: None,
                status: ServerStatus::Offline,
                start_time: None,
                user_stopped: false,
                cpu_history: VecDeque::with_capacity(MAX_HISTORY_POINTS),
            },
        );

        servers.insert(
            "game".to_string(),
            ManagedServer {
                name: "game".to_string(),
                executable: "game-server.exe".to_string(),
                child: None,
                pid: None,
                status: ServerStatus::Offline,
                start_time: None,
                user_stopped: false,
                cpu_history: VecDeque::with_capacity(MAX_HISTORY_POINTS),
            },
        );

        servers.insert(
            "chat".to_string(),
            ManagedServer {
                name: "chat".to_string(),
                executable: "chat-server.exe".to_string(),
                child: None,
                pid: None,
                status: ServerStatus::Offline,
                start_time: None,
                user_stopped: false,
                cpu_history: VecDeque::with_capacity(MAX_HISTORY_POINTS),
            },
        );

        let system = System::new_with_specifics(
            RefreshKind::new().with_processes(ProcessRefreshKind::new().with_cpu().with_memory()),
        );

        Self {
            servers: Arc::new(Mutex::new(servers)),
            log_center,
            config,
            system: Arc::new(Mutex::new(system)),
            start_time: Instant::now(),
            history: Arc::new(Mutex::new(VecDeque::with_capacity(MAX_HISTORY_POINTS))),
        }
    }

    pub async fn start_server(&self, name: &str) -> Result<(), String> {
        let (exe, server_name) = {
            let mut servers = self.servers.lock();
            let server = servers.get_mut(name).ok_or_else(|| "Server not found".to_string())?;

            if server.status == ServerStatus::Online || server.status == ServerStatus::Starting {
                return Ok(());
            }

            server.status = ServerStatus::Starting;
            server.user_stopped = false;
            (server.executable.clone(), name.to_string())
        };

        let log_center = self.log_center.clone();
        let exe_dir = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|p| p.to_path_buf()))
            .unwrap_or_else(|| std::env::current_dir().unwrap_or_default());
        let exe_path = exe_dir.join(&exe);

        let mut cmd = Command::new(&exe_path);
        cmd.current_dir(&exe_dir);
        cmd.creation_flags(CREATE_NO_WINDOW);
        cmd.stdout(Stdio::piped()).stderr(Stdio::piped());

        match cmd.spawn() {
            Ok(mut child) => {
                let pid = child.id();
                log_center.push(&server_name, &format!("Serviço iniciado com PID {:?}", pid));

                if let Some(stdout) = child.stdout.take() {
                    let lc = log_center.clone();
                    let s_name = server_name.clone();
                    tokio::spawn(async move {
                        let mut reader = BufReader::new(stdout).lines();
                        while let Ok(Some(line)) = reader.next_line().await {
                            lc.push(&s_name, &line);
                        }
                    });
                }

                if let Some(stderr) = child.stderr.take() {
                    let lc = log_center.clone();
                    let s_name = server_name.clone();
                    tokio::spawn(async move {
                        let mut reader = BufReader::new(stderr).lines();
                        while let Ok(Some(line)) = reader.next_line().await {
                            lc.push(&s_name, &format!("[STDERR] {}", line));
                        }
                    });
                }

                {
                    let mut servers = self.servers.lock();
                    if let Some(s) = servers.get_mut(&server_name) {
                        s.pid = pid;
                        s.status = ServerStatus::Online;
                        s.start_time = Some(Instant::now());
                        s.child = Some(child);
                    }
                }

                Ok(())
            }
            Err(e) => {
                {
                    let mut servers = self.servers.lock();
                    if let Some(s) = servers.get_mut(&server_name) {
                        s.status = ServerStatus::Crashed;
                    }
                }
                let err_msg = format!("Falha ao iniciar {}: {}", exe, e);
                log_center.push(&server_name, &err_msg);
                Err(err_msg)
            }
        }
    }

    pub async fn stop_server(&self, name: &str) -> Result<(), String> {
        let child_opt = {
            let mut servers = self.servers.lock();
            let server = servers.get_mut(name).ok_or_else(|| "Server not found".to_string())?;

            if server.status == ServerStatus::Offline {
                return Ok(());
            }

            server.status = ServerStatus::Stopping;
            server.user_stopped = true;
            server.pid = None;
            server.start_time = None;
            server.child.take()
        };

        if let Some(mut child) = child_opt {
            let _ = child.kill().await;
            self.log_center.push(name, "Serviço encerrado com sucesso.");
        }

        {
            let mut servers = self.servers.lock();
            if let Some(s) = servers.get_mut(name) {
                s.status = ServerStatus::Offline;
            }
        }

        Ok(())
    }

    pub async fn restart_server(&self, name: &str) -> Result<(), String> {
        let _ = self.stop_server(name).await;
        tokio::time::sleep(Duration::from_millis(600)).await;
        self.start_server(name).await
    }

    pub async fn graceful_shutdown(&self) {
        self.log_center.push("launcher", "INICIANDO ENCERRAMENTO COMPLETO DO EMULADOR...");

        // 1. Stop Game Server first
        self.log_center.push("launcher", "Encerrando Game-Server...");
        let _ = self.stop_server("game").await;
        tokio::time::sleep(Duration::from_millis(500)).await;

        // 2. Stop Login Server second
        self.log_center.push("launcher", "Encerrando Login-Server...");
        let _ = self.stop_server("login").await;
        tokio::time::sleep(Duration::from_millis(300)).await;

        // 3. Stop Chat Server third
        self.log_center.push("launcher", "Encerrando Chat-Server...");
        let _ = self.stop_server("chat").await;
        tokio::time::sleep(Duration::from_millis(300)).await;

        self.log_center.push("launcher", "Todos os servidores encerrados. Finalizando Auto-Start.");
    }

    pub fn spawn_metrics_sampler(&self) {
        let sup = self.clone();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_millis(1000)).await;

                // 1. Refresh system processes
                let mut sys = sup.system.lock();
                sys.refresh_processes_specifics(
                    ProcessRefreshKind::new().with_cpu().with_memory(),
                );

                let now_ts = chrono::Local::now().format("%H:%M:%S").to_string();
                let mut total_cpu = 0.0f32;
                let mut total_mem = 0.0f32;
                let mut l_cpu = 0.0f32;
                let mut g_cpu = 0.0f32;
                let mut c_cpu = 0.0f32;

                {
                    let mut servers = sup.servers.lock();
                    for (name, s) in servers.iter_mut() {
                        if let Some(pid) = s.pid {
                            if let Some(proc) = sys.process(Pid::from(pid as usize)) {
                                let cpu = proc.cpu_usage();
                                let mem = (proc.memory() as f32) / (1024.0 * 1024.0);
                                total_cpu += cpu;
                                total_mem += mem;

                                if name == "login" { l_cpu = cpu; }
                                else if name == "game" { g_cpu = cpu; }
                                else if name == "chat" { c_cpu = cpu; }

                                s.cpu_history.push_back(cpu);
                                if s.cpu_history.len() > MAX_HISTORY_POINTS {
                                    s.cpu_history.pop_front();
                                }
                            }
                        }
                    }
                }

                let players = sup.get_online_players();
                let players_count = players.len();

                // 2. Add history point
                {
                    let mut hist = sup.history.lock();
                    hist.push_back(HistoryPoint {
                        timestamp: now_ts,
                        total_cpu,
                        total_mem_mb: total_mem,
                        login_cpu: l_cpu,
                        game_cpu: g_cpu,
                        chat_cpu: c_cpu,
                        players_count,
                    });
                    if hist.len() > MAX_HISTORY_POINTS {
                        hist.pop_front();
                    }
                }
            }
        });
    }

    pub fn get_dashboard_state(&self) -> DashboardStateResponse {
        let sys = self.system.lock();
        let servers_guard = self.servers.lock();
        let mut servers_out = Vec::new();
        let mut total_cpu = 0.0f32;
        let mut total_mem = 0.0f32;

        for (name, s) in servers_guard.iter() {
            let uptime = s.start_time.map(|t| t.elapsed().as_secs()).unwrap_or(0);
            let (cpu, mem) = if let Some(pid) = s.pid {
                if let Some(proc) = sys.process(Pid::from(pid as usize)) {
                    (proc.cpu_usage(), (proc.memory() as f32) / (1024.0 * 1024.0))
                } else {
                    (0.0, 0.0)
                }
            } else {
                (0.0, 0.0)
            };

            total_cpu += cpu;
            total_mem += mem;

            let (min_cpu, max_cpu, avg_cpu, trend) = if !s.cpu_history.is_empty() {
                let min = s.cpu_history.iter().copied().fold(f32::INFINITY, f32::min);
                let max = s.cpu_history.iter().copied().fold(0.0f32, f32::max);
                let sum: f32 = s.cpu_history.iter().sum();
                let avg = sum / (s.cpu_history.len() as f32);

                let trend = if s.cpu_history.len() >= 3 {
                    let recent_avg = s.cpu_history.iter().rev().take(3).sum::<f32>() / 3.0;
                    if recent_avg > avg + 1.0 {
                        "up".to_string()
                    } else if recent_avg < avg - 1.0 {
                        "down".to_string()
                    } else {
                        "stable".to_string()
                    }
                } else {
                    "stable".to_string()
                };

                (min, max, avg, trend)
            } else {
                (cpu, cpu, cpu, "stable".to_string())
            };

            servers_out.push(ServerMetrics {
                name: name.clone(),
                status: s.status.clone(),
                pid: s.pid,
                uptime_secs: uptime,
                cpu_percent: cpu,
                memory_mb: mem,
                min_cpu,
                max_cpu,
                avg_cpu,
                trend,
            });
        }

        let history = self.history.lock().iter().cloned().collect();
        let online_players = self.get_online_players();
        let online_count = online_players.len();

        DashboardStateResponse {
            servers: servers_out,
            total_cpu_percent: total_cpu,
            total_memory_mb: total_mem,
            history,
            online_players,
            online_count,
            launcher_uptime_secs: self.start_time.elapsed().as_secs(),
        }
    }

    pub fn get_online_players(&self) -> Vec<OnlinePlayerInfo> {
        let mut players = Vec::new();
        let db_path = "aion.db";

        if let Ok(conn) = rusqlite::Connection::open_with_flags(
            db_path,
            rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY | rusqlite::OpenFlags::SQLITE_OPEN_NO_MUTEX,
        ) {
            let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64;
            
            let stmt = conn.prepare(
                "SELECT s.token, s.username, s.issued_at, IFNULL(c.name, 'Nenhum') 
                 FROM sessions s 
                 LEFT JOIN accounts a ON a.username = s.username 
                 LEFT JOIN characters c ON c.account_id = a.id 
                 ORDER BY s.issued_at DESC LIMIT 50"
            ).or_else(|_| {
                conn.prepare(
                    "SELECT token, account_name, created_at, 'Personagem Ativo' 
                     FROM sessions 
                     ORDER BY created_at DESC LIMIT 50"
                )
            });

            if let Ok(mut query) = stmt {
                let rows = query.query_map([], |row| {
                    let _token: String = row.get(0)?;
                    let username: String = row.get(1)?;
                    let created_at: i64 = row.get(2)?;
                    let char_name: String = row.get(3)?;
                    let duration = (now - created_at).max(0) as u64;

                    let login_time = chrono::DateTime::from_timestamp(created_at, 0)
                        .map(|dt| chrono::DateTime::<chrono::Local>::from(dt).format("%H:%M:%S").to_string())
                        .unwrap_or_else(|| "--:--:--".to_string());

                    Ok(OnlinePlayerInfo {
                        account_name: username,
                        character_name: char_name,
                        login_time,
                        duration_secs: duration,
                        server: "Atreia (Oficial)".to_string(),
                        status: "Conectado".to_string(),
                    })
                });

                if let Ok(iter) = rows {
                    for p in iter.flatten() {
                        players.push(p);
                    }
                }
            }
        }

        players
    }

    pub fn get_tray_tooltip_text(&self) -> String {
        let servers = self.servers.lock();
        let login_stat = servers.get("login").map(|s| match s.status {
            ServerStatus::Online => "Online",
            ServerStatus::Starting => "Iniciando",
            ServerStatus::Stopping => "Parando",
            ServerStatus::Crashed => "Erro",
            ServerStatus::Offline => "Offline",
        }).unwrap_or("Offline");

        let game_stat = servers.get("game").map(|s| match s.status {
            ServerStatus::Online => "Online",
            ServerStatus::Starting => "Iniciando",
            ServerStatus::Stopping => "Parando",
            ServerStatus::Crashed => "Erro",
            ServerStatus::Offline => "Offline",
        }).unwrap_or("Offline");

        let chat_stat = servers.get("chat").map(|s| match s.status {
            ServerStatus::Online => "Online",
            ServerStatus::Starting => "Iniciando",
            ServerStatus::Stopping => "Parando",
            ServerStatus::Crashed => "Erro",
            ServerStatus::Offline => "Offline",
        }).unwrap_or("Offline");

        let uptime = self.start_time.elapsed().as_secs();
        let hrs = uptime / 3600;
        let mins = (uptime % 3600) / 60;
        let secs = uptime % 60;

        let players_count = self.get_online_players().len();

        format!(
            "Emulador Rust\nLogin: {}\nGame: {}\nChat: {}\nJogadores: {}\nTempo online: {:02}:{:02}:{:02}",
            login_stat, game_stat, chat_stat, players_count, hrs, mins, secs
        )
    }

    pub fn spawn_crash_monitor(&self) {
        let sup = self.clone();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_millis(1000)).await;
                let to_restart = {
                    let mut servers = sup.servers.lock();
                    let mut list = Vec::new();

                    for (name, s) in servers.iter_mut() {
                        if s.status == ServerStatus::Online && !s.user_stopped {
                            if let Some(child) = s.child.as_mut() {
                                if let Ok(Some(exit_status)) = child.try_wait() {
                                    sup.log_center.push(name, &format!("QUEDA DETECTADA: Processo encerrou com status {:?}", exit_status));
                                    s.status = ServerStatus::Crashed;
                                    s.child = None;
                                    s.pid = None;
                                    s.start_time = None;

                                    if sup.config.launcher.restartOnCrash {
                                        list.push(name.clone());
                                    }
                                }
                            }
                        }
                    }
                    list
                };

                for name in to_restart {
                    sup.log_center.push(&name, "Reiniciando servidor automaticamente em instantes...");
                    tokio::time::sleep(Duration::from_millis(sup.config.launcher.crashRestartDelayMs)).await;
                    let _ = sup.start_server(&name).await;
                }
            }
        });
    }
}
