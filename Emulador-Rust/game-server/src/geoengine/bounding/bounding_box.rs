use super::volume::BoundingVolume;
use crate::geoengine::math::{Ray, Vector3f};

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct BoundingBox {
    pub min: Vector3f,
    pub max: Vector3f,
    pub center: Vector3f,
    pub extent: Vector3f,
}

impl BoundingBox {
    pub fn new(min: Vector3f, max: Vector3f) -> Self {
        let center = (min + max) * 0.5;
        let extent = (max - min) * 0.5;
        Self {
            min,
            max,
            center,
            extent,
        }
    }

    pub fn from_points(points: &[Vector3f]) -> Self {
        if points.is_empty() {
            return Self::new(Vector3f::ZERO, Vector3f::ZERO);
        }
        let mut min = points[0];
        let mut max = points[0];
        for p in &points[1..] {
            min = min.min(p);
            max = max.max(p);
        }
        Self::new(min, max)
    }

    pub fn merge(&self, other: &Self) -> Self {
        let min = self.min.min(&other.min);
        let max = self.max.max(&other.max);
        Self::new(min, max)
    }

    pub fn intersects_ray(&self, ray: &Ray) -> bool {
        self.intersects_ray_distance(ray).is_some()
    }

    pub fn intersects_ray_distance(&self, ray: &Ray) -> Option<f32> {
        let mut tmin = f32::NEG_INFINITY;
        let mut tmax = f32::INFINITY;

        // X axis slab
        if ray.direction.x.abs() > 1e-8 {
            let inv_d = 1.0 / ray.direction.x;
            let mut t1 = (self.min.x - ray.origin.x) * inv_d;
            let mut t2 = (self.max.x - ray.origin.x) * inv_d;
            if t1 > t2 {
                std::mem::swap(&mut t1, &mut t2);
            }
            tmin = tmin.max(t1);
            tmax = tmax.min(t2);
            if tmin > tmax {
                return None;
            }
        } else if ray.origin.x < self.min.x || ray.origin.x > self.max.x {
            return None;
        }

        // Y axis slab
        if ray.direction.y.abs() > 1e-8 {
            let inv_d = 1.0 / ray.direction.y;
            let mut t1 = (self.min.y - ray.origin.y) * inv_d;
            let mut t2 = (self.max.y - ray.origin.y) * inv_d;
            if t1 > t2 {
                std::mem::swap(&mut t1, &mut t2);
            }
            tmin = tmin.max(t1);
            tmax = tmax.min(t2);
            if tmin > tmax {
                return None;
            }
        } else if ray.origin.y < self.min.y || ray.origin.y > self.max.y {
            return None;
        }

        // Z axis slab
        if ray.direction.z.abs() > 1e-8 {
            let inv_d = 1.0 / ray.direction.z;
            let mut t1 = (self.min.z - ray.origin.z) * inv_d;
            let mut t2 = (self.max.z - ray.origin.z) * inv_d;
            if t1 > t2 {
                std::mem::swap(&mut t1, &mut t2);
            }
            tmin = tmin.max(t1);
            tmax = tmax.min(t2);
            if tmin > tmax {
                return None;
            }
        } else if ray.origin.z < self.min.z || ray.origin.z > self.max.z {
            return None;
        }

        if tmax < 0.0 {
            return None;
        }

        let hit_dist = if tmin >= 0.0 { tmin } else { tmax };
        Some(hit_dist)
    }

    pub fn contains_point(&self, point: &Vector3f) -> bool {
        point.x >= self.min.x && point.x <= self.max.x
            && point.y >= self.min.y && point.y <= self.max.y
            && point.z >= self.min.z && point.z <= self.max.z
    }
}

impl BoundingVolume for BoundingBox {
    fn intersects_ray(&self, ray: &Ray) -> bool {
        self.intersects_ray_distance(ray).is_some()
    }

    fn intersects_ray_distance(&self, ray: &Ray) -> Option<f32> {
        let mut tmin = f32::NEG_INFINITY;
        let mut tmax = f32::INFINITY;

        // X axis slab
        if ray.direction.x.abs() > 1e-8 {
            let inv_d = 1.0 / ray.direction.x;
            let mut t1 = (self.min.x - ray.origin.x) * inv_d;
            let mut t2 = (self.max.x - ray.origin.x) * inv_d;
            if t1 > t2 {
                std::mem::swap(&mut t1, &mut t2);
            }
            tmin = tmin.max(t1);
            tmax = tmax.min(t2);
            if tmin > tmax {
                return None;
            }
        } else if ray.origin.x < self.min.x || ray.origin.x > self.max.x {
            return None;
        }

        // Y axis slab
        if ray.direction.y.abs() > 1e-8 {
            let inv_d = 1.0 / ray.direction.y;
            let mut t1 = (self.min.y - ray.origin.y) * inv_d;
            let mut t2 = (self.max.y - ray.origin.y) * inv_d;
            if t1 > t2 {
                std::mem::swap(&mut t1, &mut t2);
            }
            tmin = tmin.max(t1);
            tmax = tmax.min(t2);
            if tmin > tmax {
                return None;
            }
        } else if ray.origin.y < self.min.y || ray.origin.y > self.max.y {
            return None;
        }

        // Z axis slab
        if ray.direction.z.abs() > 1e-8 {
            let inv_d = 1.0 / ray.direction.z;
            let mut t1 = (self.min.z - ray.origin.z) * inv_d;
            let mut t2 = (self.max.z - ray.origin.z) * inv_d;
            if t1 > t2 {
                std::mem::swap(&mut t1, &mut t2);
            }
            tmin = tmin.max(t1);
            tmax = tmax.min(t2);
            if tmin > tmax {
                return None;
            }
        } else if ray.origin.z < self.min.z || ray.origin.z > self.max.z {
            return None;
        }

        if tmax < 0.0 {
            return None;
        }

        let hit_dist = if tmin >= 0.0 { tmin } else { tmax };
        Some(hit_dist)
    }

    fn contains_point(&self, point: &Vector3f) -> bool {
        point.x >= self.min.x && point.x <= self.max.x
            && point.y >= self.min.y && point.y <= self.max.y
            && point.z >= self.min.z && point.z <= self.max.z
    }

    fn get_center(&self) -> Vector3f {
        self.center
    }

    fn clone_box(&self) -> Box<dyn BoundingVolume> {
        Box::new(*self)
    }
}
