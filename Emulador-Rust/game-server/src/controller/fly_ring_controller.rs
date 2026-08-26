//! Controlador de Anéis de Voo no Ar (FlyRingController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct FlyRingController {
    pub visible: VisibleObjectController,
    pub ring_id: u32,
    pub radius: f32,
    pub boost_speed: f32,
}

impl FlyRingController {
    pub fn new(
        object_id: u32,
        ring_id: u32,
        map_id: u32,
        position: Coord,
        radius: f32,
        boost_speed: f32,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            ring_id,
            radius,
            boost_speed,
        }
    }

    pub fn check_pass_ring(&self, player_pos: &Coord) -> bool {
        self.visible.position.distance(player_pos) <= self.radius
    }
}
