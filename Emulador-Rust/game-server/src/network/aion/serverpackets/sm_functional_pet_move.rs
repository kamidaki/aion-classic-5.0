//! Pacote SM_FUNCTIONAL_PET_MOVE

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmFunctionalPetMove {
    pub pet_id: u32,
    pub pos: Coord,
    pub heading: u8,
}
