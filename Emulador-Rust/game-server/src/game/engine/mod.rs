use crate::consume_le_bytes;

pub mod damage;

#[derive(Debug, Clone, Copy)]
pub struct Coord {
    x: f32,
    y: f32,
    z: f32,
}

impl Coord {
    pub const LEN: usize = 12;

    pub fn new(x: f32, y: f32, z: f32) -> Self {
        Self { x, y, z }
    }

    pub fn x(&self) -> f32 {
        self.x
    }

    pub fn y(&self) -> f32 {
        self.y
    }

    pub fn z(&self) -> f32 {
        self.z
    }

    pub fn serialise(&self, buf: &mut [u8]) -> usize {
        assert!(buf.len() >= Self::LEN);
        buf[..4].copy_from_slice(&self.x.to_le_bytes());
        buf[4..8].copy_from_slice(&self.y.to_le_bytes());
        buf[8..12].copy_from_slice(&self.z.to_le_bytes());

        Self::LEN
    }

    pub fn deserialise(buf: &[u8; Self::LEN]) -> Self {
        let mut _len = 0;
        Self {
            x: consume_le_bytes!(_len, buf, f32),
            y: consume_le_bytes!(_len, buf, f32),
            z: consume_le_bytes!(_len, buf, f32),
        }
    }

    pub fn distance(&self, location: &Coord) -> f32 {
        let dx = self.x - location.x;
        let dy = self.y - location.y;
        let dz = self.z - location.z;
        let distance = (dx * dx + dy * dy + dz * dz).sqrt();
        distance
    }
}

impl std::ops::Add for &Coord {
    type Output = Coord;

    fn add(self, rhs: Self) -> Self::Output {
        Self::Output {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
            z: self.z + rhs.z,
        }
    }
}

/// When an entity moves these bits are set to tell the game about
/// the type of movement
#[derive(Debug, Clone, Copy)]
#[repr(transparent)]
pub struct MoveType(u8);

impl MoveType {
    pub const STOP: MoveType = MoveType(0x00);
    pub const FALL: MoveType = MoveType(0x08);
    pub const GLIDE: MoveType = MoveType(0x04);
    pub const CONTINUE: MoveType = MoveType(0x80);
    pub const TURN: MoveType = MoveType(0x40);
    /// Mouse click to move mostly
    pub const DIRECT: MoveType = MoveType(0x20);

    pub const NPC_DIRECT: MoveType = MoveType(0xE0);
    pub const NPC_RUN_FAST: MoveType = MoveType(0xE2);
    pub const NPC_WALK_SLOW: MoveType = MoveType(0xE4);

    pub const fn from_bits(bits: u8) -> Self {
        MoveType(bits)
    }

    pub const fn bits(self) -> u8 {
        self.0
    }

    #[inline(always)]
    pub fn contains(self, other: MoveType) -> bool {
        (self.0 & other.0) == other.0
    }
}

impl From<u8> for MoveType {
    fn from(value: u8) -> Self {
        MoveType::from_bits(value)
    }
}

/// The direct a character is moving 0x00 represents south
/// The range is 0x00 - 0x77 (0 - 119) (mod 120)
#[derive(Debug, Clone, Copy)]
pub struct Direction(u8);

impl Direction {
    const MODULUS: u8 = 120;

    pub fn new(direction: u8) -> Self {
        Self(direction % Self::MODULUS)
    }

    pub fn bits(&self) -> u8 {
        self.0
    }
}

/// Interface da GeoEngine para consultas de terreno, colisão 3D e linha de visão (LoS).
pub trait GeoService: Send + Sync {
    /// Retorna a altura Z estimada ou exata do terreno no mapa
    fn get_z(&self, world_id: u32, x: f32, y: f32) -> f32;

    /// Verifica se há linha de visão desobstruída (Raycast)
    fn can_see(&self, world_id: u32, from: &Coord, to: &Coord) -> bool;

    /// Valida se uma posição está em zona de voo autorizada
    fn is_fly_zone(&self, world_id: u32, pos: &Coord) -> bool;

    /// Valida se a velocidade de deslocamento do jogador é legítima
    fn validate_speed(&self, from: &Coord, to: &Coord, dt_seconds: f32, max_speed: f32) -> bool {
        if dt_seconds <= 0.0 {
            return true;
        }
        let dist = from.distance(to);
        dist / dt_seconds <= max_speed * 1.3
    }
}

/// Implementação padrão resiliente da GeoEngine
#[derive(Debug, Default, Clone)]
pub struct DefaultGeoEngine;

impl GeoService for DefaultGeoEngine {
    fn get_z(&self, _world_id: u32, _x: f32, _y: f32) -> f32 {
        0.0
    }

    fn can_see(&self, _world_id: u32, _from: &Coord, _to: &Coord) -> bool {
        true
    }

    fn is_fly_zone(&self, world_id: u32, _pos: &Coord) -> bool {
        // Reshanta (400010000) e certas zonas de capitais permitem voo livre
        matches!(world_id, 400_010_000 | 110_010_000 | 120_010_000)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coord_distance_and_add_work_properly() {
        let a = Coord::new(0.0, 0.0, 0.0);
        let b = Coord::new(3.0, 4.0, 0.0);
        assert_eq!(a.distance(&b), 5.0);

        let c = &a + &b;
        assert_eq!(c.x(), 3.0);
        assert_eq!(c.y(), 4.0);
        assert_eq!(c.z(), 0.0);
    }

    #[test]
    fn move_type_bit_mask_detection() {
        let mt = MoveType::from_bits(MoveType::GLIDE.bits() | MoveType::TURN.bits());
        assert!(mt.contains(MoveType::GLIDE));
        assert!(mt.contains(MoveType::TURN));
        assert!(!mt.contains(MoveType::FALL));
    }

    #[test]
    fn geo_engine_validates_speed_and_fly_zones() {
        let geo = DefaultGeoEngine;
        let p1 = Coord::new(100.0, 100.0, 200.0);
        let p2 = Coord::new(106.0, 100.0, 200.0); // 6m em 1s = 6m/s

        assert!(geo.validate_speed(&p1, &p2, 1.0, 6.0));
        assert!(!geo.validate_speed(&p1, &p2, 0.1, 6.0), "60m/s deve ser rejeitado por speedhack");

        assert!(geo.is_fly_zone(400_010_000, &p1), "Reshanta e zona de voo");
        assert!(!geo.is_fly_zone(210_010_000, &p1), "Poeta padrao nao e zona de voo livre");
    }
}
