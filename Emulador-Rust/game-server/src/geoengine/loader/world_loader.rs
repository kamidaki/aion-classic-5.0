use std::collections::HashMap;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::Path;

use crate::geoengine::math::{Matrix3f, Vector3f};
use crate::geoengine::models::{GeoMap, Spatial, Terrain};

pub struct WorldLoader;

impl WorldLoader {
    pub fn load_world<P: AsRef<Path>>(
        world_id: u32,
        file_path: P,
        models: &HashMap<String, Spatial>,
    ) -> std::io::Result<GeoMap> {
        let file = File::open(file_path)?;
        let mut reader = BufReader::with_capacity(1024 * 1024, file);
        let mut buffer = Vec::new();
        reader.read_to_end(&mut buffer)?;

        let mut offset = 0usize;
        let total_len = buffer.len();
        let mut geo_map = GeoMap::new(world_id);

        macro_rules! read_u8 {
            () => {{
                if offset >= total_len {
                    return Ok(geo_map);
                }
                let val = buffer[offset];
                offset += 1;
                val
            }};
        }

        macro_rules! read_i16 {
            () => {{
                if offset + 2 > total_len {
                    return Ok(geo_map);
                }
                let val = i16::from_le_bytes([buffer[offset], buffer[offset + 1]]);
                offset += 2;
                val
            }};
        }

        macro_rules! read_i32 {
            () => {{
                if offset + 4 > total_len {
                    return Ok(geo_map);
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
                    return Ok(geo_map);
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

        let has_terrain = read_u8!();
        if has_terrain == 0 {
            let default_val = read_i16!();
            let _cutout_size = read_i32!();
            geo_map.set_terrain(Terrain::new(vec![default_val], vec![]));
        } else {
            let size = read_i32!() as usize;
            let mut terrain_data = Vec::with_capacity(size);
            for _ in 0..size {
                terrain_data.push(read_i16!());
            }

            let cutout_size = read_i32!() as usize;
            let mut cutouts = Vec::with_capacity(cutout_size);
            for _ in 0..cutout_size {
                cutouts.push(read_i32!() as u32);
            }

            geo_map.set_terrain(Terrain::new(terrain_data, cutouts));
        }

        while offset < total_len {
            let name_len = read_i16!() as usize;
            if offset + name_len > total_len {
                break;
            }
            let name = String::from_utf8_lossy(&buffer[offset..offset + name_len]).to_string();
            offset += name_len;

            let loc_x = read_f32!();
            let loc_y = read_f32!();
            let loc_z = read_f32!();
            let location = Vector3f::new(loc_x, loc_y, loc_z);

            let mut matrix_arr = [0.0f32; 9];
            for i in 0..9 {
                matrix_arr[i] = read_f32!();
            }
            let rot_matrix = Matrix3f::from_array(&matrix_arr);

            let scale = read_f32!();
            let _event_type = read_u8!();

            let lookup_key = name.to_lowercase();
            if let Some(template_node) = models.get(&lookup_key) {
                let mut instance_clone = template_node.clone();
                instance_clone.set_transform(&rot_matrix, &location, scale);
                geo_map.attach_child(instance_clone);
            }
        }

        geo_map.update_model_bound();
        Ok(geo_map)
    }
}
