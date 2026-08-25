//! Definições de slots de equipamento do Aion Classic (64-bit mask).

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct ItemSlot(pub u64);

impl ItemSlot {
    pub const NONE: Self = Self(0);
    pub const MAIN_HAND: Self = Self(1 << 0);        // 1 (0x1)
    pub const SUB_HAND: Self = Self(1 << 1);         // 2 (0x2)
    pub const HELMET: Self = Self(1 << 2);           // 4 (0x4)
    pub const TORSO: Self = Self(1 << 3);            // 8 (0x8)
    pub const GLOVES: Self = Self(1 << 4);           // 16 (0x10)
    pub const BOOTS: Self = Self(1 << 5);            // 32 (0x20)
    pub const EAR_LEFT: Self = Self(1 << 6);         // 64 (0x40)
    pub const EAR_RIGHT: Self = Self(1 << 7);        // 128 (0x80)
    pub const RING_LEFT: Self = Self(1 << 8);        // 256 (0x100)
    pub const RING_RIGHT: Self = Self(1 << 9);       // 512 (0x200)
    pub const NECKLACE: Self = Self(1 << 10);        // 1024 (0x400)
    pub const SHOULDERS: Self = Self(1 << 11);       // 2048 (0x800)
    pub const PANTS: Self = Self(1 << 12);           // 4096 (0x1000)
    pub const POWER_SHARD_LEFT: Self = Self(1 << 13);// 8192 (0x2000)
    pub const POWER_SHARD_RIGHT: Self = Self(1 << 14);// 16384 (0x4000)
    pub const WINGS: Self = Self(1 << 15);           // 32768 (0x8000)
    pub const WAIST: Self = Self(1 << 16);           // 65536 (0x10000)
    pub const PLUME: Self = Self(1 << 17);           // 131072 (0x20000)
    pub const BRACELET: Self = Self(1 << 18);        // 262144 (0x40000)

    // Slots combinados
    pub const MAIN_OR_SUB: Self = Self(Self::MAIN_HAND.0 | Self::SUB_HAND.0);
    pub const EARRINGS: Self = Self(Self::EAR_LEFT.0 | Self::EAR_RIGHT.0);
    pub const RINGS: Self = Self(Self::RING_LEFT.0 | Self::RING_RIGHT.0);
    pub const SHARDS: Self = Self(Self::POWER_SHARD_LEFT.0 | Self::POWER_SHARD_RIGHT.0);

    #[inline]
    pub fn contains(&self, other: ItemSlot) -> bool {
        (self.0 & other.0) == other.0
    }

    #[inline]
    pub fn intersects(&self, other: ItemSlot) -> bool {
        (self.0 & other.0) != 0
    }

    #[inline]
    pub fn is_armor_body(&self) -> bool {
        self.intersects(Self(Self::TORSO.0 | Self::PANTS.0 | Self::GLOVES.0 | Self::BOOTS.0 | Self::SHOULDERS.0))
    }

    #[inline]
    pub fn is_weapon(&self) -> bool {
        self.intersects(Self::MAIN_OR_SUB)
    }

    #[inline]
    pub fn is_accessory(&self) -> bool {
        self.intersects(Self(Self::HELMET.0 | Self::NECKLACE.0 | Self::EARRINGS.0 | Self::RINGS.0 | Self::WAIST.0 | Self::WINGS.0 | Self::PLUME.0 | Self::BRACELET.0))
    }

    /// Converte a string de slot do XML do cliente para ItemSlot.
    pub fn from_xml_str(s: &str) -> Self {
        match s.trim().to_lowercase().as_str() {
            "main_or_sub" => Self::MAIN_OR_SUB,
            "main" => Self::MAIN_HAND,
            "sub" => Self::SUB_HAND,
            "torso" => Self::TORSO,
            "leg" | "pants" => Self::PANTS,
            "glove" | "gloves" => Self::GLOVES,
            "foot" | "boots" => Self::BOOTS,
            "shoulder" | "shoulders" => Self::SHOULDERS,
            "head" | "helmet" => Self::HELMET,
            "neck" | "necklace" => Self::NECKLACE,
            "right_or_left_ear" | "ear" | "earring" => Self::EARRINGS,
            "right_or_left_finger" | "finger" | "ring" => Self::RINGS,
            "waist" | "belt" => Self::WAIST,
            "wing" | "wings" => Self::WINGS,
            "plume" => Self::PLUME,
            "bracelet" => Self::BRACELET,
            "shard" => Self::SHARDS,
            _ => Self::NONE,
        }
    }
}
