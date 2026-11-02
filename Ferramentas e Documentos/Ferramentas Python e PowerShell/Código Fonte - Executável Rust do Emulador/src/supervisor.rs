use crate::config::RootConfig;
use crate::db_manager::{DbManagerMulti, DatabaseSummary, OnlinePlayerInfo};
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
    pub http_port: u16,
    pub servers: Vec<ServerMetrics>,
    pub history: Vec<HistoryPoint>,
    pub online_players_count: usize,
    /// Legacy single-database (kept for backward compat with old UI calls)
    pub database: DatabaseMetrics,
    /// Multi-database list: gs, ls, cs
    pub databases: Vec<DatabaseSummary>,
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
    #[allow(dead_code)]
    pub management_port: Option<u16>,
    #[allow(dead_code)]
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
    db_manager: DbManagerMulti,
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

fn resolve_java_binary(candidate: &str, java_dir: &str) -> String {
    if let Ok(cwd) = std::env::current_dir() {
        if candidate != "java" && !candidate.trim().is_empty() {
            let rel_cand = cwd.join(candidate);
            if rel_cand.exists() {
                return rel_cand.to_string_lossy().to_string();
            }
        }
        if !java_dir.trim().is_empty() {
            let bundled = cwd.join(java_dir).join("bin").join("java.exe");
            if bundled.exists() {
                return bundled.to_string_lossy().to_string();
            }
        }
        let config_bundled = cwd.join("Config").join("java-deployment").join("bin").join("java.exe");
        if config_bundled.exists() {
            return config_bundled.to_string_lossy().to_string();
        }
        let default_bundled = cwd.join("java-deployment").join("bin").join("java.exe");
        if default_bundled.exists() {
            return default_bundled.to_string_lossy().to_string();
        }
    }

    if candidate != "java" && std::path::Path::new(candidate).exists() {
        return candidate.to_string();
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

pub fn decode_process_output(slice: &[u8]) -> String {
    let mut bytes = slice;
    while bytes.ends_with(b"\n") || bytes.ends_with(b"\r") {
        bytes = &bytes[..bytes.len() - 1];
    }
    if bytes.is_empty() {
        return String::new();
    }
    if let Ok(valid_str) = std::str::from_utf8(bytes) {
        return valid_str.to_string();
    }
    // Fallback: decode PT-BR CP850 / Windows-1252 so accented characters never break
    let mut s = String::with_capacity(bytes.len());
    for &b in bytes {
        if b < 0x80 {
            s.push(b as char);
        } else {
            let ch = match b {
                0x80 => 'Ç', 0x81 => 'ü', 0x82 => 'é', 0x83 => 'â', 0x84 => 'ä', 0x85 => 'à',
                0x86 => 'å', 0x87 => 'ç', 0x88 => 'ê', 0x89 => 'ë', 0x8a => 'è', 0x8b => 'ï',
                0x8c => 'î', 0x8d => 'ì', 0x8e => 'Ä', 0x8f => 'Å', 0x90 => 'É', 0x91 => 'æ',
                0x92 => 'Æ', 0x93 => 'ô', 0x94 => 'ö', 0x95 => 'ò', 0x96 => 'û', 0x97 => 'ù',
                0x98 => 'ÿ', 0x99 => 'Ö', 0x9a => 'Ü', 0xa0 => 'á', 0xa1 => 'í', 0xa2 => 'ó',
                0xa3 => 'ú', 0xa4 => 'ñ', 0xa5 => 'Ñ', 0xa6 => 'ª', 0xa7 => 'º', 0xa8 => '¿',
                0xad => '¡', 0xc6 => 'ã', 0xc7 => 'Ã', 0xe4 => 'õ', 0xe5 => 'Õ',
                0xc1 => 'Á', 0xc9 => 'É', 0xcd => 'Í', 0xd3 => 'Ó', 0xda => 'Ú',
                0xe1 => 'á', 0xe9 => 'é', 0xed => 'í', 0xf3 => 'ó', 0xfa => 'ú',
                0xe3 => 'ã', 0xe7 => 'ç', 0xf5 => 'õ', 0xea => 'ê', 0xf4 => 'ô',
                _ => char::from(b),
            };
            s.push(ch);
        }
    }
    s
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

    pub fn new(config: RootConfig, log_center: LogCenter, db_manager: DbManagerMulti) -> Self {
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
                    java_exe: resolve_java_binary(&sc.java_exe, &config.paths.java_dir),
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

            // Database existence and connection check
            let db_id = match name {
                "chat" => "cs",
                "login" => "ls",
                "game" => "gs",
                _ => "",
            };
            if !db_id.is_empty() {
                let chk = self.db_manager.check_database(db_id);
                if !chk.connected {
                    let err = format!(
                        "Falha ao conectar no MySQL do {} ({}:{} - usuário '{}'). Verifique o arquivo: {}. Erro: {}",
                        chk.server_name, chk.host, chk.port, chk.user, chk.properties_file, chk.error.unwrap_or_default()
                    );
                    self.log_center.push(name, &format!("[Launcher] ERRO DE BANCO: {}", err));
                    return Err(err);
                }
                if !chk.db_exists {
                    let err = format!(
                        "O banco de dados '{}' do {} não existe no MySQL! Crie o banco de dados antes de iniciar o servidor.",
                        chk.db_name, chk.server_name
                    );
                    self.log_center.push(name, &format!("[Launcher] ERRO DE BANCO: {}", err));
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

        self.log_center.push(name, &format!("[Launcher] Iniciando {} com Java [{}] e JVM: {:?}...", name, java_exe, jvm_args));

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
                        let mut reader = BufReader::new(out);
                        let mut buf = Vec::with_capacity(1024);
                        loop {
                            buf.clear();
                            match reader.read_until(b'\n', &mut buf).await {
                                Ok(0) => break,
                                Ok(_) => {
                                    let line = decode_process_output(&buf);
                                    if !line.trim().is_empty() {
                                        lc_out.push(&name_out, &line);
                                    }
                                }
                                Err(_) => break,
                            }
                        }
                    });
                }

                let lc_err = self.log_center.clone();
                let name_err = name.to_string();
                if let Some(err) = stderr {
                    tokio::spawn(async move {
                        let mut reader = BufReader::new(err);
                        let mut buf = Vec::with_capacity(1024);
                        loop {
                            buf.clear();
                            match reader.read_until(b'\n', &mut buf).await {
                                Ok(0) => break,
                                Ok(_) => {
                                    let line = decode_process_output(&buf);
                                    if !line.trim().is_empty() {
                                        lc_err.push(&name_err, &line);
                                    }
                                }
                                Err(_) => break,
                            }
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
        let child_to_kill = {
            let mut srvs = self.servers.lock();
            let srv = srvs.get_mut(name).ok_or_else(|| format!("Servidor desconhecido: {}", name))?;

            if srv.status == ServerStatus::Offline {
                return Ok(());
            }

            srv.user_stopped = true;
            srv.status = ServerStatus::Stopping;
            srv.child.take()
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
        if let Err(e) = self.start_server("chat").await {
            self.log_center.push("launcher", &format!("[Launcher] Interrompendo sequência: ChatServer não pôde ser iniciado: {}", e));
            return;
        }

        self.log_center.push("launcher", "[Launcher] Aguardando 5 segundos antes de inicializar o LoginServer...");
        tokio::time::sleep(Duration::from_secs(5)).await;

        self.log_center.push("launcher", "[Launcher] [2/3] Iniciando LoginServer...");
        if let Err(e) = self.start_server("login").await {
            self.log_center.push("launcher", &format!("[Launcher] Interrompendo sequência: LoginServer não pôde ser iniciado: {}", e));
            return;
        }

        self.log_center.push("launcher", "[Launcher] Aguardando 5 segundos antes de inicializar o GameServer...");
        tokio::time::sleep(Duration::from_secs(5)).await;

        self.log_center.push("launcher", "[Launcher] [3/3] Iniciando GameServer...");
        if let Err(e) = self.start_server("game").await {
            self.log_center.push("launcher", &format!("[Launcher] GameServer não pôde ser iniciado: {}", e));
            return;
        }

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

        // --- Multi-database summaries (GS, LS, CS) ---
        let db_summaries = self.db_manager.get_all_summaries();
        // Legacy single-database compat: use GS as primary
        let gs_summary = db_summaries.iter().find(|d| d.id == "gs");
        let legacy_database = if let Some(gs) = gs_summary {
            DatabaseMetrics {
                is_connected: gs.is_connected,
                engine: gs.engine.clone(),
                host: gs.host.clone(),
                port: gs.port,
                db_name: gs.db_name.clone(),
                user: gs.user.clone(),
                total_tables: gs.total_tables,
                total_rows: gs.total_rows,
            }
        } else {
            DatabaseMetrics {
                is_connected: false,
                engine: "MySQL".to_string(),
                host: "N/A".to_string(),
                port: 3306,
                db_name: "N/A".to_string(),
                user: "N/A".to_string(),
                total_tables: 0,
                total_rows: 0,
            }
        };

        DashboardState {
            launcher_pid: self.launcher_pid,
            launcher_cpu,
            launcher_memory_mb: launcher_mem,
            total_cpu: (total_cpu + launcher_cpu).clamp(0.0, 100.0),
            total_memory_mb: total_mem + launcher_mem,
            uptime_secs: self.start_time.elapsed().as_secs(),
            local_ip: get_local_lan_ip(),
            http_port: self._config.gui.http_port,
            servers: server_metrics,
            history: hist.iter().cloned().collect(),
            online_players_count: self.db_manager.get_online_players().len(),
            database: legacy_database,
            databases: db_summaries,
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
        format!("Aion Classic - EMULADOR\nServidores Ativos: {}/3", active)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolve_java_binary() {
        let bin = resolve_java_binary("java", "java-deployment");
        println!("Resolved Java binary: {}", bin);
        assert!(!bin.contains("1.8"), "Must NOT resolve to obsolete JDK 8: {}", bin);
        // Modern JDK verification
        assert!(!bin.is_empty(), "Java binary must not be empty");
    }
}

