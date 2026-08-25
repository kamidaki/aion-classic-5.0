//! SkillService - Gerenciamento de Execução de Habilidades e Efeitos (Padrão Java AION)

use std::collections::HashMap;

use crate::character::Character;
use crate::data::ActionType;
use crate::entity::Entity;
use crate::message::{client as c, server as s};
use crate::{ClientUpdate, Messages, ServerUpdate};

pub struct SkillService;

impl SkillService {
    /// Processa o uso de uma habilidade por um jogador
    pub fn handle_use_skill(
        update: &ClientUpdate,
        use_skill: &c::UseSkill,
        characters: &mut HashMap<u32, Character>,
        entities: &mut [Entity],
        restrictions: &crate::restrictions::RestrictionsManager,
        messages: &mut Messages,
    ) {
        let char_id = update.character_id();
        let Some(character) = characters.get_mut(&char_id) else {
            return;
        };

        let is_self_or_aoe = use_skill.target_id == 0 || use_skill.target_id == char_id;

        // Validação estrita pelo subsistema de restrições
        let player_state = character.to_player_state();
        let skill_info = crate::restrictions::SkillInfo {
            skill_id: use_skill.skill_id as u32,
            skill_type: crate::restrictions::SkillType::Physical,
            has_evade_effect: false,
            has_resurrect_effect: false,
            is_hide_skill: false,
            is_recall_instant: false,
            is_disabled: false,
            is_enemy_target: !is_self_or_aoe,
        };

        if let Err(restriction_err) = restrictions.can_use_skill(&player_state, &skill_info) {
            println!("WARN: [SkillService] Skill {} restricted for player {}: {:?}", use_skill.skill_id, char_id, restriction_err);
            return;
        }

        if is_self_or_aoe {
            // Self-buff ou skill utilitária/área
            let eff = s::AbnormalEffect::new(use_skill.skill_id as u32, 30000, 1);
            messages.push_direct(
                update.client_id(),
                ServerUpdate::new(s::Message::AbnormalStatus(s::AbnormalStatus::with_effects(
                    char_id,
                    vec![eff.clone()],
                ))),
            );
            messages.push_others(
                update.client_id(),
                ServerUpdate::new(s::Message::AbnormalStatusOther(
                    s::AbnormalStatusOther::with_effects(char_id, vec![eff]),
                )),
            );
            messages.push_direct(
                update.client_id(),
                ServerUpdate::new(s::Message::SkillPenaltyStatusOther(
                    s::SkillPenaltyStatusOther::new(char_id, use_skill.skill_id as u32, 5000),
                )),
            );
            let skill_effect = s::SkillEffect::new(char_id, 0, 1, 0);
            messages.push_direct(
                update.client_id(),
                ServerUpdate::new(s::Message::SkillSucceded(s::SkillSucceded::new(
                    char_id,
                    char_id,
                    use_skill.skill_id as u32,
                    use_skill.skill_level as u8,
                    vec![skill_effect],
                ))),
            );
        } else if let Some(entity) = entities
            .iter_mut()
            .find(|e| e.id() == use_skill.target_id && e.is_alive())
        {
            let hit = crate::engine::damage::CombatEngine::calculate_physical_hit(
                character.stats.secondary.main_hand_attack,
                1.5,
                100,
                character.stats.secondary.main_hand_accuracy,
                100,
                100,
                100,
                character.stats.secondary.main_hand_crit,
                50,
                1.5,
            );
            let damage = hit.damage.max(1);
            let is_crit = if hit.ty == crate::engine::damage::Type::Critical { 1 } else { 0 };
            entity.hp.update(-damage);

            let eff = s::SkillEffect::new(entity.id(), -damage, 0, is_crit);
            messages.broadcast.extend(
                [
                    s::Message::UseSkill(s::UseSkill::new(
                        char_id,
                        use_skill.skill_id,
                        use_skill.skill_level,
                        use_skill.target_id,
                    )),
                    s::Message::SkillSucceded(s::SkillSucceded::new(
                        char_id,
                        use_skill.target_id,
                        use_skill.skill_id as u32,
                        use_skill.skill_level as u8,
                        vec![eff],
                    )),
                    s::Message::SkillPenaltyStatusOther(s::SkillPenaltyStatusOther::new(
                        char_id,
                        use_skill.skill_id as u32,
                        3000,
                    )),
                    s::Message::HitPointOther(s::HitPointOther::new(
                        entity.id(),
                        damage,
                        entity.hp.current() as u32,
                        entity.hp.max() as u32,
                        0,
                        is_crit,
                    )),
                ]
                .map(ServerUpdate::new),
            );

            if entity.is_dead() {
                messages.broadcast.extend(
                    [
                        s::Message::Action(s::Action::new(
                            entity.id(),
                            ActionType::Die,
                            character.stats.move_speed,
                            char_id,
                        )),
                        s::Message::Loot(s::Loot::new(entity.id(), 0)),
                    ]
                    .map(ServerUpdate::new),
                );
            }
        }
    }
}
