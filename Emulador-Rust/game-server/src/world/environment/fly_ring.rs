use crate::geoengine::math::Vector3f;

#[derive(Debug, Clone)]
pub struct FlyRing {
    pub ring_id: u32,
    pub map_id: u32,
    pub center: Vector3f,
    pub radius: f32,
    pub speed_boost: f32,
}

impl FlyRing {
    pub fn new(ring_id: u32, map_id: u32, center: Vector3f, radius: f32, speed_boost: f32) -> Self {
        Self {
            ring_id,
            map_id,
            center,
            radius,
            speed_boost,
        }
    }

    pub fn intersects_point(&self, pos: &Vector3f) -> bool {
        self.center.distance_squared(pos) <= (self.radius * self.radius)
    }
}
