//! Condições de Atributos Vitais (HP, MP, DP - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::condition::condition::SkillCondition;
use crate::skillengine::model::skill_template::SkillTemplate;

/// Condição de Pontos de Vida (HP)
#[derive(Debug, Clone)]
pub struct HpCondition {
    pub min_hp_percent: u8,
    pub max_hp_percent: u8,
}

impl SkillCondition for HpCondition {
    fn validate(
        &self,
        caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        let hp_pct = caster.stats.hp.percent();
        if hp_pct < self.min_hp_percent {
            return Err("HP insuficiente para conjurar");
        }
        if hp_pct > self.max_hp_percent {
            return Err("HP acima do limite para esta habilidade");
        }
        Ok(())
    }
}

/// Condição de Mana (MP)
#[derive(Debug, Clone)]
pub struct MpCondition {
    pub required_mp: u32,
}

impl SkillCondition for MpCondition {
    fn validate(
        &self,
        caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        if caster.stats.mp.current() < self.required_mp {
            return Err("MP insuficiente");
        }
        Ok(())
    }
}

/// Condição de Pontos Divinos (DP)
#[derive(Debug, Clone)]
pub struct DpCondition {
    pub required_dp: u32,
}

impl SkillCondition for DpCondition {
    fn validate(
        &self,
        caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        if (caster.stats.dp.current() as u32) < self.required_dp {
            return Err("DP insuficiente");
        }
        Ok(())
    }
}
