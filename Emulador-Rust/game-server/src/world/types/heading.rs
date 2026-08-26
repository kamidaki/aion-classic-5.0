use crate::geoengine::math::fast_math::{angle_to_heading, heading_to_angle};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct Heading(pub u8);

impl Heading {
    #[inline]
    pub const fn new(val: u8) -> Self {
        Self(val)
    }

    #[inline]
    pub fn to_radians(&self) -> f32 {
        heading_to_angle(self.0)
    }

    #[inline]
    pub fn from_radians(radians: f32) -> Self {
        Self(angle_to_heading(radians))
    }

    #[inline]
    pub fn calculate_heading_to(from_x: f32, from_y: f32, to_x: f32, to_y: f32) -> Self {
        let dx = to_x - from_x;
        let dy = to_y - from_y;
        let angle = dy.atan2(dx);
        Self::from_radians(angle)
    }
}
