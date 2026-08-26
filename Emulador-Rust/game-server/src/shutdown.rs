//! Hook de Desligamento Seguro do GameServer (Shutdown - Padrão Java Aion Classic Shutdown.java)

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

pub struct ShutdownHook {
    is_shutting_down: Arc<AtomicBool>,
    countdown_seconds: u32,
    announce_interval: u32,
}

impl ShutdownHook {
    pub fn new() -> Self {
        Self {
            is_shutting_down: Arc::new(AtomicBool::new(false)),
            countdown_seconds: 60,
            announce_interval: 10,
        }
    }

    pub fn is_shutting_down(&self) -> bool {
        self.is_shutting_down.load(Ordering::SeqCst)
    }

    pub fn start_shutdown(&self, seconds: u32) {
        self.is_shutting_down.store(true, Ordering::SeqCst);
        println!("[SHUTDOWN] Servidor entrando em processo de encerramento em {}s...", seconds);
    }

    pub fn cancel_shutdown(&self) {
        self.is_shutting_down.store(false, Ordering::SeqCst);
        println!("[SHUTDOWN] Processo de encerramento cancelado.");
    }
}

impl Default for ShutdownHook {
    fn default() -> Self {
        Self::new()
    }
}
