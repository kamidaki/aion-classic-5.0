//! Handler de Ciclo de Decisão e Pensamento da IA (ThinkEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::ai::handler::aggro_handler::AggroEventHandler;
use crate::ai::hate_table::HateTable;
use crate::ai::state::AIState;
use crate::character::Character;
use crate::entity::Entity;

pub struct ThinkEventHandler;

impl ThinkEventHandler {
    /// Executa o ciclo de pensamento periódica da IA
    pub fn think(
        entity: &mut Entity,
        state: &mut AIState,
        hate_table: &mut HateTable,
        characters: &mut HashMap<u32, Character>,
        aggro_range: f32,
    ) {
        match state {
            AIState::Idle | AIState::Walking => {
                // Se for agressivo, procura por jogadores no raio
                for character in characters.values() {
                    if AggroEventHandler::check_see_player(
                        entity.location(),
                        aggro_range,
                        character,
                        hate_table,
                        state,
                    ) {
                        entity.set_taget(character.id());
                        break;
                    }
                }
            }
            AIState::Attacking => {
                // Verifica se o alvo principal ainda está vivo
                if let Some(target_id) = hate_table.get_highest_target() {
                    let target_alive = characters
                        .get(&target_id)
                        .map(|c| !c.to_player_state().is_dead)
                        .unwrap_or(false);

                    if !target_alive {
                        hate_table.remove_target(target_id);
                        if let Some(next_target) = hate_table.get_highest_target() {
                            entity.set_taget(next_target);
                        } else {
                            *state = AIState::Idle;
                            entity.clear_target();
                        }
                    }
                } else {
                    *state = AIState::Idle;
                    entity.clear_target();
                }
            }
            _ => {}
        }
    }
}
