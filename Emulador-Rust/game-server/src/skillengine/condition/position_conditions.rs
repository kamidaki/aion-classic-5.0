//! Condições Posicionais e de Voo (Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::condition::condition::SkillCondition;
use crate::skillengine::model::skill_template::SkillTemplate;

/// Condição de Ataque pelas Costas (Back Attack / BackCondition - ex: Assassin Backstab)
#[derive(Debug, Clone)]
pub struct BackCondition;

impl SkillCondition for BackCondition {
    fn validate(
        &self,
        caster: &Character,
        target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        let Some(t) = target else {
            return Err("Alvo inválido para ataque posicional");
        };

        // Validação de proximidade angular em relação ao alvo
        let caster_pos = caster.location();
        let target_pos = t.location();
        let dist = caster_pos.distance(target_pos);
        if dist > 5.0 {
            return Err("Alvo fora de alcance para golpe pelas costas");
        }
        Ok(())
    }
}

/// Condição de Ataque Frontal (FrontCondition)
#[derive(Debug, Clone)]
pub struct FrontCondition;

impl SkillCondition for FrontCondition {
    fn validate(
        &self,
        caster: &Character,
        target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        let Some(t) = target else {
            return Err("Alvo inválido");
        };
        let dist = caster.location().distance(t.location());
        if dist > 5.0 {
            return Err("Alvo fora de alcance frontal");
        }
        Ok(())
    }
}

/// Condição de Proibição de Voo (NoFlyingCondition - Skills terrestres apenas)
#[derive(Debug, Clone)]
pub struct NoFlyingCondition;

impl SkillCondition for NoFlyingCondition {
    fn validate(
        &self,
        caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        let state = caster.to_player_state();
        if state.mode == crate::restrictions::PlayerMode::Flying
            || state.mode == crate::restrictions::PlayerMode::Gliding
        {
            return Err("Esta habilidade não pode ser utilizada em voo");
        }
        Ok(())
    }
}

/// Condição de Voo Obrigatório (OnFlyingCondition)
#[derive(Debug, Clone)]
pub struct OnFlyingCondition;

impl SkillCondition for OnFlyingCondition {
    fn validate(
        &self,
        caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        let state = caster.to_player_state();
        if state.mode != crate::restrictions::PlayerMode::Flying
            && state.mode != crate::restrictions::PlayerMode::Gliding
        {
            return Err("Esta habilidade requer que você esteja voando");
        }
        Ok(())
    }
}
