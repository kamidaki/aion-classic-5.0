use crate::geoengine::math::Vector3f;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CollisionResult {
    pub contact_point: Vector3f,
    pub distance: f32,
    pub triangle_index: usize,
    pub material_id: u8,
    pub normal: Vector3f,
}

impl CollisionResult {
    pub fn new(
        contact_point: Vector3f,
        distance: f32,
        triangle_index: usize,
        material_id: u8,
        normal: Vector3f,
    ) -> Self {
        Self {
            contact_point,
            distance,
            triangle_index,
            material_id,
            normal,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct CollisionResults {
    pub results: Vec<CollisionResult>,
}

impl CollisionResults {
    pub fn new() -> Self {
        Self {
            results: Vec::with_capacity(16),
        }
    }

    pub fn add(&mut self, result: CollisionResult) {
        self.results.push(result);
    }

    pub fn sort_by_distance(&mut self) {
        self.results.sort_by(|a, b| a.distance.partial_cmp(&b.distance).unwrap_or(std::cmp::Ordering::Equal));
    }

    pub fn closest(&self) -> Option<&CollisionResult> {
        self.results.iter().min_by(|a, b| a.distance.partial_cmp(&b.distance).unwrap_or(std::cmp::Ordering::Equal))
    }

    pub fn is_empty(&self) -> bool {
        self.results.is_empty()
    }

    pub fn len(&self) -> usize {
        self.results.len()
    }
}
