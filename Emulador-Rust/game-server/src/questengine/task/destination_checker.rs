//! Trait de Verificação de Destino em Missões de Escolta e Chegada (DestinationChecker)

use crate::engine::Coord;

pub trait DestinationChecker: Send + Sync {
    fn check(&self, current_pos: &Coord) -> bool;
}
