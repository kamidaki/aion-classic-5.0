//! Fendas Espaciais (Rift - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct Rift {
    pub id: u32,
    pub origin_map: u32,
    pub dest_map: u32,
    pub origin_pos: Coord,
    pub dest_pos: Coord,
    pub min_level: u16,
    pub max_level: u16,
    pub max_uses: u32,
    pub current_uses: u32,
    pub is_active: bool,
}

impl Rift {
    pub fn new(
        id: u32,
        origin_map: u32,
        dest_map: u32,
        origin_pos: Coord,
        dest_pos: Coord,
        min_level: u16,
        max_level: u16,
        max_uses: u32,
    ) -> Self {
        Self {
            id,
            origin_map,
            dest_map,
            origin_pos,
            dest_pos,
            min_level,
            max_level,
            max_uses,
            current_uses: 0,
            is_active: true,
        }
    }

    pub fn try_teleport(&mut self, player_level: u16) -> Option<Coord> {
        if !self.is_active || self.current_uses >= self.max_uses {
            return None;
        }

        if player_level >= self.min_level && player_level <= self.max_level {
            self.current_uses += 1;
            if self.current_uses >= self.max_uses {
                self.is_active = false;
            }
            Some(self.dest_pos)
        } else {
            None
        }
    }
}
