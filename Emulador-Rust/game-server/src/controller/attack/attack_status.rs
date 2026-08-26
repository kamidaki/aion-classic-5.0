//! Status de Ataque e Reação de Combate (AttackStatus - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AttackStatus {
    #[default]
    NormalHit,
    Dodge,
    OffhandDodge,
    Parry,
    OffhandParry,
    Block,
    OffhandBlock,
    Resist,
    OffhandResist,
    Buf,
    OffhandBuf,
    OffhandNormalHit,
    CriticalDodge,
    CriticalParry,
    CriticalBlock,
    CriticalResist,
    Critical,
    OffhandCriticalDodge,
    OffhandCriticalParry,
    OffhandCriticalBlock,
    OffhandCriticalResist,
    OffhandCritical,
}

impl AttackStatus {
    pub fn id(&self) -> u8 {
        match self {
            Self::Dodge => 0,
            Self::OffhandDodge => 1,
            Self::Parry => 2,
            Self::OffhandParry => 3,
            Self::Block => 4,
            Self::OffhandBlock => 5,
            Self::Resist => 6,
            Self::OffhandResist => 7,
            Self::Buf => 8,
            Self::OffhandBuf => 9,
            Self::NormalHit => 10,
            Self::OffhandNormalHit => 11,
            Self::CriticalDodge => 192,
            Self::CriticalParry => 194,
            Self::CriticalBlock => 196,
            Self::CriticalResist => 198,
            Self::Critical => 202,
            Self::OffhandCriticalDodge => 209,
            Self::OffhandCriticalParry => 211,
            Self::OffhandCriticalBlock => 213,
            Self::OffhandCriticalResist => 215,
            Self::OffhandCritical => 219,
        }
    }

    pub fn is_counter_skill(&self) -> bool {
        matches!(
            self,
            Self::Dodge
                | Self::OffhandDodge
                | Self::Parry
                | Self::OffhandParry
                | Self::Block
                | Self::OffhandBlock
                | Self::CriticalDodge
                | Self::CriticalParry
                | Self::CriticalBlock
                | Self::OffhandCriticalDodge
                | Self::OffhandCriticalParry
                | Self::OffhandCriticalBlock
        )
    }

    pub fn is_critical(&self) -> bool {
        matches!(
            self,
            Self::CriticalDodge
                | Self::CriticalParry
                | Self::CriticalBlock
                | Self::CriticalResist
                | Self::Critical
                | Self::OffhandCriticalDodge
                | Self::OffhandCriticalParry
                | Self::OffhandCriticalBlock
                | Self::OffhandCriticalResist
                | Self::OffhandCritical
        )
    }

    pub fn get_offhand_status(main_status: AttackStatus) -> AttackStatus {
        match main_status {
            Self::Dodge => Self::OffhandDodge,
            Self::Parry => Self::OffhandParry,
            Self::Block => Self::OffhandBlock,
            Self::Resist => Self::OffhandResist,
            Self::Buf => Self::OffhandBuf,
            Self::NormalHit => Self::OffhandNormalHit,
            Self::Critical => Self::OffhandCritical,
            Self::CriticalDodge => Self::OffhandCriticalDodge,
            Self::CriticalParry => Self::OffhandCriticalParry,
            Self::CriticalBlock => Self::OffhandCriticalBlock,
            Self::CriticalResist => Self::OffhandCriticalResist,
            other => other,
        }
    }
}
