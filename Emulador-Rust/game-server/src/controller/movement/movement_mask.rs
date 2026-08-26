//! Máscara de Bits de Tipos de Movimento (MovementMask - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct MovementMask(pub u8);

impl MovementMask {
    pub const IMMEDIATE: u8 = 0x00;
    pub const MOUSE: u8 = 0x01;
    pub const KEYBOARD: u8 = 0x02;
    pub const GLIDE: u8 = 0x04;
    pub const FALL: u8 = 0x08;
    pub const VALIDATE: u8 = 0x10;
    pub const JUMP: u8 = 0x20;
    pub const NPC_WALK: u8 = 0x40;
    pub const NPC_RUN: u8 = 0x80;

    pub fn new(mask: u8) -> Self {
        Self(mask)
    }

    pub fn is_gliding(&self) -> bool {
        (self.0 & Self::GLIDE) != 0
    }

    pub fn is_falling(&self) -> bool {
        (self.0 & Self::FALL) != 0
    }

    pub fn is_jumping(&self) -> bool {
        (self.0 & Self::JUMP) != 0
    }
}
