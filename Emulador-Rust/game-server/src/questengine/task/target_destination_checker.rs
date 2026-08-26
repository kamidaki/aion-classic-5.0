//! Verificador de Proximidade a um Alvo/NPC (TargetDestinationChecker)

use super::destination_checker::DestinationChecker;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct TargetDestinationChecker {
    pub target_obj_id: u32,
    pub target_pos: Coord,
    pub max_distance: f32,
}

impl TargetDestinationChecker {
    pub fn new(target_obj_id: u32, target_pos: Coord, max_distance: f32) -> Self {
        Self {
            target_obj_id,
            target_pos,
            max_distance,
        }
    }
}

impl DestinationChecker for TargetDestinationChecker {
    fn check(&self, current_pos: &Coord) -> bool {
        self.target_pos.distance(current_pos) <= self.max_distance
    }
}
