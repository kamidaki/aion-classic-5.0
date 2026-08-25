use crate::consume_le_bytes;

pub mod damage;

#[derive(Debug, Clone, Copy, PartialEq)]
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

/// Triângulo 3D para colisão e malhas de terreno
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Triangle3D {
    pub v0: Coord,
    pub v1: Coord,
    pub v2: Coord,
}

impl Triangle3D {
    pub fn new(v0: Coord, v1: Coord, v2: Coord) -> Self {
        Self { v0, v1, v2 }
    }

    /// Calcula a altura Z exata sobre o triângulo usando Interpolação Baricêntrica
    pub fn calculate_z(&self, x: f32, y: f32) -> Option<f32> {
        let det = (self.v1.y - self.v2.y) * (self.v0.x - self.v2.x)
            + (self.v2.x - self.v1.x) * (self.v0.y - self.v2.y);
        if det.abs() < 1e-6 {
            return None;
        }
        let l0 = ((self.v1.y - self.v2.y) * (x - self.v2.x)
            + (self.v2.x - self.v1.x) * (y - self.v2.y))
            / det;
        let l1 = ((self.v2.y - self.v0.y) * (x - self.v2.x)
            + (self.v0.x - self.v2.x) * (y - self.v2.y))
            / det;
        let l2 = 1.0 - l0 - l1;

        if l0 >= -1e-4 && l1 >= -1e-4 && l2 >= -1e-4 {
            Some(l0 * self.v0.z + l1 * self.v1.z + l2 * self.v2.z)
        } else {
            None
        }
    }
}

/// Raio 3D para cálculo de Linha de Visão (LoS)
#[derive(Debug, Clone, Copy)]
pub struct Ray3D {
    pub origin: Coord,
    pub direction: Coord,
}

impl Ray3D {
    pub fn new(origin: Coord, target: Coord) -> Self {
        let dx = target.x - origin.x;
        let dy = target.y - origin.y;
        let dz = target.z - origin.z;
        let len = (dx * dx + dy * dy + dz * dz).sqrt().max(1e-6);
        Self {
            origin,
            direction: Coord::new(dx / len, dy / len, dz / len),
        }
    }

    /// Teste de interseção Raio-Triângulo usando Algoritmo Möller–Trumbore
    pub fn intersects_triangle(&self, tri: &Triangle3D) -> Option<f32> {
        let edge1 = Coord::new(
            tri.v1.x - tri.v0.x,
            tri.v1.y - tri.v0.y,
            tri.v1.z - tri.v0.z,
        );
        let edge2 = Coord::new(
            tri.v2.x - tri.v0.x,
            tri.v2.y - tri.v0.y,
            tri.v2.z - tri.v0.z,
        );

        let h = Coord::new(
            self.direction.y * edge2.z - self.direction.z * edge2.y,
            self.direction.z * edge2.x - self.direction.x * edge2.z,
            self.direction.x * edge2.y - self.direction.y * edge2.x,
        );

        let a = edge1.x * h.x + edge1.y * h.y + edge1.z * h.z;
        if a.abs() < 1e-6 {
            return None;
        }

        let f = 1.0 / a;
        let s = Coord::new(
            self.origin.x - tri.v0.x,
            self.origin.y - tri.v0.y,
            self.origin.z - tri.v0.z,
        );

        let u = f * (s.x * h.x + s.y * h.y + s.z * h.z);
        if !(0.0..=1.0).contains(&u) {
            return None;
        }

        let q = Coord::new(
            s.y * edge1.z - s.z * edge1.y,
            s.z * edge1.x - s.x * edge1.z,
            s.x * edge1.y - s.y * edge1.x,
        );

        let v = f * (self.direction.x * q.x + self.direction.y * q.y + self.direction.z * q.z);
        if v < 0.0 || u + v > 1.0 {
            return None;
        }

        let t = f * (edge2.x * q.x + edge2.y * q.y + edge2.z * q.z);
        if t > 1e-6 {
            Some(t)
        } else {
            None
        }
    }
}

/// Cálculo canônico de dano de queda do Aion Retail
pub fn calculate_fall_damage(delta_z: f32, max_hp: u32) -> u32 {
    if delta_z <= 5.0 {
        0
    } else if delta_z <= 35.0 {
        let ratio = (delta_z - 5.0) / 30.0;
        (max_hp as f32 * ratio) as u32
    } else {
        max_hp // Morte instantânea
    }
}

/// Vetor de planeio controlado (Gliding) com taxa de descida constante
pub fn calculate_glide_trajectory(from: &Coord, heading: u8, duration_sec: f32, forward_speed: f32) -> Coord {
    let angle_rad = (heading as f32 / 120.0) * std::f32::consts::PI * 2.0;
    let dx = angle_rad.sin() * forward_speed * duration_sec;
    let dy = angle_rad.cos() * forward_speed * duration_sec;
    let dz = -1.5 * duration_sec; // Taxa constante de descida suave de 1.5 m/s

    Coord::new(from.x + dx, from.y + dy, from.z + dz)
}

/// Grid de particionamento espacial em células de 100m x 100m
#[derive(Debug, Clone, Default)]
pub struct RegionGrid {
    pub cell_size: f32,
}

impl RegionGrid {
    pub fn new(cell_size: f32) -> Self {
        Self { cell_size: if cell_size <= 0.0 { 100.0 } else { cell_size } }
    }

    pub fn get_cell_coords(&self, pos: &Coord) -> (i32, i32) {
        ((pos.x / self.cell_size).floor() as i32, (pos.y / self.cell_size).floor() as i32)
    }

    /// Retorna as 9 regiões adjacentes (3x3 grid) visíveis para a entidade
    pub fn get_visible_regions(&self, pos: &Coord) -> Vec<(i32, i32)> {
        let (cx, cy) = self.get_cell_coords(pos);
        let mut regions = Vec::with_capacity(9);
        for dx in -1..=1 {
            for dy in -1..=1 {
                regions.push((cx + dx, cy + dy));
            }
        }
        regions
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

    #[test]
    fn test_barycentric_z_calculation() {
        let v0 = Coord::new(0.0, 0.0, 10.0);
        let v1 = Coord::new(10.0, 0.0, 20.0);
        let v2 = Coord::new(0.0, 10.0, 30.0);
        let tri = Triangle3D::new(v0, v1, v2);

        let z = tri.calculate_z(2.0, 2.0).expect("dentro do triangulo");
        assert!((z - 16.0).abs() < 1e-4);
    }

    #[test]
    fn test_moller_trumbore_ray_intersection() {
        let v0 = Coord::new(-5.0, 10.0, -5.0);
        let v1 = Coord::new(5.0, 10.0, -5.0);
        let v2 = Coord::new(0.0, 10.0, 5.0);
        let tri = Triangle3D::new(v0, v1, v2);

        // Raio disparado de (0, 0, 0) em direcao a (0, 20, 0) cruzando a parede em Y = 10
        let ray = Ray3D::new(Coord::new(0.0, 0.0, 0.0), Coord::new(0.0, 20.0, 0.0));
        let dist = ray.intersects_triangle(&tri).expect("deve cruzar o triangulo");
        assert!((dist - 10.0).abs() < 1e-3);
    }

    #[test]
    fn test_fall_damage_and_gliding() {
        assert_eq!(calculate_fall_damage(4.0, 1000), 0);
        assert_eq!(calculate_fall_damage(20.0, 1000), 500);
        assert_eq!(calculate_fall_damage(50.0, 1000), 1000);

        let start = Coord::new(100.0, 100.0, 50.0);
        let glided = calculate_glide_trajectory(&start, 0, 2.0, 6.0);
        assert_eq!(glided.z, 47.0); // Desceu 3.0 metros em 2 segundos
    }

    #[test]
    fn test_region_grid_3x3_neighborhood() {
        let grid = RegionGrid::new(100.0);
        let pos = Coord::new(150.0, 250.0, 0.0);
        assert_eq!(grid.get_cell_coords(&pos), (1, 2));

        let regions = grid.get_visible_regions(&pos);
        assert_eq!(regions.len(), 9);
        assert!(regions.contains(&(0, 1)));
        assert!(regions.contains(&(1, 2)));
        assert!(regions.contains(&(2, 3)));
    }
}
