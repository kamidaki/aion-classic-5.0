pub mod math;
pub mod bounding;
pub mod collision;
pub mod models;
pub mod loader;
pub mod height;
pub mod movement;
pub mod pathfinding;

pub use math::{Matrix3f, Matrix4f, Ray, Vector3f};
pub use bounding::{BoundingBox, BoundingSphere, BoundingVolume};
pub use collision::{CollisionIntention, CollisionResult, CollisionResults};
pub use models::{DoorGeometry, Geometry, GeoMap, Mesh, Node, Spatial, Terrain};
pub use loader::{GeoConfig, MeshLoader, WorldLoader};
pub use height::HeightQuery;
pub use movement::{FallDetector, MovementValidationResult, MovementValidator};
pub use pathfinding::{AStarPathfinder, NavMeshGraph};

#[cfg(test)]
mod tests;

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, RwLock};

#[derive(Clone)]
pub struct GeoEngine {
    config: GeoConfig,
    models: Arc<RwLock<HashMap<String, Spatial>>>,
    maps: Arc<RwLock<HashMap<u32, Arc<GeoMap>>>>,
}

impl GeoEngine {
    pub fn new(config: GeoConfig) -> Self {
        Self {
            config,
            models: Arc::new(RwLock::new(HashMap::new())),
            maps: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub fn initialize(&self) -> std::io::Result<()> {
        let mesh_path = self.config.geo_dir.join("meshs.geo");
        if mesh_path.exists() {
            println!("INFO: [GeoEngine] Loading meshes from {}...", mesh_path.display());
            let loaded_models = MeshLoader::load_meshes(&mesh_path)?;
            println!("INFO: [GeoEngine] Loaded {} 3D mesh templates successfully.", loaded_models.len());
            let mut models_guard = self.models.write().unwrap();
            *models_guard = loaded_models;
        } else {
            println!("WARN: [GeoEngine] meshs.geo not found at {}. Using empty mesh set.", mesh_path.display());
        }
        Ok(())
    }

    pub fn load_world(&self, world_id: u32) -> std::io::Result<Arc<GeoMap>> {
        {
            let maps = self.maps.read().unwrap();
            if let Some(map) = maps.get(&world_id) {
                return Ok(map.clone());
            }
        }

        let geo_file = self.config.geo_dir.join(format!("{}.geo", world_id));
        let geo_map = if geo_file.exists() {
            println!("INFO: [GeoEngine] Loading world {} from {}...", world_id, geo_file.display());
            let models_guard = self.models.read().unwrap();
            WorldLoader::load_world(world_id, &geo_file, &models_guard)?
        } else {
            println!("WARN: [GeoEngine] World file {}.geo not found. Initializing flat default map.", world_id);
            GeoMap::new(world_id)
        };

        let map_arc = Arc::new(geo_map);
        let mut maps = self.maps.write().unwrap();
        maps.insert(world_id, map_arc.clone());
        Ok(map_arc)
    }

    pub fn get_z(&self, world_id: u32, x: f32, y: f32, current_z: Option<f32>) -> f32 {
        let maps = self.maps.read().unwrap();
        if let Some(map) = maps.get(&world_id) {
            map.get_z(x, y, current_z)
        } else {
            current_z.unwrap_or(0.0)
        }
    }

    pub fn can_see(&self, world_id: u32, start: &Vector3f, end: &Vector3f) -> bool {
        let maps = self.maps.read().unwrap();
        if let Some(map) = maps.get(&world_id) {
            map.can_see(start, end)
        } else {
            true
        }
    }

    pub fn validate_movement(
        &self,
        world_id: u32,
        current_pos: &Vector3f,
        target_pos: &Vector3f,
        elapsed_sec: f32,
        is_flying: bool,
        is_gliding: bool,
    ) -> MovementValidationResult {
        let maps = self.maps.read().unwrap();
        if let Some(map) = maps.get(&world_id) {
            MovementValidator::validate_step(map, current_pos, target_pos, elapsed_sec, is_flying, is_gliding)
        } else {
            MovementValidationResult {
                is_valid: true,
                adjusted_pos: *target_pos,
                reason: None,
            }
        }
    }

    pub fn find_path(
        &self,
        world_id: u32,
        start: Vector3f,
        goal: Vector3f,
        step_size: f32,
        max_iterations: usize,
    ) -> Option<Vec<Vector3f>> {
        let maps = self.maps.read().unwrap();
        if let Some(map) = maps.get(&world_id) {
            AStarPathfinder::find_path(map, start, goal, step_size, max_iterations)
        } else {
            Some(vec![start, goal])
        }
    }
}
