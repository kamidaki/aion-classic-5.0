//! NpcController - Gerenciador de NPCs interativos (lojas, diálogos, teleporters)

use super::creature::CreatureController;

#[derive(Debug, Clone)]
pub struct NpcController {
    pub creature: CreatureController,
    pub npc_template_id: u32,
    pub is_shop: bool,
    pub is_quest_giver: bool,
    pub is_teleporter: bool,
}

impl NpcController {
    pub fn new(npc_obj_id: u32, npc_template_id: u32, max_hp: i32, is_shop: bool, is_quest_giver: bool, is_teleporter: bool) -> Self {
        Self {
            creature: CreatureController::new(npc_obj_id, max_hp, 1000),
            npc_template_id,
            is_shop,
            is_quest_giver,
            is_teleporter,
        }
    }

    pub fn can_interact(&self, player_x: f32, player_y: f32, npc_x: f32, npc_y: f32) -> bool {
        let dx = player_x - npc_x;
        let dy = player_y - npc_y;
        let dist_sq = dx * dx + dy * dy;
        dist_sq <= 36.0 // Max 6 metros
    }
}
