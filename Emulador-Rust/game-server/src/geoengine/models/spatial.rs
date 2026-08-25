use crate::geoengine::bounding::BoundingBox;
use crate::geoengine::collision::{CollisionIntention, CollisionResults};
use crate::geoengine::math::{Matrix3f, Matrix4f, Ray, Vector3f};
use super::mesh::Mesh;

#[derive(Debug, Clone)]
pub struct Geometry {
    pub name: String,
    pub mesh: Mesh,
    pub world_matrix: Matrix4f,
    pub world_bound: BoundingBox,
}

impl Geometry {
    pub fn new(name: String, mesh: Mesh) -> Self {
        let world_bound = mesh.bound;
        Self {
            name,
            mesh,
            world_matrix: Matrix4f::IDENTITY,
            world_bound,
        }
    }

    pub fn set_transform(&mut self, rot: &Matrix3f, loc: &Vector3f, scale: f32) {
        self.world_matrix = Matrix4f::from_transform(rot, loc, scale);
        // Transform local bound to world bound
        let corners = [
            Vector3f::new(self.mesh.bound.min.x, self.mesh.bound.min.y, self.mesh.bound.min.z),
            Vector3f::new(self.mesh.bound.max.x, self.mesh.bound.min.y, self.mesh.bound.min.z),
            Vector3f::new(self.mesh.bound.min.x, self.mesh.bound.max.y, self.mesh.bound.min.z),
            Vector3f::new(self.mesh.bound.max.x, self.mesh.bound.max.y, self.mesh.bound.min.z),
            Vector3f::new(self.mesh.bound.min.x, self.mesh.bound.min.y, self.mesh.bound.max.z),
            Vector3f::new(self.mesh.bound.max.x, self.mesh.bound.min.y, self.mesh.bound.max.z),
            Vector3f::new(self.mesh.bound.min.x, self.mesh.bound.max.y, self.mesh.bound.max.z),
            Vector3f::new(self.mesh.bound.max.x, self.mesh.bound.max.y, self.mesh.bound.max.z),
        ];
        let transformed_corners: Vec<Vector3f> = corners
            .iter()
            .map(|c| self.world_matrix.transform_point(c))
            .collect();
        self.world_bound = BoundingBox::from_points(&transformed_corners);
    }

    pub fn collide_ray(&self, ray: &Ray, target_intentions: CollisionIntention, results: &mut CollisionResults) {
        if !self.world_bound.intersects_ray_distance(ray).is_some() {
            return;
        }
        self.mesh.collide_ray(ray, &self.world_matrix, target_intentions, results);
    }
}

#[derive(Debug, Clone)]
pub struct Node {
    pub name: String,
    pub children: Vec<Spatial>,
    pub collision_flags: u16,
    pub intentions: CollisionIntention,
    pub world_bound: BoundingBox,
    pub world_matrix: Matrix4f,
}

impl Node {
    pub fn new(name: String) -> Self {
        Self {
            name,
            children: Vec::new(),
            collision_flags: 0,
            intentions: CollisionIntention::NONE,
            world_bound: BoundingBox::new(Vector3f::ZERO, Vector3f::ZERO),
            world_matrix: Matrix4f::IDENTITY,
        }
    }

    pub fn attach_child(&mut self, child: Spatial) {
        self.children.push(child);
        self.update_world_bound();
    }

    pub fn set_collision_flags(&mut self, flags: u16) {
        self.collision_flags = flags;
        self.intentions = CollisionIntention::new((flags >> 8) as u8);
    }

    pub fn set_transform(&mut self, rot: &Matrix3f, loc: &Vector3f, scale: f32) {
        self.world_matrix = Matrix4f::from_transform(rot, loc, scale);
        for child in &mut self.children {
            match child {
                Spatial::Geom(g) => g.set_transform(rot, loc, scale),
                Spatial::NodeSpatial(n) => n.set_transform(rot, loc, scale),
                Spatial::Door(d) => d.geom.set_transform(rot, loc, scale),
            }
        }
        self.update_world_bound();
    }

    pub fn update_world_bound(&mut self) {
        if self.children.is_empty() {
            return;
        }
        let mut combined = match &self.children[0] {
            Spatial::Geom(g) => g.world_bound,
            Spatial::NodeSpatial(n) => n.world_bound,
            Spatial::Door(d) => d.geom.world_bound,
        };
        for child in &self.children[1..] {
            let b = match child {
                Spatial::Geom(g) => g.world_bound,
                Spatial::NodeSpatial(n) => n.world_bound,
                Spatial::Door(d) => d.geom.world_bound,
            };
            combined = combined.merge(&b);
        }
        self.world_bound = combined;
    }

    pub fn collide_ray(&self, ray: &Ray, target_intentions: CollisionIntention, results: &mut CollisionResults) {
        if !self.world_bound.intersects_ray_distance(ray).is_some() {
            return;
        }
        for child in &self.children {
            match child {
                Spatial::Geom(g) => g.collide_ray(ray, target_intentions, results),
                Spatial::NodeSpatial(n) => n.collide_ray(ray, target_intentions, results),
                Spatial::Door(d) => d.collide_ray(ray, target_intentions, results),
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct DoorGeometry {
    pub name: String,
    pub geom: Geometry,
    pub is_open: bool,
}

impl DoorGeometry {
    pub fn new(name: String, geom: Geometry) -> Self {
        Self {
            name,
            geom,
            is_open: false,
        }
    }

    pub fn collide_ray(&self, ray: &Ray, target_intentions: CollisionIntention, results: &mut CollisionResults) {
        if self.is_open {
            return; // Open doors don't block
        }
        self.geom.collide_ray(ray, target_intentions, results);
    }
}

#[derive(Debug, Clone)]
pub enum Spatial {
    Geom(Geometry),
    NodeSpatial(Node),
    Door(DoorGeometry),
}

impl Spatial {
    pub fn name(&self) -> &str {
        match self {
            Spatial::Geom(g) => &g.name,
            Spatial::NodeSpatial(n) => &n.name,
            Spatial::Door(d) => &d.name,
        }
    }

    pub fn world_bound(&self) -> &BoundingBox {
        match self {
            Spatial::Geom(g) => &g.world_bound,
            Spatial::NodeSpatial(n) => &n.world_bound,
            Spatial::Door(d) => &d.geom.world_bound,
        }
    }

    pub fn set_transform(&mut self, rot: &Matrix3f, loc: &Vector3f, scale: f32) {
        match self {
            Spatial::Geom(g) => g.set_transform(rot, loc, scale),
            Spatial::NodeSpatial(n) => n.set_transform(rot, loc, scale),
            Spatial::Door(d) => d.geom.set_transform(rot, loc, scale),
        }
    }

    pub fn collide_ray(&self, ray: &Ray, target_intentions: CollisionIntention, results: &mut CollisionResults) {
        match self {
            Spatial::Geom(g) => g.collide_ray(ray, target_intentions, results),
            Spatial::NodeSpatial(n) => n.collide_ray(ray, target_intentions, results),
            Spatial::Door(d) => d.collide_ray(ray, target_intentions, results),
        }
    }
}
