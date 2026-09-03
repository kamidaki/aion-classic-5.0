use crate::config::RootConfig;
use crate::db_manager::{DbManager, OnlinePlayerInfo};
use crate::logs::LogCenter;
use parking_lot::Mutex;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use std::net::UdpSocket;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use std::time::{Duration, Instant};
use sysinfo::{Pid, ProcessRefreshKind, RefreshKind, System};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, Command};

const CREATE_NO_WINDOW: u32 = 0x08000000;
const MAX_HISTORY_POINTS: usize = 120;

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
    pub label: String,
    pub tag: String,
    pub color: String,
    pub status: ServerStatus,
    pub pid: Option<u32>,
    pub uptime_secs: u64,
    pub cpu_percent: f32,
    pub memory_mb: f32,
    pub min_cpu: f32,
    pub max_cpu: f32,
    pub avg_cpu: f32,
    pub trend: String,
    pub countdown_secs: Option<u64>,
}

#[derive(Debug, Clone, Serialize)]
pub struct SubsystemMetric {
    pub id: String,
    pub name: String,
    pub category: String,
    pub file_source: String,
    pub color: String,
    pub cpu_percent: f32,
    pub memory_mb: f32,
    pub count_metric: String,
    pub status: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct HistoryPoint {
    pub timestamp: String,
    pub total_cpu: f32,
    pub total_mem_mb: f32,
    pub login_cpu: f32,
    pub game_cpu: f32,
    pub chat_cpu: f32,
    pub launcher_cpu: f32,
    pub login_mem_mb: f32,
    pub game_mem_mb: f32,
    pub chat_mem_mb: f32,
    pub launcher_mem_mb: f32,
    pub players_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseMetrics {
    pub is_connected: bool,
    pub engine: String,
    pub host: String,
    pub port: u16,
    pub db_name: String,
    pub user: String,
    pub total_tables: usize,
    pub total_rows: i64,
}

#[derive(Debug, Clone, Serialize)]
pub struct DashboardState {
    pub launcher_pid: u32,
    pub launcher_cpu: f32,
    pub launcher_memory_mb: f32,
    pub total_cpu: f32,
    pub total_memory_mb: f32,
    pub uptime_secs: u64,
    pub local_ip: String,
    pub servers: Vec<ServerMetrics>,
    pub history: Vec<HistoryPoint>,
    pub online_players_count: usize,
    pub database: DatabaseMetrics,
    pub os_total_memory_mb: f32,
    pub os_used_memory_mb: f32,
    pub subsystems: Vec<SubsystemMetric>,
}

pub struct ManagedServer {
    pub name: String,
    pub label: String,
    pub tag: String,
    pub color: String,
    pub working_dir: PathBuf,
    pub java_exe: String,
    pub jvm_args: Vec<String>,
    pub classpath: String,
    pub main_class: String,
    pub management_port: Option<u16>,
    pub shutdown_delay_seconds: u64,
    pub child: Option<Child>,
    pub pid: Option<u32>,
    pub status: ServerStatus,
    pub start_time: Option<Instant>,
    pub user_stopped: bool,
    pub cpu_history: VecDeque<f32>,
    pub stopping_deadline: Option<Instant>,
}

#[derive(Clone)]
pub struct Supervisor {
    servers: Arc<Mutex<HashMap<String, ManagedServer>>>,
    log_center: LogCenter,
    _config: RootConfig,
    system: Arc<Mutex<System>>,
    start_time: Instant,
    history: Arc<Mutex<VecDeque<HistoryPoint>>>,
    db_manager: DbManager,
    launcher_pid: u32,
}

pub fn get_local_lan_ip() -> String {
    if let Ok(socket) = UdpSocket::bind("0.0.0.0:0") {
        if socket.connect("8.8.8.8:80").is_ok() {
            if let Ok(addr) = socket.local_addr() {
                return addr.ip().to_string();
            }
        }
    }
    "127.0.0.1".to_string()
}

fn resolve_java_binary(candidate: &str) -> String {
    if candidate != "java" && std::path::Path::new(candidate).exists() {
        return candidate.to_string();
    }

    // Prioritize official JDK 8 paths required by Aion Classic emulator
    let defaults = [
        r"C:\Program Files\Java\jdk1.8.0_431\bin\java.exe",
        r"C:\Program Files\Java\jdk-1.8\bin\java.exe",
        r"C:\Program Files\Java\jre1.8.0_431\bin\java.exe",
    ];

    for d in &defaults {
        if std::path::Path::new(d).exists() {
            return d.to_string();
        }
    }

    if let Ok(java_home) = std::env::var("JAVA_HOME") {
        let p = PathBuf::from(java_home).join("bin").join("java.exe");
        if p.exists() {
            return p.to_string_lossy().to_string();
        }
    }

    "java".to_string()
}

fn is_port_in_use(port: u16) -> bool {
    let addr = std::net::SocketAddr::from(([127, 0, 0, 1], port));
    if std::net::TcpStream::connect_timeout(&addr, Duration::from_millis(150)).is_ok() {
        return true;
    }
    std::net::TcpListener::bind(("0.0.0.0", port)).is_err()
}

impl Supervisor {
    pub fn purge_orphaned_java_processes(log_center: &LogCenter) {
        let mut sys = System::new_with_specifics(
            RefreshKind::new().with_processes(ProcessRefreshKind::new()),
        );
        sys.refresh_processes();

        let my_pid = std::process::id();
        let targets = [
            "chatserver-classicemu-brasil.jar",
            "loginserver-classicemu-brasil.jar",
            "gameserver-classicemu-brasil.jar",
            "al-chat.jar",
            "encom-login",
            "encom-game",
            "com.aionemu.gameserver.gameserver",
            "com.aionemu.loginserver.loginserver",
            "com.aionemu.chatserver.chatserver",
        ];

        for (pid, proc) in sys.processes() {
            if pid.as_u32() == my_pid {
                continue;
            }
            let name = proc.name().to_lowercase();
            let is_java = name == "java.exe" || name == "javaw.exe" || name == "java";
            if !is_java {
                continue;
            }

            let cmdline = proc.cmd().join(" ").to_lowercase();
            let mut matched = false;
            for t in &targets {
                if cmdline.contains(t) {
                    matched = true;
                    break;
                }
            }

            if matched {
                log_center.push(
                    "launcher",
                    &format!(
                        "[Supervisor] Processo Java orfão detectado (PID: {}) de execução anterior. Finalizando para liberar portas...",
                        pid.as_u32()
                    ),
                );
                let _ = proc.kill();
            }
        }
    }

    pub fn new(config: RootConfig, log_center: LogCenter, db_manager: DbManager) -> Self {
        // Purge any orphaned Java processes from previous crashes or unclosed sessions
        Self::purge_orphaned_java_processes(&log_center);

        let mut servers = HashMap::new();

        for (id, sc) in &config.servers {
            let working_dir = PathBuf::from(&sc.working_dir);
            servers.insert(
                id.clone(),
                ManagedServer {
                    name: id.clone(),
                    label: sc.label.clone(),
                    tag: sc.tag.clone(),
                    color: sc.color.clone(),
                    working_dir,
                    java_exe: resolve_java_binary(&sc.java_exe),
                    jvm_args: sc.jvm_args.clone(),
                    classpath: sc.classpath.clone(),
                    main_class: sc.main_class.clone(),
                    management_port: sc.management_port,
                    shutdown_delay_seconds: sc.shutdown_delay_seconds,
                    child: None,
                    pid: None,
                    status: ServerStatus::Offline,
                    start_time: None,
                    user_stopped: false,
                    cpu_history: VecDeque::with_capacity(MAX_HISTORY_POINTS),
                    stopping_deadline: None,
                },
            );
        }

        let system = System::new_with_specifics(
            RefreshKind::new()
                .with_processes(ProcessRefreshKind::new().with_cpu().with_memory())
                .with_memory(sysinfo::MemoryRefreshKind::everything()),
        );

        Self {
            servers: Arc::new(Mutex::new(servers)),
            log_center,
            _config: config,
            system: Arc::new(Mutex::new(system)),
            start_time: Instant::now(),
            history: Arc::new(Mutex::new(VecDeque::with_capacity(MAX_HISTORY_POINTS))),
            db_manager,
            launcher_pid: std::process::id(),
        }
    }

    pub async fn start_server(&self, name: &str) -> Result<(), String> {
        let (java_exe, jvm_args, classpath, main_class, working_dir) = {
            let mut srvs = self.servers.lock();
            let srv = srvs.get_mut(name).ok_or_else(|| format!("Servidor desconhecido: {}", name))?;

            if srv.status == ServerStatus::Online || srv.status == ServerStatus::Starting {
                return Err(format!("O servidor {} já está em execução ou inicializando.", name));
            }

            // Port de-duplication check
            let expected_port = match name {
                "login" => Some(2106),
                "game" => Some(7777),
                "chat" => Some(10241),
                _ => None,
            };

            if let Some(port) = expected_port {
                if is_port_in_use(port) {
                    let err = format!("A porta de rede {} do {} já está em uso por outro processo!", port, name);
                    self.log_center.push(name, &format!("[Launcher] ERRO: {}", err));
                    return Err(err);
                }
            }

            srv.status = ServerStatus::Starting;
            srv.user_stopped = false;
            srv.stopping_deadline = None;

            (
                srv.java_exe.clone(),
                srv.jvm_args.clone(),
                srv.classpath.clone(),
                srv.main_class.clone(),
                srv.working_dir.clone(),
            )
        };

        let mut cmd = Command::new(&java_exe);
        for arg in &jvm_args {
            cmd.arg(arg);
        }
        cmd.arg("-cp").arg(&classpath);
        cmd.arg(&main_class);
        cmd.current_dir(&working_dir);
        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());
        cmd.creation_flags(CREATE_NO_WINDOW);

        self.log_center.push(name, &format!("[Launcher] Iniciando {} com JVM: {:?}...", name, jvm_args));

        match cmd.spawn() {
            Ok(mut child) => {
                let pid = child.id().unwrap_or(0);
                let stdout = child.stdout.take();
                let stderr = child.stderr.take();

                {
                    let mut srvs = self.servers.lock();
                    if let Some(srv) = srvs.get_mut(name) {
                        srv.child = Some(child);
                        srv.pid = Some(pid);
                        srv.status = ServerStatus::Online;
                        srv.start_time = Some(Instant::now());
                    }
                }

                self.log_center.push(name, &format!("[Launcher] {} inicializado com sucesso (PID: {})", name, pid));

                let lc_out = self.log_center.clone();
                let name_out = name.to_string();
                if let Some(out) = stdout {
                    tokio::spawn(async move {
                        let mut reader = BufReader::new(out).lines();
                        while let Ok(Some(line)) = reader.next_line().await {
                            lc_out.push(&name_out, &line);
                        }
                    });
                }

                let lc_err = self.log_center.clone();
                let name_err = name.to_string();
                if let Some(err) = stderr {
                    tokio::spawn(async move {
                        let mut reader = BufReader::new(err).lines();
                        while let Ok(Some(line)) = reader.next_line().await {
                            lc_err.push(&name_err, &line);
                        }
                    });
                }

                Ok(())
            }
            Err(e) => {
                let mut srvs = self.servers.lock();
                if let Some(srv) = srvs.get_mut(name) {
                    srv.status = ServerStatus::Crashed;
                }
                let err_msg = format!("Falha ao iniciar {}: {}", name, e);
                self.log_center.push(name, &err_msg);
                Err(err_msg)
            }
        }
    }

    pub async fn stop_server(&self, name: &str) -> Result<(), String> {
        let (management_port, shutdown_delay, child_exists) = {
            let mut srvs = self.servers.lock();
            let srv = srvs.get_mut(name).ok_or_else(|| format!("Servidor desconhecido: {}", name))?;

            if srv.status == ServerStatus::Offline {
                return Ok(());
            }

            srv.user_stopped = true;
            (srv.management_port, srv.shutdown_delay_seconds, srv.child.is_some())
        };

        if !child_exists {
            let mut srvs = self.servers.lock();
            if let Some(s) = srvs.get_mut(name) {
                s.status = ServerStatus::Offline;
            }
            return Ok(());
        }

        // Se o servidor tiver porta de gerenciamento (ex: GameServer), dispara desligamento seguro
        if let Some(port) = management_port {
            {
                let mut srvs = self.servers.lock();
                if let Some(s) = srvs.get_mut(name) {
                    s.status = ServerStatus::Stopping;
                    s.stopping_deadline = Some(Instant::now() + Duration::from_secs(shutdown_delay));
                }
            }

            self.log_center.push(name, &format!("[Launcher] Solicitando desligamento seguro via porta de gerenciamento {}...", port));

            let client = reqwest_like_http_post(port, shutdown_delay, "shutdown").await;
            if client.is_ok() {
                self.log_center.push(name, "[Launcher] Comando de shutdown recebido pelo jogo. Gravando dados em disco...");
            } else {
                self.log_center.push(name, "[Launcher] Porta de gerenciamento indisponivel, aguardando saida do processo...");
            }

            // Aguarda o processo terminar graciosamente
            let max_wait = Duration::from_secs(shutdown_delay.min(15));
            let start = Instant::now();

            loop {
                tokio::time::sleep(Duration::from_millis(200)).await;
                let exited = {
                    let mut srvs = self.servers.lock();
                    if let Some(s) = srvs.get_mut(name) {
                        if let Some(child) = s.child.as_mut() {
                            match child.try_wait() {
                                Ok(Some(_)) => true,
                                Ok(None) => false,
                                Err(_) => true,
                            }
                        } else {
                            true
                        }
                    } else {
                        true
                    }
                };

                if exited {
                    break;
                }

                if start.elapsed() > max_wait {
                    self.log_center.push(name, "[Launcher] Tempo limite de shutdown seguro atingido. Finalizando processo...");
                    let child_to_kill = {
                        let mut srvs = self.servers.lock();
                        srvs.get_mut(name).and_then(|s| s.child.take())
                    };
                    if let Some(mut child) = child_to_kill {
                        let _ = child.kill().await;
                    }
                    break;
                }
            }

            let mut srvs = self.servers.lock();
            if let Some(s) = srvs.get_mut(name) {
                s.child = None;
                s.status = ServerStatus::Offline;
                s.pid = None;
                s.stopping_deadline = None;
            }

            self.log_center.push(name, &format!("[Launcher] {} finalizado com sucesso.", name));
            return Ok(());
        }

        // Caso contrario (LoginServer / ChatServer), encerra o processo diretamente
        let child_to_kill = {
            let mut srvs = self.servers.lock();
            if let Some(s) = srvs.get_mut(name) {
                s.status = ServerStatus::Stopping;
                s.child.take()
            } else {
                None
            }
        };

        if let Some(mut child) = child_to_kill {
            let _ = child.kill().await;
            let _ = child.wait().await;
        }

        {
            let mut srvs = self.servers.lock();
            if let Some(s) = srvs.get_mut(name) {
                s.status = ServerStatus::Offline;
                s.pid = None;
                s.stopping_deadline = None;
            }
        }

        self.log_center.push(name, &format!("[Launcher] {} finalizado com sucesso.", name));
        Ok(())
    }

    pub async fn restart_server(&self, name: &str) -> Result<(), String> {
        self.stop_server(name).await?;

        let self_clone = self.clone();
        let name_str = name.to_string();

        tokio::spawn(async move {
            // Aguarda o servidor atingir Offline
            loop {
                tokio::time::sleep(Duration::from_millis(500)).await;
                let status = {
                    let srvs = self_clone.servers.lock();
                    srvs.get(&name_str).map(|s| s.status.clone()).unwrap_or(ServerStatus::Offline)
                };

                if status == ServerStatus::Offline {
                    break;
                }
            }

            tokio::time::sleep(Duration::from_secs(2)).await;
            let _ = self_clone.start_server(&name_str).await;
        });

        Ok(())
    }

    pub async fn graceful_shutdown(&self) {
        self.log_center.push("launcher", "[Launcher] Encerrando todos os servidores graciosamente com segurança...");
        self.log_center.push("launcher", "[Launcher] [1/3] Finalizando Game-Server e salvando dados...");
        let _ = self.stop_server("game").await;

        self.log_center.push("launcher", "[Launcher] [2/3] Finalizando Login-Server...");
        let _ = self.stop_server("login").await;

        self.log_center.push("launcher", "[Launcher] [3/3] Finalizando Chat-Server...");
        let _ = self.stop_server("chat").await;

        // Limpeza final de segurança em todos os servidores
        let mut children_to_kill = Vec::new();
        {
            let mut srvs = self.servers.lock();
            for (_name, srv) in srvs.iter_mut() {
                if let Some(child) = srv.child.take() {
                    children_to_kill.push(child);
                }
                srv.status = ServerStatus::Offline;
                srv.pid = None;
                srv.stopping_deadline = None;
            }
        }

        for mut child in children_to_kill {
            let _ = child.kill().await;
        }

        self.log_center.push("launcher", "[Launcher] Todos os servidores foram encerrados com sucesso.");
    }

    pub async fn start_all_servers_sequentially(&self) {
        self.log_center.push("launcher", "[Launcher] Iniciando sequencia: ChatServer -> (5s) -> LoginServer -> (5s) -> GameServer.");
        
        self.log_center.push("launcher", "[Launcher] [1/3] Iniciando ChatServer...");
        let _ = self.start_server("chat").await;

        self.log_center.push("launcher", "[Launcher] Aguardando 5 segundos antes de inicializar o LoginServer...");
        tokio::time::sleep(Duration::from_secs(5)).await;

        self.log_center.push("launcher", "[Launcher] [2/3] Iniciando LoginServer...");
        let _ = self.start_server("login").await;

        self.log_center.push("launcher", "[Launcher] Aguardando 5 segundos antes de inicializar o GameServer...");
        tokio::time::sleep(Duration::from_secs(5)).await;

        self.log_center.push("launcher", "[Launcher] [3/3] Iniciando GameServer...");
        let _ = self.start_server("game").await;

        self.log_center.push("launcher", "[Launcher] Sequencia de servidores inicializada com sucesso.");
    }

    pub fn spawn_crash_monitor(&self) {
        let self_clone = self.clone();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_millis(1000)).await;
                let mut crashed_servers = Vec::new();

                {
                    let mut srvs = self_clone.servers.lock();
                    for (name, srv) in srvs.iter_mut() {
                        if let Some(child) = srv.child.as_mut() {
                            if let Ok(Some(status)) = child.try_wait() {
                                srv.child = None;
                                srv.pid = None;
                                srv.stopping_deadline = None;

                                if srv.user_stopped {
                                    srv.status = ServerStatus::Offline;
                                    self_clone.log_center.push(name, "[Launcher] Servidor finalizado voluntariamente.");
                                } else {
                                    srv.status = ServerStatus::Crashed;
                                    self_clone.log_center.push(
                                        name,
                                        &format!("[Launcher] CRASH DETECTADO: Processo encerrou com status {:?}", status),
                                    );
                                    crashed_servers.push(name.clone());
                                }
                            }
                        }
                    }
                }

                for name in crashed_servers {
                    let sup = self_clone.clone();
                    tokio::spawn(async move {
                        tokio::time::sleep(Duration::from_millis(2000)).await;
                        let _ = sup.start_server(&name).await;
                    });
                }
            }
        });
    }

    pub fn spawn_metrics_sampler(&self) {
        let self_clone = self.clone();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(Duration::from_millis(1000)).await;
                self_clone.sample_metrics();
            }
        });
    }

    fn sample_metrics(&self) {
        let num_cpus = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1) as f32;

        let mut sys = self.system.lock();
        sys.refresh_processes_specifics(
            ProcessRefreshKind::new().with_cpu().with_memory(),
        );
        sys.refresh_memory();

        let mut srvs = self.servers.lock();
        let mut total_cpu = 0.0f32;
        let mut total_mem = 0.0f32;

        let mut login_cpu = 0.0f32;
        let mut login_mem = 0.0f32;
        let mut game_cpu = 0.0f32;
        let mut game_mem = 0.0f32;
        let mut chat_cpu = 0.0f32;
        let mut chat_mem = 0.0f32;

        for (name, srv) in srvs.iter_mut() {
            if let Some(pid_u32) = srv.pid {
                let pid = Pid::from_u32(pid_u32);
                if let Some(proc) = sys.process(pid) {
                    let cpu = (proc.cpu_usage() / num_cpus).clamp(0.0, 100.0);
                    let mem = proc.memory() as f32 / (1024.0 * 1024.0);

                    srv.cpu_history.push_back(cpu);
                    if srv.cpu_history.len() > MAX_HISTORY_POINTS {
                        srv.cpu_history.pop_front();
                    }

                    total_cpu += cpu;
                    total_mem += mem;

                    match name.as_str() {
                        "login" => { login_cpu = cpu; login_mem = mem; },
                        "game" => { game_cpu = cpu; game_mem = mem; },
                        "chat" => { chat_cpu = cpu; chat_mem = mem; },
                        _ => {}
                    }
                }
            }
        }

        let launcher_pid = Pid::from_u32(self.launcher_pid);
        let (launcher_cpu, launcher_mem) = if let Some(proc) = sys.process(launcher_pid) {
            let cpu = (proc.cpu_usage() / num_cpus).clamp(0.0, 100.0);
            (cpu, proc.memory() as f32 / (1024.0 * 1024.0))
        } else {
            (0.0, 0.0)
        };

        let now_str = chrono::Local::now().format("%H:%M:%S").to_string();
        let players_count = self.db_manager.get_online_players().len();

        let mut hist = self.history.lock();
        hist.push_back(HistoryPoint {
            timestamp: now_str,
            total_cpu: (total_cpu + launcher_cpu).clamp(0.0, 100.0),
            total_mem_mb: total_mem + launcher_mem,
            login_cpu,
            game_cpu,
            chat_cpu,
            launcher_cpu,
            login_mem_mb: login_mem,
            game_mem_mb: game_mem,
            chat_mem_mb: chat_mem,
            launcher_mem_mb: launcher_mem,
            players_count,
        });

        if hist.len() > MAX_HISTORY_POINTS {
            hist.pop_front();
        }
    }

    pub fn get_dashboard_state(&self) -> DashboardState {
        let num_cpus = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1) as f32;

        let sys = self.system.lock();
        let srvs = self.servers.lock();
        let hist = self.history.lock();

        let mut server_metrics = Vec::new();
        let mut total_cpu = 0.0f32;
        let mut total_mem = 0.0f32;

        for (_id, srv) in srvs.iter() {
            let (cpu, mem) = if let Some(pid_u32) = srv.pid {
                let pid = Pid::from_u32(pid_u32);
                if let Some(proc) = sys.process(pid) {
                    let c = (proc.cpu_usage() / num_cpus).clamp(0.0, 100.0);
                    (c, proc.memory() as f32 / (1024.0 * 1024.0))
                } else {
                    (0.0, 0.0)
                }
            } else {
                (0.0, 0.0)
            };

            total_cpu += cpu;
            total_mem += mem;

            let uptime = srv.start_time.map(|t| t.elapsed().as_secs()).unwrap_or(0);
            let avg_cpu = if srv.cpu_history.is_empty() {
                0.0
            } else {
                srv.cpu_history.iter().sum::<f32>() / srv.cpu_history.len() as f32
            };

            let min_cpu = srv.cpu_history.iter().copied().fold(f32::INFINITY, f32::min);
            let max_cpu = srv.cpu_history.iter().copied().fold(f32::NEG_INFINITY, f32::max);

            let countdown = srv.stopping_deadline.map(|dl| {
                if dl > Instant::now() {
                    (dl - Instant::now()).as_secs()
                } else {
                    0
                }
            });

            server_metrics.push(ServerMetrics {
                name: srv.name.clone(),
                label: srv.label.clone(),
                tag: srv.tag.clone(),
                color: srv.color.clone(),
                status: srv.status.clone(),
                pid: srv.pid,
                uptime_secs: uptime,
                cpu_percent: cpu,
                memory_mb: mem,
                min_cpu: if min_cpu.is_finite() { min_cpu } else { 0.0 },
                max_cpu: if max_cpu.is_finite() { max_cpu } else { 0.0 },
                avg_cpu,
                trend: if cpu > avg_cpu { "up".to_string() } else { "down".to_string() },
                countdown_secs: countdown,
            });
        }

        let launcher_pid = Pid::from_u32(self.launcher_pid);
        let (launcher_cpu, launcher_mem) = if let Some(proc) = sys.process(launcher_pid) {
            let c = (proc.cpu_usage() / num_cpus).clamp(0.0, 100.0);
            (c, proc.memory() as f32 / (1024.0 * 1024.0))
        } else {
            (0.0, 0.0)
        };

        let os_total_mem = sys.total_memory() as f32 / (1024.0 * 1024.0);
        let os_used_mem = sys.used_memory() as f32 / (1024.0 * 1024.0);

        let (db_connected, db_tables, db_rows) = self.db_manager.get_summary();

        DashboardState {
            launcher_pid: self.launcher_pid,
            launcher_cpu,
            launcher_memory_mb: launcher_mem,
            total_cpu: (total_cpu + launcher_cpu).clamp(0.0, 100.0),
            total_memory_mb: total_mem + launcher_mem,
            uptime_secs: self.start_time.elapsed().as_secs(),
            local_ip: get_local_lan_ip(),
            servers: server_metrics,
            history: hist.iter().cloned().collect(),
            online_players_count: self.db_manager.get_online_players().len(),
            database: DatabaseMetrics {
                is_connected: db_connected,
                engine: "MySQL".to_string(),
                host: self.db_manager.host.clone(),
                port: self.db_manager.port,
                db_name: self.db_manager.db_name.clone(),
                user: self.db_manager.user.clone(),
                total_tables: db_tables,
                total_rows: db_rows,
            },
            os_total_memory_mb: os_total_mem,
            os_used_memory_mb: os_used_mem,
            subsystems: Vec::new(),
        }
    }

    pub fn get_online_players(&self) -> Vec<OnlinePlayerInfo> {
        self.db_manager.get_online_players()
    }

    pub fn get_tray_tooltip_text(&self) -> String {
        let srvs = self.servers.lock();
        let active = srvs.values().filter(|s| s.status == ServerStatus::Online).count();
        format!("Aion Classic - Classic Emu\nServidores Ativos: {}/3", active)
    }
}

async fn reqwest_like_http_post(port: u16, delay: u64, mode: &str) -> Result<(), ()> {
    use tokio::io::AsyncWriteExt;
    use tokio::net::TcpStream;

    let addr = format!("127.0.0.1:{}", port);
    let mut stream = TcpStream::connect(&addr).await.map_err(|_| ())?;

    let body = format!("{{\"delay\":{},\"mode\":\"{}\"}}", delay, mode);
    let req = format!(
        "POST /shutdown HTTP/1.1\r\nHost: 127.0.0.1:{}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        port, body.len(), body
    );

    stream.write_all(req.as_bytes()).await.map_err(|_| ())?;
    stream.flush().await.map_err(|_| ())?;
    Ok(())
}
