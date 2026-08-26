//! Controlador de Armadilhas e Minas (TrapController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct TrapController {
    pub visible: VisibleObjectController,
    pub creator_id: u32,
    pub skill_id: u32,
    pub trigger_radius: f32,
    pub damage: i32,
    pub is_triggered: bool,
}

impl TrapController {
    pub fn new(
        object_id: u32,
        creator_id: u32,
        skill_id: u32,
        map_id: u32,
        position: Coord,
        trigger_radius: f32,
        damage: i32,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            creator_id,
            skill_id,
            trigger_radius,
            damage,
            is_triggered: false,
        }
    }

    pub fn check_trigger(&mut self, target_pos: &Coord) -> Option<i32> {
        if !self.is_triggered && self.visible.position.distance(target_pos) <= self.trigger_radius {
            self.is_triggered = true;
            Some(self.damage)
        } else {
            None
        }
    }
}
