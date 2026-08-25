//! Cenário Scriptado de Movimento (WalkScenario - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct WalkScenario {
    pub scenario_id: u32,
    pub path_points: Vec<Coord>,
    pub current_step: usize,
}

impl WalkScenario {
    pub fn new(scenario_id: u32, path_points: Vec<Coord>) -> Self {
        Self {
            scenario_id,
            path_points,
            current_step: 0,
        }
    }

    pub fn get_next_dest(&mut self) -> Option<&Coord> {
        if self.current_step < self.path_points.len() {
            let dest = &self.path_points[self.current_step];
            self.current_step += 1;
            Some(dest)
        } else {
            None
        }
    }
}
