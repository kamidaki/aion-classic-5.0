use crate::geoengine::math::{Ray, Vector3f};
use super::result::CollisionResult;

/// Möller–Trumbore ray-triangle intersection algorithm.
/// Returns Option<(distance, contact_point, normal)>.
pub fn ray_triangle_intersect(
    ray: &Ray,
    v0: &Vector3f,
    v1: &Vector3f,
    v2: &Vector3f,
) -> Option<(f32, Vector3f, Vector3f)> {
    const EPSILON: f32 = 1e-7;

    let edge1 = *v1 - *v0;
    let edge2 = *v2 - *v0;
    let h = ray.direction.cross(&edge2);
    let a = edge1.dot(&h);

    if a.abs() < EPSILON {
        return None; // Ray is parallel to this triangle.
    }

    let f = 1.0 / a;
    let s = ray.origin - *v0;
    let u = f * s.dot(&h);

    if !(0.0..=1.0).contains(&u) {
        return None;
    }

    let q = s.cross(&edge1);
    let v = f * ray.direction.dot(&q);

    if v < 0.0 || u + v > 1.0 {
        return None;
    }

    // At this stage we can compute t to find out where the intersection point is on the line.
    let t = f * edge2.dot(&q);

    if t > EPSILON {
        let contact = ray.get_point(t);
        let normal = edge1.cross(&edge2).normalize();
        Some((t, contact, normal))
    } else {
        // Line intersection, but not a ray intersection (behind ray origin).
        None
    }
}
