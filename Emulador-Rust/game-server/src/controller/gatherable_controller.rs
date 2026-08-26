//! Controlador de Nós de Coleta e Extração (GatherableController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct GatherableController {
    pub visible: VisibleObjectController,
    pub template_id: u32,
    pub max_gather_count: u8,
    pub current_gather_count: u8,
    pub current_gatherer: Option<u32>,
    pub required_skill_level: u32,
}

impl GatherableController {
    pub fn new(
        object_id: u32,
        template_id: u32,
        map_id: u32,
        position: Coord,
        required_skill_level: u32,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            template_id,
            max_gather_count: 3,
            current_gather_count: 0,
            current_gatherer: None,
            required_skill_level,
        }
    }

    pub fn start_gathering(&mut self, player_id: u32, player_skill_level: u32) -> bool {
        if self.current_gatherer.is_some() || self.current_gather_count >= self.max_gather_count {
            return false;
        }
        if player_skill_level < self.required_skill_level {
            return false;
        }
        self.current_gatherer = Some(player_id);
        true
    }

    pub fn finish_gathering(&mut self, success: bool) -> bool {
        self.current_gatherer = None;
        if success {
            self.current_gather_count += 1;
        }
        self.is_depleted()
    }

    pub fn cancel_gathering(&mut self) {
        self.current_gatherer = None;
    }

    pub fn is_depleted(&self) -> bool {
        self.current_gather_count >= self.max_gather_count
    }
}
