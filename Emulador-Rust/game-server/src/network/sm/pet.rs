//! Pacotes do Servidor para Mascotes e Evocações (SM_PET_* - Padrão Classic 4.5)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmAddPet {
    pub pet_id: u32,
    pub pet_template_id: u32,
    pub name: String,
}

#[derive(Debug, Clone)]
pub struct SmRemovePet {
    pub pet_id: u32,
}

#[derive(Debug, Clone)]
pub struct SmFunctionalPetMove {
    pub pet_id: u32,
    pub pos: Coord,
    pub heading: u8,
}
