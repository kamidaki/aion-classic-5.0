use super::spatial::{Node, Spatial};
use super::terrain::Terrain;
use crate::geoengine::collision::{CollisionIntention, CollisionResults};
use crate::geoengine::math::{Ray, Vector3f};

#[derive(Debug, Clone)]
pub struct GeoMap {
    pub world_id: u32,
    pub map_size: f32,
    pub terrain: Option<Terrain>,
    pub root_node: Node,
}

impl GeoMap {
    pub fn new(world_id: u32) -> Self {
        Self {
            world_id,
            map_size: 3072.0, // reserva: `set_terrain` corrige pelo tamanho do heightmap
            terrain: None,
            root_node: Node::new(format!("World_{}", world_id)),
        }
    }

    /// O tamanho do mapa sai do proprio heightmap: **dois metros por amostra**.
    ///
    /// Ficava fixo em 3072, que e o valor certo para os mapas de 1536 amostras -- a maioria -- e
    /// errado para todos os outros. Medido contra as posicoes de NPC dos XMLs de spawn do Java EMU:
    ///
    /// ```text
    /// 210070000 Telos Elyos      1024 amostras   ms=2048: 88,5%   ms=3072:  1,2%
    /// 220080000 Telos Asmodians  1024 amostras   ms=2048: 88,5%   ms=3072:  1,2%
    /// 600010000 Silentera        768 amostras    ms=1536: 41,2%   ms=3072:  1,4%
    /// ```
    ///
    /// (Silentera fica baixo porque e mapa de caverna, com boa parte dos NPCs em tunel e nao no
    /// terreno -- mas 41% contra 1,4% e a mesma resposta.)
    ///
    /// Para os mapas de 1536 nada muda: 1536 * 2 = 3072.
    pub fn set_terrain(&mut self, terrain: Terrain) {
        if terrain.width_samples > 1 {
            self.map_size = (terrain.width_samples * 2) as f32;
        }
        self.terrain = Some(terrain);
    }

    pub fn attach_child(&mut self, child: Spatial) {
        self.root_node.attach_child(child);
    }

    pub fn update_model_bound(&mut self) {
        self.root_node.update_world_bound();
    }

    /// Queries the ground Z coordinate at (x, y).
    /// It checks both the terrain heightmap and physical mesh geometries (bridges, buildings, stairs).
    /// If `current_z` is provided, it finds the best walkable surface nearest to `current_z`.
    pub fn get_z(&self, x: f32, y: f32, current_z: Option<f32>) -> f32 {
        let terrain_z = self.terrain.as_ref().and_then(|t| t.get_height(x, y, self.map_size));

        // Cast a vertical downward ray from high above (or near current_z + 10m)
        let ray_start_z = current_z.unwrap_or(2000.0) + 15.0;
        let ray = Ray::new(
            Vector3f::new(x, y, ray_start_z),
            Vector3f::new(0.0, 0.0, -1.0),
        );

        let mut results = CollisionResults::new();
        self.root_node.collide_ray(
            &ray,
            CollisionIntention::PHYSICAL | CollisionIntention::WALKABLE,
            &mut results,
        );

        let mut best_z = terrain_z.unwrap_or(0.0);

        if !results.is_empty() {
            results.sort_by_distance();
            if let Some(target_z) = current_z {
                // Find surface that is closest above or near target_z (within step height)
                let mut best_diff = f32::MAX;
                for res in &results.results {
                    let z = res.contact_point.z;
                    // Accept if surface is higher than terrain and reasonable
                    let diff = (z - target_z).abs();
                    if diff < best_diff && z >= (terrain_z.unwrap_or(0.0) - 1.0) {
                        best_diff = diff;
                        best_z = z;
                    }
                }
            } else if let Some(first) = results.results.first() {
                if first.contact_point.z > best_z {
                    best_z = first.contact_point.z;
                }
            }
        }

        best_z
    }

    /// Checks line-of-sight between two 3D points.
    /// Returns true if no physical geometry or door blocks the ray.
    pub fn can_see(&self, start: &Vector3f, end: &Vector3f) -> bool {
        let dist = start.distance(end);
        if dist < 0.001 {
            return true;
        }

        let dir = (*end - *start).normalize();
        let ray = Ray::new(*start, dir);

        let mut results = CollisionResults::new();
        self.root_node.collide_ray(
            &ray,
            CollisionIntention::PHYSICAL | CollisionIntention::DOOR,
            &mut results,
        );

        for hit in &results.results {
            if hit.distance < dist - 0.1 && hit.distance > 0.1 {
                return false; // Obstructed by physical mesh or closed door
            }
        }

        true
    }
}
