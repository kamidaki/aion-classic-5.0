//! GlideFlag & Controle de Planar no Voo

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GlideFlag {
    None = 0,
    Gliding = 1,
    Windstream = 2,
}

impl GlideFlag {
    pub fn from_u8(val: u8) -> Self {
        match val {
            1 => GlideFlag::Gliding,
            2 => GlideFlag::Windstream,
            _ => GlideFlag::None,
        }
    }
}
