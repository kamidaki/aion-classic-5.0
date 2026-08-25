//! TrapController - Gerenciador de armadilhas (Ranger/Gunslinger)

#[derive(Debug, Clone)]
pub struct TrapController {
    pub trap_id: u32,
    pub owner_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub trigger_radius: f32,
    pub skill_id: u16,
    pub is_triggered: bool,
}

impl TrapController {
    pub fn new(trap_id: u32, owner_id: u32, x: f32, y: f32, z: f32, radius: f32, skill_id: u16) -> Self {
        Self {
            trap_id,
            owner_id,
            x,
            y,
            z,
            trigger_radius: radius,
            skill_id,
            is_triggered: false,
        }
    }

    pub fn check_trigger(&mut self, entity_id: u32, ex: f32, ey: f32, ez: f32) -> Option<u16> {
        if self.is_triggered || entity_id == self.owner_id {
            return None;
        }
        let dx = self.x - ex;
        let dy = self.y - ey;
        let dz = self.z - ez;
        let dist = (dx * dx + dy * dy + dz * dz).sqrt();
        if dist <= self.trigger_radius {
            self.is_triggered = true;
            Some(self.skill_id)
        } else {
            None
        }
    }
}
