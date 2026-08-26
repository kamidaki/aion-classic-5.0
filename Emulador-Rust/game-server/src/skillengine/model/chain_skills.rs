//! Habilidades em Cadeia (ChainSkills - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

#[derive(Debug, Clone, PartialEq)]
pub struct ChainSkill {
    pub pre_skill_id: u32,
    pub next_skill_id: u32,
    pub time_window_secs: u32,
    pub trigger_rate: f32, // Chance de habilitar a corrente (ex: 100% ou 30%)
}

impl ChainSkill {
    pub fn new(pre_skill_id: u32, next_skill_id: u32, time_window_secs: u32, trigger_rate: f32) -> Self {
        Self {
            pre_skill_id,
            next_skill_id,
            time_window_secs,
            trigger_rate,
        }
    }
}

/// Estado de uma cadeia ativa para um jogador
#[derive(Debug, Clone)]
pub struct ActiveChainState {
    pub skill_id: u32,
    pub next_skill_id: u32,
    pub expires_at: Instant,
}
