//! Condição de Cadeia de Habilidade (ChainCondition - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;
use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::condition::condition::SkillCondition;
use crate::skillengine::model::chain_skills::ActiveChainState;
use crate::skillengine::model::skill_template::SkillTemplate;

#[derive(Debug, Clone)]
pub struct ChainCondition {
    pub pre_skill_id: u32,
}

impl ChainCondition {
    pub fn new(pre_skill_id: u32) -> Self {
        Self { pre_skill_id }
    }

    /// Valida se o jogador tem a corrente ativa não expirada
    pub fn validate_chain(
        &self,
        active_chain: Option<&ActiveChainState>,
        skill_id: u32,
        now: Instant,
    ) -> Result<(), &'static str> {
        let Some(chain) = active_chain else {
            return Err("A habilidade anterior da corrente não foi utilizada");
        };

        if chain.next_skill_id != skill_id {
            return Err("Esta habilidade não corresponde à corrente atual");
        }

        if now > chain.expires_at {
            return Err("A janela de tempo da corrente expirou");
        }

        Ok(())
    }
}

impl SkillCondition for ChainCondition {
    fn validate(
        &self,
        _caster: &Character,
        _target: Option<&Entity>,
        _template: &SkillTemplate,
    ) -> Result<(), &'static str> {
        Ok(())
    }
}
