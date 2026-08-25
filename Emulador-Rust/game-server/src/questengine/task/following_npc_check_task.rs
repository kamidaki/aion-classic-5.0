//! Tarefa Periódica de Acompanhamento de Escolta de NPC (FollowingNpcCheckTask)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct FollowingNpcCheckTask {
    pub player_id: u32,
    pub npc_obj_id: u32,
    pub max_follow_distance: f32,
}

impl FollowingNpcCheckTask {
    pub fn new(player_id: u32, npc_obj_id: u32, max_follow_distance: f32) -> Self {
        Self {
            player_id,
            npc_obj_id,
            max_follow_distance,
        }
    }

    pub fn is_following_within_range(&self, player_pos: &Coord, npc_pos: &Coord) -> bool {
        player_pos.distance(npc_pos) <= self.max_follow_distance
    }
}
