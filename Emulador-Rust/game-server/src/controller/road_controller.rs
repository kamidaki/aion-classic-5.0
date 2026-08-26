//! Controlador de Estradas e Rotas de Velocidade (RoadController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct RoadController {
    pub visible: VisibleObjectController,
    pub road_id: u32,
    pub speed_bonus: f32,
    pub radius: f32,
}

impl RoadController {
    pub fn new(
        object_id: u32,
        road_id: u32,
        map_id: u32,
        position: Coord,
        radius: f32,
        speed_bonus: f32,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            road_id,
            speed_bonus,
            radius,
        }
    }

    pub fn is_in_road(&self, player_pos: &Coord) -> bool {
        self.visible.position.distance(player_pos) <= self.radius
    }
}
