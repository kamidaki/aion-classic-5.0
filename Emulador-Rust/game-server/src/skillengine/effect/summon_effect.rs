//! Efeitos de Invocação (Summon, Trap, Servant, Totem, Kisk - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::engine::Coord;
use crate::entity::Entity;
use crate::skillengine::effect::effect_trait::EffectTrait;
use crate::skillengine::model::effect_model::Effect;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SummonType {
    Spirit,
    Servant,
    Totem,
    Trap,
    Kisk,
}

/// Efeito de Invocação de Entidades Aliadas ou Armadilhas
#[derive(Debug, Clone)]
pub struct SummonEffect {
    pub npc_id: u32,
    pub summon_type: SummonType,
    pub duration_ms: u32,
}

impl SummonEffect {
    pub fn new(npc_id: u32, summon_type: SummonType, duration_ms: u32) -> Self {
        Self {
            npc_id,
            summon_type,
            duration_ms,
        }
    }

    /// Spawna a entidade invocada na coordenada do conjurador
    pub fn spawn_summoned_entity(&self, caster_id: u32, location: Coord, entity_id: u32) -> Entity {
        let mut entity = Entity::novo(entity_id, location, self.npc_id, self.npc_id);
        entity.set_level(50);
        entity
    }
}

impl EffectTrait for SummonEffect {
    fn apply_to_entity(&self, _effect: &mut Effect, _target: &mut Entity) {}
    fn apply_to_player(&self, _effect: &mut Effect, _target: &mut Character) {}
    fn on_tick_entity(&self, _effect: &Effect, _target: &mut Entity) {}
    fn on_tick_player(&self, _effect: &Effect, _target: &mut Character) {}
    fn end_on_player(&self, _effect: &Effect, _target: &mut Character) {}
}
