use super::volume::BoundingVolume;
use crate::geoengine::math::{Ray, Vector3f};

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct BoundingSphere {
    pub center: Vector3f,
    pub radius: f32,
}

impl BoundingSphere {
    pub fn new(center: Vector3f, radius: f32) -> Self {
        Self { center, radius }
    }
}

impl BoundingVolume for BoundingSphere {
    fn intersects_ray(&self, ray: &Ray) -> bool {
        self.intersects_ray_distance(ray).is_some()
    }

    fn intersects_ray_distance(&self, ray: &Ray) -> Option<f32> {
        let oc = ray.origin - self.center;
        let a = ray.direction.dot(&ray.direction);
        let b = 2.0 * oc.dot(&ray.direction);
        let c = oc.dot(&oc) - self.radius * self.radius;
        let discriminant = b * b - 4.0 * a * c;
        if discriminant < 0.0 {
            return None;
        }
        let sqrt_d = discriminant.sqrt();
        let t1 = (-b - sqrt_d) / (2.0 * a);
        let t2 = (-b + sqrt_d) / (2.0 * a);
        if t1 >= 0.0 {
            Some(t1)
        } else if t2 >= 0.0 {
            Some(t2)
        } else {
            None
        }
    }

    fn contains_point(&self, point: &Vector3f) -> bool {
        self.center.distance_squared(point) <= self.radius * self.radius
    }

    fn get_center(&self) -> Vector3f {
        self.center
    }

    fn clone_box(&self) -> Box<dyn BoundingVolume> {
        Box::new(*self)
    }
}
