//! Handler de Retorno à Posição Original / Leash (ReturningEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::hate_table::HateTable;
use crate::ai::state::AIState;
use crate::engine::Coord;
use crate::entity::Entity;

pub struct ReturningEventHandler;

impl ReturningEventHandler {
    /// Verifica se a entidade ultrapassou a distância máxima de perseguição (leash range)
    pub fn check_leash(
        current_pos: &Coord,
        spawn_pos: &Coord,
        leash_range: f32,
    ) -> bool {
        current_pos.distance(spawn_pos) > leash_range
    }

    /// Reseta o monstro, limpa o hate, regenera o HP para 100% e inicia o retorno
    pub fn on_return(
        entity: &mut Entity,
        state: &mut AIState,
        hate_table: &mut HateTable,
    ) {
        *state = AIState::Returning;
        hate_table.clear();
        entity.clear_target();

        // Cura 100% do HP ao resetar
        let max_hp = entity.max_hp;
        entity.hp.update(max_hp);
    }

    /// Finaliza o retorno quando alcança a coordenada original de spawn
    pub fn on_arrive_home(state: &mut AIState) {
        *state = AIState::Idle;
    }
}
