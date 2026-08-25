//! Definições de tinturas e cores de armaduras (Dyes) do Aion Classic.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct RgbColor {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

impl RgbColor {
    pub fn new(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b }
    }

    pub fn to_hex(&self) -> u32 {
        ((self.r as u32) << 16) | ((self.g as u32) << 8) | (self.b as u32)
    }

    pub fn from_rgb_str(s: &str) -> Option<Self> {
        let parts: Vec<&str> = s.split(',').map(|p| p.trim()).collect();
        if parts.len() == 3 {
            let r = parts[0].parse::<u8>().ok()?;
            let g = parts[1].parse::<u8>().ok()?;
            let b = parts[2].parse::<u8>().ok()?;
            Some(Self { r, g, b })
        } else {
            None
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct DyeColorTemplate {
    pub id: u32,
    pub name: String,
    pub desc: String,
    pub color: RgbColor,
    pub dye_item_names: Vec<String>,
}
