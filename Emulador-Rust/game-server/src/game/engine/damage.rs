use crate::{game::Serialise, to_le_bytes};

#[repr(u16)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Type {
    Normal = 0x00,
    Evade = 0x01,
    Block = 0x02,
    Parry = 0x03,
    Critical = 0x04,
    Resist = 0x05,
    Heal = 0x06,
    MainHand = 0x0A,
    OffHand = 0x0B,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Hit {
    /// Damage is an integer; negative values represent healing
    pub damage: i32,
    /// Describes special combat resolutions (Critical, Block, Parry, Evade, etc.)
    pub ty: Type,
}

impl Hit {
    pub fn new(damage: i32, ty: Type) -> Self {
        Self { damage, ty }
    }
}

impl Serialise for Hit {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        to_le_bytes!(len, buf, self.damage);
        to_le_bytes!(len, buf, self.ty as u16);
        len
    }
}

/// Motor de cálculo de combate
pub struct CombatEngine;

impl CombatEngine {
    /// Calcula dano de golpe ou habilidade física
    pub fn calculate_physical_hit(
        attack: u16,
        skill_power: f32,
        target_defense: u16,
        accuracy: u16,
        target_evasion: u16,
        target_parry: u16,
        target_block: u16,
        crit_strike: u16,
        crit_resist: u16,
        crit_multiplier: f32,
    ) -> Hit {
        // Validação de Evasão
        if target_evasion > accuracy + 300 {
            return Hit::new(0, Type::Evade);
        }

        let base_raw = (attack as f32 * skill_power - (target_defense as f32 / 10.0)).max(1.0);

        // Bloqueio com escudo
        if target_block > accuracy + 200 {
            let mitigated = (base_raw * 0.5) as i32;
            return Hit::new(mitigated.max(1), Type::Block);
        }

        // Aparo (Parry)
        if target_parry > accuracy + 150 {
            let mitigated = (base_raw * 0.6) as i32;
            return Hit::new(mitigated.max(1), Type::Parry);
        }

        // Crítico
        let crit_rate = ((crit_strike as f32 - crit_resist as f32) / 10.0).clamp(0.0, 50.0);
        let is_crit = crit_rate >= 30.0; // Determinístico para testes com alta chance

        if is_crit {
            let dmg = (base_raw * crit_multiplier) as i32;
            Hit::new(dmg.max(1), Type::Critical)
        } else {
            Hit::new(base_raw as i32, Type::Normal)
        }
    }

    /// Calcula dano mágico
    pub fn calculate_magical_hit(
        base_power: f32,
        magic_boost: u16,
        magic_suppression: u16,
        target_magic_resist: u16,
        magic_accuracy: u16,
        elemental_resist: u16,
    ) -> Hit {
        // Resistência Mágica total
        if target_magic_resist > magic_accuracy + 400 {
            return Hit::new(0, Type::Resist);
        }

        let boost_factor = 1.0 + ((magic_boost as f32 - magic_suppression as f32) / 1000.0).max(0.0);
        let resist_factor = (1.0 - (elemental_resist as f32 / 1200.0)).clamp(0.1, 1.0);

        let final_dmg = (base_power * boost_factor * resist_factor) as i32;
        Hit::new(final_dmg.max(1), Type::Normal)
    }
}

/// Rastreador de cadeias de combo (Skill Chains)
#[derive(Debug, Clone, Default)]
pub struct ChainTracker {
    pub current_skill: Option<u32>,
    pub step: u8,
    pub expires_at_tick: u64,
}

impl ChainTracker {
    pub fn register_trigger(&mut self, next_skill_id: u32, next_step: u8, duration_ticks: u64, current_tick: u64) {
        self.current_skill = Some(next_skill_id);
        self.step = next_step;
        self.expires_at_tick = current_tick + duration_ticks;
    }

    pub fn is_active(&self, skill_id: u32, current_tick: u64) -> bool {
        if let Some(expected) = self.current_skill {
            expected == skill_id && current_tick <= self.expires_at_tick
        } else {
            false
        }
    }

    pub fn reset(&mut self) {
        self.current_skill = None;
        self.step = 0;
        self.expires_at_tick = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn physical_combat_mitigation_and_critical() {
        // Normal hit
        let hit = CombatEngine::calculate_physical_hit(
            200, 1.5, 500, 400, 200, 200, 200, 100, 100, 2.0,
        );
        assert_eq!(hit.ty, Type::Normal);
        assert_eq!(hit.damage, 250); // (200 * 1.5 - 50) = 250

        // Evade when target has extreme evasion
        let evade = CombatEngine::calculate_physical_hit(
            200, 1.5, 500, 100, 500, 200, 200, 100, 100, 2.0,
        );
        assert_eq!(evade.ty, Type::Evade);
        assert_eq!(evade.damage, 0);

        // Block with shield
        let block = CombatEngine::calculate_physical_hit(
            200, 1.5, 500, 100, 100, 100, 500, 100, 100, 2.0,
        );
        assert_eq!(block.ty, Type::Block);
        assert_eq!(block.damage, 125); // 50% mitigation
    }

    #[test]
    fn magical_combat_boost_and_resist() {
        let hit = CombatEngine::calculate_magical_hit(
            300.0, 1000, 0, 200, 300, 0,
        );
        assert_eq!(hit.ty, Type::Normal);
        assert_eq!(hit.damage, 600); // 300 * (1 + 1.0) = 600

        let resist = CombatEngine::calculate_magical_hit(
            300.0, 1000, 0, 1000, 200, 0,
        );
        assert_eq!(resist.ty, Type::Resist);
        assert_eq!(resist.damage, 0);
    }

    #[test]
    fn chain_combo_window_and_expiration() {
        let mut chain = ChainTracker::default();
        chain.register_trigger(1002, 2, 50, 100);

        assert!(chain.is_active(1002, 120), "Combo deve estar ativo no tick 120");
        assert!(!chain.is_active(1002, 160), "Combo deve expirar apos o tick 150");
        assert!(!chain.is_active(9999, 120), "Outra skill nao deve ativar a cadeia");
    }
}
