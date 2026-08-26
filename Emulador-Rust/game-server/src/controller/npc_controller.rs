//! Controlador de NPCs (NpcController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::creature_controller::CreatureController;
use crate::controller::movement::NpcMoveController;
use crate::engine::Coord;

pub struct NpcController {
    pub creature: CreatureController,
    pub npc_move: NpcMoveController,
    pub npc_id: u32,
    pub dialog_id: u32,
}

impl NpcController {
    pub fn new(
        object_id: u32,
        npc_id: u32,
        map_id: u32,
        position: Coord,
        heading: u8,
        speed: f32,
        max_hp: i32,
    ) -> Self {
        Self {
            creature: CreatureController::new(
                object_id,
                map_id,
                position,
                heading,
                speed,
                max_hp,
                1000,
            ),
            npc_move: NpcMoveController::new(position, heading, speed),
            npc_id,
            dialog_id: 10,
        }
    }

    pub fn on_dialog_request(&self, player_id: u32) {
        self.creature.observers.notify_dialog(player_id);
    }
}
