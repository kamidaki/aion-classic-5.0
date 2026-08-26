//! Modelos de Rotas de Voo e Anéis de Voo (FlyPathEntry / FlyRing - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct FlyPathEntryModel {
    pub path_id: u32,
    pub start_pos: Coord,
    pub end_pos: Coord,
    pub cost_kinah: u32,
    pub duration_seconds: u32,
}

#[derive(Debug, Clone)]
pub struct FlyRingModel {
    pub name: String,
    pub center_pos: Coord,
    pub radius: f32,
}
