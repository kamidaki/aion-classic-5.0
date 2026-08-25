use crate::geoengine::math::{Ray, Vector3f};

pub trait BoundingVolume: Send + Sync {
    fn intersects_ray(&self, ray: &Ray) -> bool;
    fn intersects_ray_distance(&self, ray: &Ray) -> Option<f32>;
    fn contains_point(&self, point: &Vector3f) -> bool;
    fn get_center(&self) -> Vector3f;
    fn clone_box(&self) -> Box<dyn BoundingVolume>;
}
