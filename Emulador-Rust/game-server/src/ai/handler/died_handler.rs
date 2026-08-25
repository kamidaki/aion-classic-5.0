//! Handler de Morte da IA (DiedEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::hate_table::HateTable;
use crate::ai::state::AIState;

pub struct DiedEventHandler;

impl DiedEventHandler {
    pub fn on_died(state: &mut AIState, hate_table: &mut HateTable) {
        *state = AIState::Dead;
        hate_table.clear();
    }
}
