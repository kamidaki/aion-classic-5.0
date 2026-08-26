//! Tarefa de Conjuração de Habilidade (CastTask - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

/// Estado de Conjuração em Progresso
#[derive(Debug, Clone)]
pub struct CastTask {
    pub caster_id: u32,
    pub target_id: u32,
    pub skill_id: u32,
    pub skill_level: u8,
    pub cast_start: Instant,
    pub cast_duration_ms: u32,
    pub is_canceled: bool,
}

impl CastTask {
    pub fn new(
        caster_id: u32,
        target_id: u32,
        skill_id: u32,
        skill_level: u8,
        cast_duration_ms: u32,
    ) -> Self {
        Self {
            caster_id,
            target_id,
            skill_id,
            skill_level,
            cast_start: Instant::now(),
            cast_duration_ms,
            is_canceled: false,
        }
    }

    /// Verifica se o cast já concluiu seu tempo
    pub fn is_finished(&self, now: Instant) -> bool {
        if self.is_canceled {
            return false;
        }
        let elapsed = now.duration_since(self.cast_start).as_millis() as u32;
        elapsed >= self.cast_duration_ms
    }

    /// Cancela a conjuração atual (por movimento ou dano que quebra cast)
    pub fn cancel(&mut self) {
        self.is_canceled = true;
    }
}
