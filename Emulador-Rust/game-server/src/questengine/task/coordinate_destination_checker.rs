//! Verificador de Destino por Coordenadas e Raio (CoordinateDestinationChecker)

use super::destination_checker::DestinationChecker;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct CoordinateDestinationChecker {
    pub target_pos: Coord,
    pub radius: f32,
}

impl CoordinateDestinationChecker {
    pub fn new(target_pos: Coord, radius: f32) -> Self {
        Self { target_pos, radius }
    }
}

impl DestinationChecker for CoordinateDestinationChecker {
    fn check(&self, current_pos: &Coord) -> bool {
        self.target_pos.distance(current_pos) <= self.radius
    }
}
