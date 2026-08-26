//! Controlador de Mascotes / Pets Cosméticos (PetController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::movement::PetMoveController;
use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct PetController {
    pub visible: VisibleObjectController,
    pub pet_move: PetMoveController,
    pub master_id: u32,
    pub pet_id: u32,
    pub fullness: u8,
    pub mood: u8,
}

impl PetController {
    pub fn new(
        object_id: u32,
        master_id: u32,
        pet_id: u32,
        map_id: u32,
        position: Coord,
        heading: u8,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, heading),
            pet_move: PetMoveController::new(position, heading, 6.0),
            master_id,
            pet_id,
            fullness: 100,
            mood: 100,
        }
    }

    pub fn feed(&mut self, amount: u8) {
        self.fullness = (self.fullness + amount).min(100);
    }
}
