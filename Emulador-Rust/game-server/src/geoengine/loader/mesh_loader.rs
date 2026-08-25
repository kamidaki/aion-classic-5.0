use std::collections::HashMap;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::Path;

use crate::geoengine::collision::CollisionIntention;
use crate::geoengine::math::Vector3f;
use crate::geoengine::models::{DoorGeometry, Geometry, Mesh, Node, Spatial};

pub struct MeshLoader;

impl MeshLoader {
    pub fn load_meshes<P: AsRef<Path>>(file_path: P) -> std::io::Result<HashMap<String, Spatial>> {
        let file = File::open(file_path)?;
        let mut reader = BufReader::with_capacity(1024 * 1024, file);
        let mut geoms: HashMap<String, Spatial> = HashMap::new();

        let mut buffer = Vec::new();
        reader.read_to_end(&mut buffer)?;

        let mut offset = 0usize;
        let total_len = buffer.len();

        macro_rules! read_i16 {
            () => {{
                if offset + 2 > total_len {
                    break;
                }
                let val = i16::from_le_bytes([buffer[offset], buffer[offset + 1]]);
                offset += 2;
                val
            }};
        }

        macro_rules! read_u16 {
            () => {{
                if offset + 2 > total_len {
                    break;
                }
                let val = u16::from_le_bytes([buffer[offset], buffer[offset + 1]]);
                offset += 2;
                val
            }};
        }

        macro_rules! read_i32 {
            () => {{
                if offset + 4 > total_len {
                    break;
                }
                let val = i32::from_le_bytes([
                    buffer[offset],
                    buffer[offset + 1],
                    buffer[offset + 2],
                    buffer[offset + 3],
                ]);
                offset += 4;
                val
            }};
        }

        macro_rules! read_f32 {
            () => {{
                if offset + 4 > total_len {
                    break;
                }
                let val = f32::from_le_bytes([
                    buffer[offset],
                    buffer[offset + 1],
                    buffer[offset + 2],
                    buffer[offset + 3],
                ]);
                offset += 4;
                val
            }};
        }

        while offset < total_len {
            let name_len = read_i16!() as usize;
            if offset + name_len > total_len {
                break;
            }
            let name = String::from_utf8_lossy(&buffer[offset..offset + name_len]).to_string();
            offset += name_len;

            let mut node = Node::new(name.clone());
            let mut intentions = CollisionIntention::NONE;
            let mut single_child_material_id = 0u8;

            let model_count = read_i16!() as usize;
            for c in 0..model_count {
                let vertex_float_count = (read_i32!() * 3) as usize;
                let mut vertices = Vec::with_capacity(vertex_float_count / 3);
                for _ in 0..(vertex_float_count / 3) {
                    let x = read_f32!();
                    let y = read_f32!();
                    let z = read_f32!();
                    vertices.push(Vector3f::new(x, y, z));
                }

                let triangle_indices_count = read_i32!() as usize;
                let mut indices = Vec::with_capacity(triangle_indices_count);
                for _ in 0..triangle_indices_count {
                    indices.push(read_u16!());
                }

                let collision_flags = read_u16!();
                let mesh = Mesh::new(vertices, indices, collision_flags);

                if mesh.intentions.contains(CollisionIntention::MOVEABLE) {
                    // Skip moveable meshes (dynamic ships, moveable props)
                    continue;
                }

                intentions |= mesh.intentions;
                single_child_material_id = mesh.material_id;

                let geom_name = if model_count == 1 {
                    name.clone()
                } else {
                    format!("child{}_{}", c, name)
                };

                let geom = Geometry::new(geom_name.clone(), mesh);

                if (intentions.0 & CollisionIntention::DOOR.0) != 0
                    && (intentions.0 & CollisionIntention::PHYSICAL.0) != 0
                {
                    let door = DoorGeometry::new(name.clone(), geom.clone());
                    geoms.insert(name.to_lowercase(), Spatial::Door(door));
                } else {
                    geoms.insert(geom_name.to_lowercase(), Spatial::Geom(geom.clone()));
                    node.attach_child(Spatial::Geom(geom));
                }
            }

            node.set_collision_flags(((intentions.0 as u16) << 8) | (single_child_material_id as u16));
            if !node.children.is_empty() {
                geoms.insert(name.to_lowercase(), Spatial::NodeSpatial(node));
            }
        }

        Ok(geoms)
    }
}
