//! Onde um personagem entra no mundo (Padrão Java AION)

#[derive(Debug, Clone, Copy)]
pub struct PontoDeEntrada {
    pub mapa: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub direcao: u8,
}

impl From<crate::dataholders::SpawnLocation> for PontoDeEntrada {
    fn from(loc: crate::dataholders::SpawnLocation) -> Self {
        Self {
            mapa: loc.map_id,
            x: loc.x,
            y: loc.y,
            z: loc.z,
            direcao: loc.heading,
        }
    }
}

/// Onde nasce um personagem **elyos** padrão (Poeta Classic 2.8 / 4.5)
pub const ELYOS: PontoDeEntrada = PontoDeEntrada {
    mapa: 210_010_000,
    x: 1207.7640,
    y: 1044.5725,
    z: 140.14894,
    direcao: 59,
};

/// Onde nasce um personagem **asmodiano** padrão (Ishalgen Classic 2.8 / 4.5)
pub const ASMODIANO: PontoDeEntrada = PontoDeEntrada {
    mapa: 220_010_000,
    x: 582.3742,
    y: 2790.7642,
    z: 299.3282,
    direcao: 66,
};

/// Ponto de entrada padrão por raça
pub fn ponto_de_entrada(raca: u32) -> PontoDeEntrada {
    match raca {
        1 => ASMODIANO,
        _ => ELYOS,
    }
}

pub const MAPA: u32 = 210_010_000;
pub const X: f32 = 1207.7640;
pub const Y: f32 = 1044.5725;
pub const Z: f32 = 140.14894;
pub const DIRECAO: u8 = 59;
