//! Trait Base para Efeitos do SkillEngine (Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::model::effect_model::Effect;

pub trait EffectTrait: Send + Sync {
    /// Aplicação inicial do efeito no alvo
    fn apply_to_entity(&self, effect: &mut Effect, target: &mut Entity);
    fn apply_to_player(&self, effect: &mut Effect, target: &mut Character);

    /// Processamento de tick periódico (DoT / HoT)
    fn on_tick_entity(&self, effect: &Effect, target: &mut Entity);
    fn on_tick_player(&self, effect: &Effect, target: &mut Character);

    /// Limpeza ao expirar ou ser removido
    fn end_on_player(&self, effect: &Effect, target: &mut Character);
}
