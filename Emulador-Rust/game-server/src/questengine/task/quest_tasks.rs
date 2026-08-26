//! Utilitários e Gerenciadores de Tarefas de Missões (QuestTasks)

use super::coordinate_destination_checker::CoordinateDestinationChecker;
use super::destination_checker::DestinationChecker;
use super::following_npc_check_task::FollowingNpcCheckTask;
use super::target_destination_checker::TargetDestinationChecker;
use super::zone_checker::ZoneChecker;
use crate::engine::Coord;

pub struct QuestTasks;

impl QuestTasks {
    pub fn new_coord_checker(pos: Coord, radius: f32) -> Box<dyn DestinationChecker> {
        Box::new(CoordinateDestinationChecker::new(pos, radius))
    }

    pub fn new_target_checker(target_obj_id: u32, target_pos: Coord, max_distance: f32) -> Box<dyn DestinationChecker> {
        Box::new(TargetDestinationChecker::new(target_obj_id, target_pos, max_distance))
    }

    pub fn new_zone_checker(zone_id: u32) -> ZoneChecker {
        ZoneChecker::new(zone_id)
    }

    pub fn new_follow_task(player_id: u32, npc_obj_id: u32, max_dist: f32) -> FollowingNpcCheckTask {
        FollowingNpcCheckTask::new(player_id, npc_obj_id, max_dist)
    }
}
