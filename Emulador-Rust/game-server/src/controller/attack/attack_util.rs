//! Utilitários e Cálculos de Ataques e Fórmulas de Dano (AttackUtil - Padrão Java Aion Classic 2.8 / 4.5)

use super::attack_result::AttackResult;
use super::attack_status::AttackStatus;

pub struct AttackUtil;

impl AttackUtil {
    /// Calcula o status do ataque físico considerando precisão, esquiva, aparo, bloqueio e crítico
    pub fn calculate_physical_status(
        accuracy: i32,
        evasion: i32,
        parry: i32,
        block: i32,
        crit_rate: i32,
        crit_resist: i32,
    ) -> AttackStatus {
        let is_crit = (crit_rate - crit_resist).max(0) > 200; // Formula canônica Aion

        let diff_dodge = evasion - accuracy;
        if diff_dodge > 300 {
            return if is_crit { AttackStatus::CriticalDodge } else { AttackStatus::Dodge };
        }

        let diff_parry = parry - accuracy;
        if diff_parry > 200 {
            return if is_crit { AttackStatus::CriticalParry } else { AttackStatus::Parry };
        }

        let diff_block = block - accuracy;
        if diff_block > 200 {
            return if is_crit { AttackStatus::CriticalBlock } else { AttackStatus::Block };
        }

        if is_crit {
            AttackStatus::Critical
        } else {
            AttackStatus::NormalHit
        }
    }

    /// Calcula o dano final considerando status, mitigação e absorção de escudo
    pub fn calculate_final_damage(
        base_damage: i32,
        status: AttackStatus,
        shield_remaining: i32,
    ) -> AttackResult {
        let mut raw_damage = base_damage;

        match status {
            AttackStatus::Dodge | AttackStatus::OffhandDodge => {
                return AttackResult::new(0, status);
            }
            AttackStatus::Parry | AttackStatus::OffhandParry => {
                raw_damage = (raw_damage as f32 * 0.6) as i32; // 40% de redução no parry
            }
            AttackStatus::Block | AttackStatus::OffhandBlock => {
                raw_damage = (raw_damage as f32 * 0.3) as i32; // 70% de redução no block
            }
            AttackStatus::Critical | AttackStatus::OffhandCritical => {
                raw_damage = (raw_damage as f32 * 1.5) as i32; // 1.5x no critical
            }
            _ => {}
        }

        if shield_remaining > 0 {
            let absorbed = raw_damage.min(shield_remaining);
            let final_dmg = raw_damage - absorbed;
            AttackResult::new(final_dmg, status).with_shield(absorbed)
        } else {
            AttackResult::new(raw_damage, status)
        }
    }
}
