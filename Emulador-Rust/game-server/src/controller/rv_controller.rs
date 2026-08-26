//! Controlador de Fendas Espaciais e Vórtices (RVController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct RVController {
    pub visible: VisibleObjectController,
    pub rift_id: u32,
    pub destination_map_id: u32,
    pub destination_pos: Coord,
    pub max_entries: u32,
    pub used_entries: u32,
    pub min_level: u16,
    pub max_level: u16,
    pub is_open: bool,
}

impl RVController {
    pub fn new(
        object_id: u32,
        rift_id: u32,
        map_id: u32,
        position: Coord,
        dest_map_id: u32,
        dest_pos: Coord,
        max_entries: u32,
        min_level: u16,
        max_level: u16,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            rift_id,
            destination_map_id: dest_map_id,
            destination_pos: dest_pos,
            max_entries,
            used_entries: 0,
            min_level,
            max_level,
            is_open: true,
        }
    }

    pub fn can_use(&self, player_level: u16) -> bool {
        self.is_open
            && self.used_entries < self.max_entries
            && player_level >= self.min_level
            && player_level <= self.max_level
    }

    pub fn use_rift(&mut self, player_level: u16) -> Option<(u32, Coord)> {
        if self.can_use(player_level) {
            self.used_entries += 1;
            if self.used_entries >= self.max_entries {
                self.is_open = false;
            }
            Some((self.destination_map_id, self.destination_pos))
        } else {
            None
        }
    }
}
