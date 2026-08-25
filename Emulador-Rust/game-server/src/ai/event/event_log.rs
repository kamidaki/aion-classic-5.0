//! Log de Eventos de IA (AIEventLog - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;
use crate::ai::event::event_type::AIEventType;

#[derive(Debug, Clone)]
pub struct AIEventLogEntry {
    pub event_type: AIEventType,
    pub timestamp: Instant,
    pub details: String,
}

#[derive(Debug, Clone, Default)]
pub struct AIEventLog {
    pub entries: Vec<AIEventLogEntry>,
    pub max_entries: usize,
}

impl AIEventLog {
    pub fn new(max_entries: usize) -> Self {
        Self {
            entries: Vec::with_capacity(max_entries),
            max_entries,
        }
    }

    pub fn log(&mut self, event_type: AIEventType, details: impl Into<String>) {
        if self.entries.len() >= self.max_entries {
            self.entries.remove(0);
        }
        self.entries.push(AIEventLogEntry {
            event_type,
            timestamp: Instant::now(),
            details: details.into(),
        });
    }
}
