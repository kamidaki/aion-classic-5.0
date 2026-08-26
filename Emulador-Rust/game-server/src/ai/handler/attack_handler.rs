//! Handler de Combate e Ataque da IA (AttackEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::attack_intention::AttackIntention;
use crate::character::Character;
use crate::engine::Coord;

pub struct AttackEventHandler;

impl AttackEventHandler {
    /// Avalia o alvo atual e decide entre ataque corpo a corpo ou aproximação
    pub fn evaluate_attack(
        npc_pos: &Coord,
        target_pos: &Coord,
        attack_range: f32,
    ) -> AttackIntention {
        let dist = npc_pos.distance(target_pos);
        if dist <= attack_range {
            AttackIntention::PhysicalAttack
        } else {
            AttackIntention::PhysicalAttack
        }
    }

    /// Executa um golpe físico básico contra o jogador
    pub fn execute_physical_hit(
        damage: i32,
        target: &mut Character,
    ) -> i32 {
        target.stats.hp.update(-damage);
        damage
    }
}
