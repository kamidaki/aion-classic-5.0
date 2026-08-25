//! CombatService - Gerenciamento de Combate, Ataques e Ações (Padrão Java AION)

use std::collections::HashMap;
use std::time::{Duration, Instant};

use crate::game::character::Character;
use crate::game::data::ActionType;
use crate::game::entity::Entity;
use crate::game::message::{client as c, server as s};
use crate::game::{Messages, ServerUpdate};

pub struct CombatService;

impl CombatService {
    /// Processa o ataque físico regular contra um alvo
    pub fn handle_attack(
        character_id: u32,
        attack: &c::Attack,
        characters: &mut HashMap<u32, Character>,
        entities: &mut [Entity],
        attack_timers: &mut HashMap<u32, (u32, Instant)>,
        messages: &mut Messages,
    ) {
        if attack.target_id == 0 {
            attack_timers.remove(&character_id);
            return;
        }

        let Some(entity) = entities.iter_mut().find(|e| e.id() == attack.target_id && e.is_alive()) else {
            return;
        };

        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        let hit = crate::game::engine::damage::CombatEngine::calculate_physical_hit(
            character.stats.secondary.main_hand_attack,
            1.0,
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
        let is_crit = if hit.ty == crate::game::engine::damage::Type::Critical { 1 } else { 0 };
        entity.hp.update(-damage);

        let s_hit_point_other = s::HitPointOther::new(
            entity.id(),
            damage,
            entity.hp.current() as u32,
            entity.hp.max() as u32,
            0,
            is_crit,
        );

        let hits = vec![hit];
        messages.broadcast.extend(
            [
                s::Message::Attack(s::Attack::new(entity.id(), character.id(), 0, hits)),
                s::Message::HitPointOther(s_hit_point_other),
            ]
            .map(ServerUpdate::new),
        );

        if entity.is_dead() {
            attack_timers.remove(&character_id);
            messages.broadcast.extend(
                [
                    s::Message::Action(s::Action::new(
                        entity.id(),
                        ActionType::Die,
                        character.stats.move_speed,
                        character.id(),
                    )),
                    s::Message::Loot(s::Loot::new(entity.id(), 0)),
                ]
                .map(ServerUpdate::new),
            );
        } else {
            let swing_delay = Duration::from_millis(character.attack_speed_ms());
            attack_timers.insert(character_id, (attack.target_id, Instant::now() + swing_delay));
        }
    }

    /// Processa a mudança de alvo selecionado
    pub fn handle_change_target(
        change_target: &c::ChangeTarget,
        entities: &[Entity],
        messages: &mut Messages,
    ) {
        if let Some(entity) = entities.iter().find(|e| e.id() == change_target.target_id) {
            messages.broadcast.push(ServerUpdate::new(s::Message::TargetInfo(
                s::TargetInfo::new(
                    change_target.target_id,
                    entity.level(),
                    entity.hp.current(),
                    entity.hp.max(),
                ),
            )));
        }
    }

    /// Processa ações corporais e emotes (sentar, levantar, pular)
    pub fn handle_action(
        character_id: u32,
        action: &c::Action,
        characters: &mut HashMap<u32, Character>,
        messages: &mut Messages,
    ) {
        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        messages.broadcast.push(ServerUpdate::new(s::Message::Action(
            s::Action::new(character.id(), action.ty, character.stats.move_speed, 0),
        )));
    }
}
