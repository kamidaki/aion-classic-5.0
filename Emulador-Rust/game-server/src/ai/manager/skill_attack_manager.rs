//! Gerenciador de Uso de Habilidades de Monstros (SkillAttackManager - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

#[derive(Debug, Clone)]
pub struct MonsterSkillEntry {
    pub skill_id: u32,
    pub skill_level: u8,
    pub hp_threshold_percent: u8, // Só usa abaixo desta % de HP (ex: 50% ou 100%)
    pub cooldown_seconds: f32,
    pub last_used: Option<Instant>,
    pub cast_chance: f32, // Chance de uso (ex: 1.0 ou 0.4)
}

#[derive(Debug, Clone, Default)]
pub struct SkillAttackManager {
    pub skills: Vec<MonsterSkillEntry>,
}

impl SkillAttackManager {
    pub fn new() -> Self {
        Self { skills: Vec::new() }
    }

    pub fn add_skill(&mut self, skill_id: u32, skill_level: u8, hp_threshold_percent: u8, cooldown_seconds: f32) {
        self.skills.push(MonsterSkillEntry {
            skill_id,
            skill_level,
            hp_threshold_percent,
            cooldown_seconds,
            last_used: None,
            cast_chance: 1.0,
        });
    }

    /// Seleciona a próxima habilidade pronta para ser conjurada de acordo com o HP e tempo de recarga
    pub fn choose_skill(&mut self, hp_percent: u8, now: Instant) -> Option<(u32, u8)> {
        for entry in self.skills.iter_mut() {
            if hp_percent <= entry.hp_threshold_percent {
                let ready = match entry.last_used {
                    Some(last) => now.duration_since(last).as_secs_f32() >= entry.cooldown_seconds,
                    None => true,
                };

                if ready {
                    entry.last_used = Some(now);
                    return Some((entry.skill_id, entry.skill_level));
                }
            }
        }
        None
    }
}
