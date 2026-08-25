#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CollisionIntention(pub u8);

impl CollisionIntention {
    pub const NONE: Self = Self(0);
    pub const PHYSICAL: Self = Self(1 << 0); // 1
    pub const MATERIAL: Self = Self(1 << 1); // 2
    pub const DOOR: Self = Self(1 << 2);     // 4
    pub const MOVEABLE: Self = Self(1 << 3); // 8
    pub const WALKABLE: Self = Self(1 << 4); // 16
    pub const SKILL: Self = Self(1 << 5);    // 32
    pub const ALL: Self = Self(0xFF);

    #[inline]
    pub const fn new(flags: u8) -> Self {
        Self(flags)
    }

    #[inline]
    pub const fn contains(&self, other: Self) -> bool {
        (self.0 & other.0) == other.0
    }

    #[inline]
    pub const fn intersects(&self, other: Self) -> bool {
        (self.0 & other.0) != 0
    }

    #[inline]
    pub const fn id(&self) -> u8 {
        self.0
    }
}

impl std::ops::BitOr for CollisionIntention {
    type Output = Self;
    #[inline]
    fn bitor(self, rhs: Self) -> Self::Output {
        Self(self.0 | rhs.0)
    }
}

impl std::ops::BitOrAssign for CollisionIntention {
    #[inline]
    fn bitor_assign(&mut self, rhs: Self) {
        self.0 |= rhs.0;
    }
}

impl std::ops::BitAnd for CollisionIntention {
    type Output = Self;
    #[inline]
    fn bitand(self, rhs: Self) -> Self::Output {
        Self(self.0 & rhs.0)
    }
}
