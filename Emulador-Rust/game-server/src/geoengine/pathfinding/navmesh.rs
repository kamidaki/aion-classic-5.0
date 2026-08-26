use std::collections::HashMap;
use crate::geoengine::math::Vector3f;

#[derive(Debug, Clone)]
pub struct NavWaypoint {
    pub id: u32,
    pub position: Vector3f,
    pub neighbors: Vec<u32>,
}

#[derive(Debug, Clone, Default)]
pub struct NavMeshGraph {
    pub waypoints: HashMap<u32, NavWaypoint>,
}

impl NavMeshGraph {
    pub fn new() -> Self {
        Self {
            waypoints: HashMap::new(),
        }
    }

    pub fn add_waypoint(&mut self, id: u32, position: Vector3f, neighbors: Vec<u32>) {
        self.waypoints.insert(id, NavWaypoint { id, position, neighbors });
    }

    pub fn find_nearest_waypoint(&self, pos: &Vector3f) -> Option<&NavWaypoint> {
        self.waypoints
            .values()
            .min_by(|a, b| {
                a.position.distance_squared(pos)
                    .partial_cmp(&b.position.distance_squared(pos))
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    }
}
