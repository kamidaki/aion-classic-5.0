use super::vector3::Vector3f;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Ray {
    pub origin: Vector3f,
    pub direction: Vector3f,
}

impl Ray {
    #[inline]
    pub fn new(origin: Vector3f, direction: Vector3f) -> Self {
        Self {
            origin,
            direction: direction.normalize(),
        }
    }

    #[inline]
    pub fn get_point(&self, distance: f32) -> Vector3f {
        self.origin + self.direction * distance
    }
}
