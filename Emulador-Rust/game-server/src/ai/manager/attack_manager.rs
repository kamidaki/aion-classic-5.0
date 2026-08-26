//! Gerenciador de Ataques e Combate de Criaturas (AttackManager / SimpleAttackManager - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::attack_intention::AttackIntention;
use crate::character::Character;
use crate::engine::damage::{CombatEngine, Hit};
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct AttackManager {
    pub attack_range: f32,
    pub attack_speed: f32,
    pub base_damage: i32,
}

impl AttackManager {
    pub fn new(attack_range: f32, attack_speed: f32, base_damage: i32) -> Self {
        Self {
            attack_range,
            attack_speed,
            base_damage,
        }
    }

    /// Calcula o golpe físico desferido pelo monstro contra o jogador
    pub fn calculate_attack_hit(&self, target: &Character) -> Hit {
        CombatEngine::calculate_physical_hit(
            self.base_damage.max(1) as u16,
            1.0,
            100,
            100,
            target.stats.secondary.evasion,
            target.stats.secondary.block,
            target.stats.secondary.parry,
            50,
            50, // Strike resist padrão
            1.5,
        )
    }

    /// Determina a intenção de combate baseado na distância
    pub fn choose_attack_intention(&self, npc_pos: &Coord, target_pos: &Coord) -> AttackIntention {
        if npc_pos.distance(target_pos) <= self.attack_range {
            AttackIntention::PhysicalAttack
        } else {
            AttackIntention::PhysicalAttack
        }
    }
}
