//! Temporizador de Missão por Tempo Limite (QuestTimer - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

#[derive(Debug, Clone)]
pub struct QuestTimer {
    pub quest_id: u32,
    pub duration_seconds: u32,
    pub started_at: Instant,
}

impl QuestTimer {
    pub fn new(quest_id: u32, duration_seconds: u32) -> Self {
        Self {
            quest_id,
            duration_seconds,
            started_at: Instant::now(),
        }
    }

    pub fn is_expired(&self) -> bool {
        self.started_at.elapsed().as_secs() >= self.duration_seconds as u64
    }

    pub fn remaining_seconds(&self) -> u32 {
        let elapsed = self.started_at.elapsed().as_secs() as u32;
        self.duration_seconds.saturating_sub(elapsed)
    }
}
