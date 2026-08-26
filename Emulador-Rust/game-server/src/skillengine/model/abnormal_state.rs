//! Estados Anormais e Efeitos de Controle de Grupo (AbnormalState - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct AbnormalStateMask(pub u32);

impl AbnormalStateMask {
    pub const NONE: Self = Self(0);
    pub const STUN: Self = Self(1 << 0);
    pub const SLEEP: Self = Self(1 << 1);
    pub const ROOT: Self = Self(1 << 2);
    pub const SILENCE: Self = Self(1 << 3);
    pub const BLIND: Self = Self(1 << 4);
    pub const PARALYZE: Self = Self(1 << 5);
    pub const FEAR: Self = Self(1 << 6);
    pub const STUMBLE: Self = Self(1 << 7);
    pub const KNOCKBACK: Self = Self(1 << 8);
    pub const OPEN_AERIAL: Self = Self(1 << 9);
    pub const SNARE: Self = Self(1 << 10);
    pub const SLOW: Self = Self(1 << 11);
    pub const SPIN: Self = Self(1 << 12);
    pub const BIND: Self = Self(1 << 13);
    pub const POISON: Self = Self(1 << 14);
    pub const BLEED: Self = Self(1 << 15);
    pub const CURSE: Self = Self(1 << 16);
    pub const DISEASE: Self = Self(1 << 17);
    pub const HIDE: Self = Self(1 << 18);
    pub const SHIELD: Self = Self(1 << 19);
    pub const TRANSFORM: Self = Self(1 << 20);
    pub const SHAPECHANGE: Self = Self(1 << 21);
    pub const NO_FLY: Self = Self(1 << 22);
    pub const INVULNERABLE: Self = Self(1 << 23);
    pub const DEFORM: Self = Self(1 << 24);
    pub const TIME_FREEZING: Self = Self(1 << 25);

    pub fn contains(self, other: Self) -> bool {
        (self.0 & other.0) == other.0
    }

    pub fn intersects(self, other: Self) -> bool {
        (self.0 & other.0) != 0
    }

    pub fn insert(&mut self, other: Self) {
        self.0 |= other.0;
    }

    pub fn remove(&mut self, other: Self) {
        self.0 &= !other.0;
    }

    /// Verifica se o estado bloqueia conjuração de magias
    pub fn cant_cast_magic(self) -> bool {
        let magic_block = Self::SILENCE | Self::STUN | Self::SLEEP | Self::FEAR | Self::PARALYZE
            | Self::STUMBLE | Self::OPEN_AERIAL | Self::SPIN | Self::TIME_FREEZING;
        self.intersects(magic_block)
    }

    /// Verifica se o estado bloqueia ataques físicos e habilidades físicas
    pub fn cant_cast_physical(self) -> bool {
        let phys_block = Self::BIND | Self::STUN | Self::SLEEP | Self::FEAR | Self::PARALYZE
            | Self::STUMBLE | Self::OPEN_AERIAL | Self::SPIN | Self::TIME_FREEZING;
        self.intersects(phys_block)
    }

    /// Verifica se o estado impede movimento (imobilização)
    pub fn cant_move(self) -> bool {
        let move_block = Self::ROOT | Self::STUN | Self::SLEEP | Self::PARALYZE | Self::STUMBLE
            | Self::OPEN_AERIAL | Self::SPIN | Self::TIME_FREEZING;
        self.intersects(move_block)
    }

    /// Verifica se qualquer dano recebido remove o efeito (ex: Sleep)
    pub fn break_on_damage(self) -> bool {
        self.contains(Self::SLEEP)
    }
}

impl std::ops::BitOr for AbnormalStateMask {
    type Output = Self;
    fn bitor(self, rhs: Self) -> Self::Output {
        Self(self.0 | rhs.0)
    }
}

impl std::ops::BitOrAssign for AbnormalStateMask {
    fn bitor_assign(&mut self, rhs: Self) {
        self.0 |= rhs.0;
    }
}

impl std::ops::BitAnd for AbnormalStateMask {
    type Output = Self;
    fn bitand(self, rhs: Self) -> Self::Output {
        Self(self.0 & rhs.0)
    }
}
