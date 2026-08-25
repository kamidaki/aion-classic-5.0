pub mod intentions;
pub mod result;
pub mod intersection;

pub use intentions::CollisionIntention;
pub use result::{CollisionResult, CollisionResults};
pub use intersection::ray_triangle_intersect;
