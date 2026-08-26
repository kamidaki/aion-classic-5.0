//! Observer Geral de Ações de Jogador e Criatura (ActionObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::observer_type::ObserverType;
use crate::engine::Coord;

pub trait ActionObserver: Send + Sync {
    fn get_observer_type(&self) -> ObserverType;

    fn on_move(&self) {}
    fn on_attack(&self) {}
    fn on_attacked(&self) {}
    fn on_die(&self) {}
    fn on_item_use(&self, _item_id: u32) {}
    fn on_dialog(&self, _target_id: u32) {}
    fn on_see(&self, _seen_id: u32) {}
    fn on_pass_ring(&self, _ring_id: u32) {}
    fn on_collision(&self, _pos: &Coord) {}
}
