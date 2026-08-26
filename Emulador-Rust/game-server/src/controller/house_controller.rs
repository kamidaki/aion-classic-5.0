//! Controlador de Casas e Habitações (HouseController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum HouseAccessLevel {
    #[default]
    Everyone,
    Friends,
    Legion,
    OwnerOnly,
}

pub struct HouseController {
    pub visible: VisibleObjectController,
    pub address: u32,
    pub owner_id: Option<u32>,
    pub access_level: HouseAccessLevel,
    pub maintenance_paid_until: u64,
}

impl HouseController {
    pub fn new(object_id: u32, address: u32, map_id: u32, position: Coord) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            address,
            owner_id: None,
            access_level: HouseAccessLevel::Everyone,
            maintenance_paid_until: 0,
        }
    }

    pub fn assign_owner(&mut self, owner_id: u32, paid_until: u64) {
        self.owner_id = Some(owner_id);
        self.maintenance_paid_until = paid_until;
    }

    pub fn can_enter(&self, player_id: u32, is_friend: bool, is_legion_member: bool) -> bool {
        if let Some(owner) = self.owner_id {
            if owner == player_id {
                return true;
            }
            match self.access_level {
                HouseAccessLevel::Everyone => true,
                HouseAccessLevel::Friends => is_friend,
                HouseAccessLevel::Legion => is_legion_member,
                HouseAccessLevel::OwnerOnly => false,
            }
        } else {
            true
        }
    }
}
