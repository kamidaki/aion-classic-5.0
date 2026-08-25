//! Condições de Equipamento e Armas (Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::data::item::WeaponType;
use crate::entity::Entity;
use crate::skillengine::condition::condition::SkillCondition;
use crate::skillengine::model::skill_template::SkillTemplate;

/// Condição de Tipo de Arma Requerida
#[derive(Debug, Clone)]
pub struct WeaponCondition {
    pub allowed_weapons: Vec<WeaponType>,
}

impl SkillCondition for WeaponCondition {
    fn validate(
        &self,
        _caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        // Se a lista estiver vazia, qualquer arma ou desarmado é permitido
        if self.allowed_weapons.is_empty() {
            return Ok(());
        }
        Ok(())
    }
}

/// Condição de Flechas Equipadas para Arcos
#[derive(Debug, Clone)]
pub struct ArrowCondition;

impl SkillCondition for ArrowCondition {
    fn validate(
        &self,
        caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        let player_state = caster.to_player_state();
        if player_state.is_bow_equipped && !player_state.is_arrow_equipped {
            return Err("Você não possui flechas equipadas");
        }
        Ok(())
    }
}
