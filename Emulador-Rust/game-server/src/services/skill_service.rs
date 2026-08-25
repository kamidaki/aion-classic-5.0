//! SkillService - Gerenciamento e Roteamento de Execução de Habilidades (Padrão Java AION Classic 2.8 / 4.5)

use std::collections::HashMap;

use crate::character::Character;
use crate::entity::Entity;
use crate::message::client as c;
use crate::{ClientUpdate, Messages};

pub struct SkillService;

impl SkillService {
    /// Processa o uso de uma habilidade por um jogador delegando para o SkillEngine
    pub fn handle_use_skill(
        update: &ClientUpdate,
        use_skill: &c::UseSkill,
        characters: &mut HashMap<u32, Character>,
        entities: &mut [Entity],
        restrictions: &crate::restrictions::RestrictionsManager,
        skill_engine: &mut crate::skillengine::SkillEngine,
        messages: &mut Messages,
    ) {
        let char_id = update.character_id();
        let client_id = update.client_id();

        if let Err(err) = skill_engine.handle_use_skill(
            char_id,
            client_id,
            use_skill,
            characters,
            entities,
            restrictions,
            messages,
        ) {
            println!(
                "WARN: [SkillService] Falha ao executar skill {}: {}",
                use_skill.skill_id, err
            );
        }
    }
}
