//! Controlador de Monstros e Chefes (MonsterController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::npc_controller::NpcController;
use crate::engine::Coord;

pub struct MonsterController {
    pub npc: NpcController,
    pub aggro_range: f32,
    pub leash_range: f32,
    pub is_boss: bool,
    pub respawn_time_seconds: u32,
}

impl MonsterController {
    pub fn new(
        object_id: u32,
        npc_id: u32,
        map_id: u32,
        position: Coord,
        heading: u8,
        speed: f32,
        max_hp: i32,
        aggro_range: f32,
        is_boss: bool,
    ) -> Self {
        Self {
            npc: NpcController::new(
                object_id,
                npc_id,
                map_id,
                position,
                heading,
                speed,
                max_hp,
            ),
            aggro_range,
            leash_range: aggro_range * 2.5,
            is_boss,
            respawn_time_seconds: if is_boss { 3600 } else { 60 },
        }
    }

    pub fn check_leash(&mut self) -> bool {
        let current_pos = self.npc.npc_move.get_position();
        if current_pos.distance(&self.npc.npc_move.spawn_point) > self.leash_range {
            self.npc.npc_move.start_return_to_spawn();
            self.npc.creature.aggro_list.clear();
            self.npc.creature.hp = self.npc.creature.max_hp; // Reset completo de HP no leash
            true
        } else {
            false
        }
    }
}
