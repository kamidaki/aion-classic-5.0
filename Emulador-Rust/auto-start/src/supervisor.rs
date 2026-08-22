use crate::config::RootConfig;
use crate::logs::LogCenter;
use parking_lot::Mutex;
use serde::Serialize;
use std::collections::HashMap;
use std::process::Stdio;
use std::sync::Arc;
use std::time::{Duration, Instant};
use sysinfo::{Pid, ProcessRefreshKind, RefreshKind, System};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, Command};

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
}

struct ManagedServer {
    name: String,
    executable: String,
    child: Option<Child>,
    pid: Option<u32>,
    status: ServerStatus,
    start_time: Option<Instant>,
    user_stopped: bool,
}

#[derive(Clone)]
pub struct Supervisor {
    servers: Arc<Mutex<HashMap<String, ManagedServer>>>,
    log_center: LogCenter,
    config: RootConfig,
    system: Arc<Mutex<System>>,
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
        cmd.stdout(Stdio::piped()).stderr(Stdio::piped());

        match cmd.spawn() {
            Ok(mut child) => {
                let pid = child.id();
                println!("INFO: [Supervisor] Started {} with PID {:?}", exe, pid);
                log_center.push(&server_name, &format!("Process started with PID {:?}", pid));

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
                let err_msg = format!("Failed to spawn {}: {}", exe, e);
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
            println!("INFO: [Supervisor] Stopped server {}", name);
            self.log_center.push(name, "Process stopped by user");
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
        tokio::time::sleep(Duration::from_millis(500)).await;
        self.start_server(name).await
    }

    pub fn get_metrics(&self) -> Vec<ServerMetrics> {
        let mut sys = self.system.lock();
        sys.refresh_processes_specifics(
            ProcessRefreshKind::new().with_cpu().with_memory(),
        );

        let servers = self.servers.lock();
        let mut out = Vec::new();

        for (name, s) in servers.iter() {
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

            out.push(ServerMetrics {
                name: name.clone(),
                status: s.status.clone(),
                pid: s.pid,
                uptime_secs: uptime,
                cpu_percent: cpu,
                memory_mb: mem,
            });
        }

        out
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
                                    println!("WARN: [Supervisor] Server {} exited unexpectedly with status: {:?}", name, exit_status);
                                    sup.log_center.push(name, &format!("CRASH DETECTED: Process exited with {:?}", exit_status));
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
                    println!("INFO: [Supervisor] Auto-restarting crashed server {}...", name);
                    tokio::time::sleep(Duration::from_millis(sup.config.launcher.crashRestartDelayMs)).await;
                    let _ = sup.start_server(&name).await;
                }
            }
        });
    }
}
