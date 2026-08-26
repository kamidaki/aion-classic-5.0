//! Observer de Colisão com Terreno e Malhas Tridimensionais (AbstractCollisionObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::iactor::IActor;
use super::observer_type::ObserverType;
use crate::engine::Coord;
use std::sync::Arc;

pub struct AbstractCollisionObserver {
    pub actor: Arc<dyn IActor>,
    pub player_id: u32,
}

impl AbstractCollisionObserver {
    pub fn new(player_id: u32, actor: Arc<dyn IActor>) -> Self {
        Self { actor, player_id }
    }
}

impl ActionObserver for AbstractCollisionObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Collision
    }

    fn on_collision(&self, pos: &Coord) {
        self.actor.act(self.player_id, pos);
    }
}
