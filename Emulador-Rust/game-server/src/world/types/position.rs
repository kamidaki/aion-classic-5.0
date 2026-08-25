use super::heading::Heading;
use super::point3d::Point3D;
use crate::geoengine::math::Vector3f;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct WorldPosition {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: Heading,
    pub map_id: u32,
    pub instance_id: u32,
}

impl WorldPosition {
    pub fn new(map_id: u32, instance_id: u32, x: f32, y: f32, z: f32, heading: Heading) -> Self {
        Self {
            x,
            y,
            z,
            heading,
            map_id,
            instance_id,
        }
    }

    #[inline]
    pub fn point(&self) -> Point3D {
        Point3D::new(self.x, self.y, self.z)
    }

    #[inline]
    pub fn to_vector3f(&self) -> Vector3f {
        Vector3f::new(self.x, self.y, self.z)
    }

    #[inline]
    pub fn distance_to(&self, other: &Self) -> f32 {
        self.point().distance_to(&other.point())
    }

    #[inline]
    pub fn distance_2d_to(&self, other: &Self) -> f32 {
        self.point().distance_2d_to(&other.point())
    }
}
