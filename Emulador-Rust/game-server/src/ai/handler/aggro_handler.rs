//! Handler de Detecção de Ameaça e Agressividade (AggroEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::hate_table::HateTable;
use crate::ai::state::AIState;
use crate::character::Character;
use crate::engine::Coord;

pub struct AggroEventHandler;

impl AggroEventHandler {
    /// Verifica se o monstro agressivo avista um jogador próximo dentro do raio de aggro
    pub fn check_see_player(
        npc_pos: &Coord,
        aggro_range: f32,
        player: &Character,
        hate_table: &mut HateTable,
        state: &mut AIState,
    ) -> bool {
        let player_state = player.to_player_state();
        if player_state.is_dead || player_state.is_protection_active {
            return false;
        }

        let dist = npc_pos.distance(player.location());
        if dist <= aggro_range {
            hate_table.add_damage_hate(player.id(), 1);
            *state = AIState::Attacking;
            return true;
        }

        false
    }

    /// Processa aggro por ter recebido ataque de um atacante
    pub fn on_attacked(
        attacker_id: u32,
        damage: i32,
        hate_table: &mut HateTable,
        state: &mut AIState,
    ) {
        hate_table.add_damage_hate(attacker_id, damage.max(1));
        if *state != AIState::Attacking {
            *state = AIState::Attacking;
        }
    }
}
