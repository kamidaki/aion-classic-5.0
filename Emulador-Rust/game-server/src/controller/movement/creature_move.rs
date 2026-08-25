//! CreatureMoveController - Controle de física e coordenadas base de criaturas

#[derive(Debug, Clone)]
pub struct CreatureMoveController {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub speed: f32,
    pub is_moving: bool,
}

impl CreatureMoveController {
    pub fn new(x: f32, y: f32, z: f32, heading: u8, speed: f32) -> Self {
        Self {
            x,
            y,
            z,
            heading,
            speed,
            is_moving: false,
        }
    }

    pub fn set_position(&mut self, x: f32, y: f32, z: f32, heading: u8) {
        self.x = x;
        self.y = y;
        self.z = z;
        self.heading = heading;
    }

    pub fn distance_to(&self, tx: f32, ty: f32, tz: f32) -> f32 {
        let dx = self.x - tx;
        let dy = self.y - ty;
        let dz = self.z - tz;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
}
