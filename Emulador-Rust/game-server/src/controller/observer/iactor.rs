//! Interface Base para Atores de Colisão e Gatilhos (IActor - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

pub trait IActor: Send + Sync {
    fn act(&self, player_id: u32, position: &Coord);
}
