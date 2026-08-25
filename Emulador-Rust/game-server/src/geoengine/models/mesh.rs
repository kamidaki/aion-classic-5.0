use crate::geoengine::bounding::BoundingBox;
use crate::geoengine::collision::{ray_triangle_intersect, CollisionIntention, CollisionResult, CollisionResults};
use crate::geoengine::math::{Matrix4f, Ray, Vector3f};

#[derive(Debug, Clone)]
pub struct Mesh {
    pub vertices: Vec<Vector3f>,
    pub indices: Vec<u16>,
    pub collision_flags: u16,
    pub intentions: CollisionIntention,
    pub material_id: u8,
    pub bound: BoundingBox,
}

impl Mesh {
    pub fn new(vertices: Vec<Vector3f>, indices: Vec<u16>, collision_flags: u16) -> Self {
        let intentions = CollisionIntention::new((collision_flags >> 8) as u8);
        let material_id = (collision_flags & 0xFF) as u8;
        let bound = BoundingBox::from_points(&vertices);

        Self {
            vertices,
            indices,
            collision_flags,
            intentions,
            material_id,
            bound,
        }
    }

    pub fn triangle_count(&self) -> usize {
        self.indices.len() / 3
    }

    pub fn get_triangle(&self, index: usize) -> Option<(Vector3f, Vector3f, Vector3f)> {
        let idx = index * 3;
        if idx + 2 < self.indices.len() {
            let i0 = self.indices[idx] as usize;
            let i1 = self.indices[idx + 1] as usize;
            let i2 = self.indices[idx + 2] as usize;
            if i0 < self.vertices.len() && i1 < self.vertices.len() && i2 < self.vertices.len() {
                return Some((self.vertices[i0], self.vertices[i1], self.vertices[i2]));
            }
        }
        None
    }

    pub fn collide_ray(
        &self,
        ray: &Ray,
        transform: &Matrix4f,
        target_intentions: CollisionIntention,
        results: &mut CollisionResults,
    ) {
        if !self.intentions.intersects(target_intentions) {
            return;
        }

        let num_triangles = self.triangle_count();
        for i in 0..num_triangles {
            if let Some((v0, v1, v2)) = self.get_triangle(i) {
                // Transform vertices by the model world matrix
                let tv0 = transform.transform_point(&v0);
                let tv1 = transform.transform_point(&v1);
                let tv2 = transform.transform_point(&v2);

                if let Some((dist, contact, normal)) = ray_triangle_intersect(ray, &tv0, &tv1, &tv2) {
                    results.add(CollisionResult::new(
                        contact,
                        dist,
                        i,
                        self.material_id,
                        normal,
                    ));
                }
            }
        }
    }
}
