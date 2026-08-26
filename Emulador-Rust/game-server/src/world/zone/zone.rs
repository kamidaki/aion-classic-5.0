use super::zone_type::ZoneType;
use crate::geoengine::math::Vector3f;

#[derive(Debug, Clone)]
pub enum ZoneGeometry {
    Box {
        min: Vector3f,
        max: Vector3f,
    },
    Cylinder {
        center: Vector3f,
        radius: f32,
        bottom_z: f32,
        top_z: f32,
    },
    Polygon {
        points: Vec<(f32, f32)>,
        bottom_z: f32,
        top_z: f32,
    },
}

impl ZoneGeometry {
    pub fn contains(&self, x: f32, y: f32, z: f32) -> bool {
        match self {
            ZoneGeometry::Box { min, max } => {
                x >= min.x && x <= max.x && y >= min.y && y <= max.y && z >= min.z && z <= max.z
            }
            ZoneGeometry::Cylinder { center, radius, bottom_z, top_z } => {
                if z < *bottom_z || z > *top_z {
                    return false;
                }
                let dx = x - center.x;
                let dy = y - center.y;
                (dx * dx + dy * dy) <= (radius * radius)
            }
            ZoneGeometry::Polygon { points, bottom_z, top_z } => {
                if z < *bottom_z || z > *top_z {
                    return false;
                }
                // Ray casting algorithm for point in 2D polygon
                let mut inside = false;
                let len = points.len();
                if len < 3 {
                    return false;
                }
                let mut j = len - 1;
                for i in 0..len {
                    let (xi, yi) = points[i];
                    let (xj, yj) = points[j];
                    if ((yi > y) != (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi) {
                        inside = !inside;
                    }
                    j = i;
                }
                inside
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct Zone {
    pub zone_id: u32,
    pub name: String,
    pub map_id: u32,
    pub zone_type: ZoneType,
    pub geometry: ZoneGeometry,
    pub priority: i32,
}

impl Zone {
    pub fn new(
        zone_id: u32,
        name: String,
        map_id: u32,
        zone_type: ZoneType,
        geometry: ZoneGeometry,
        priority: i32,
    ) -> Self {
        Self {
            zone_id,
            name,
            map_id,
            zone_type,
            geometry,
            priority,
        }
    }

    #[inline]
    pub fn contains(&self, x: f32, y: f32, z: f32) -> bool {
        self.geometry.contains(x, y, z)
    }
}
