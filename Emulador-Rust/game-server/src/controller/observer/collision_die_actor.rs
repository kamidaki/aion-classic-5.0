//! Ator de Morte por Queda ou Colisão com Chão Fatal (CollisionDieActor - Padrão Java Aion Classic 2.8 / 4.5)

use super::iactor::IActor;
use crate::engine::Coord;

#[derive(Debug, Clone, Default)]
pub struct CollisionDieActor;

impl IActor for CollisionDieActor {
    fn act(&self, player_id: u32, position: &Coord) {
        println!("[COLLISION_DIE] Jogador #{} colidiu mortalmente em {:?}", player_id, position);
    }
}
