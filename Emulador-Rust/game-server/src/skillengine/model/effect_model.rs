//! Instância de Efeito Ativo (Effect - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;
use crate::skillengine::model::abnormal_state::AbnormalStateMask;
use crate::skillengine::model::skill_target_slot::{DispelCategoryType, SkillTargetSlot};

#[derive(Debug, Clone)]
pub struct Effect {
    pub effector_id: u32,
    pub effected_id: u32,
    pub skill_id: u32,
    pub skill_level: u8,
    pub target_slot: SkillTargetSlot,
    pub dispel_category: DispelCategoryType,
    pub abnormal_state: AbnormalStateMask,
    pub duration_ms: u32,
    pub applied_at: Instant,
    pub next_tick_at: Option<Instant>,
    pub tick_interval_ms: u32,
    pub value: i32,
    pub shield_capacity: i32,
    pub is_active: bool,
}

impl Effect {
    pub fn new(
        effector_id: u32,
        effected_id: u32,
        skill_id: u32,
        skill_level: u8,
        target_slot: SkillTargetSlot,
        duration_ms: u32,
        value: i32,
    ) -> Self {
        let now = Instant::now();
        Self {
            effector_id,
            effected_id,
            skill_id,
            skill_level,
            target_slot,
            dispel_category: DispelCategoryType::Buff,
            abnormal_state: AbnormalStateMask::NONE,
            duration_ms,
            applied_at: now,
            next_tick_at: None,
            tick_interval_ms: 0,
            value,
            shield_capacity: 0,
            is_active: true,
        }
    }

    pub fn is_expired(&self, now: Instant) -> bool {
        if self.duration_ms == 0 {
            return false; // Permanente / passivo
        }
        let elapsed = now.duration_since(self.applied_at).as_millis() as u32;
        elapsed >= self.duration_ms
    }

    pub fn remaining_time_ms(&self, now: Instant) -> u32 {
        if self.duration_ms == 0 {
            return 0;
        }
        let elapsed = now.duration_since(self.applied_at).as_millis() as u32;
        self.duration_ms.saturating_sub(elapsed)
    }
}
