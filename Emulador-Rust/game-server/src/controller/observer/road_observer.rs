//! Observer de Estradas e Caminhos Especiais (RoadObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone)]
pub struct RoadObserver {
    pub road_id: u32,
    pub speed_bonus: f32,
}

impl RoadObserver {
    pub fn new(road_id: u32, speed_bonus: f32) -> Self {
        Self {
            road_id,
            speed_bonus,
        }
    }
}

impl ActionObserver for RoadObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::Move
    }
}
