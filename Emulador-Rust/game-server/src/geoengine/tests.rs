#[cfg(test)]
mod tests {
    use std::path::PathBuf;
    use crate::geoengine::bounding::{BoundingBox, BoundingSphere, BoundingVolume};
    use crate::geoengine::collision::{ray_triangle_intersect, CollisionIntention, CollisionResults};
    use crate::geoengine::loader::{GeoConfig, MeshLoader, WorldLoader};
    use crate::geoengine::math::{Matrix3f, Matrix4f, Ray, Vector3f};
    use crate::geoengine::models::{GeoMap, Geometry, Mesh, Terrain};
    use crate::geoengine::movement::{FallDetector, MovementValidator};
    use crate::geoengine::pathfinding::AStarPathfinder;
    use crate::geoengine::GeoEngine;

    #[test]
    fn test_vector3_math() {
        let v1 = Vector3f::new(1.0, 2.0, 3.0);
        let v2 = Vector3f::new(4.0, 5.0, 6.0);
        let sum = v1 + v2;
        assert_eq!(sum, Vector3f::new(5.0, 7.0, 9.0));

        let dot = v1.dot(&v2);
        assert_eq!(dot, 1.0 * 4.0 + 2.0 * 5.0 + 3.0 * 6.0);

        let cross = Vector3f::UNIT_X.cross(&Vector3f::UNIT_Y);
        assert_eq!(cross, Vector3f::UNIT_Z);

        assert_eq!(Vector3f::new(3.0, 4.0, 0.0).length(), 5.0);
    }

    #[test]
    fn test_matrix3_transform() {
        let mut mat = Matrix3f::IDENTITY;
        mat.m00 = 2.0;
        mat.m11 = 2.0;
        mat.m22 = 2.0;
        let v = Vector3f::new(1.0, 2.0, 3.0);
        let transformed = mat.mult(&v);
        assert_eq!(transformed, Vector3f::new(2.0, 4.0, 6.0));
    }

    #[test]
    fn test_moller_trumbore_ray_intersection() {
        let ray = Ray::new(
            Vector3f::new(0.0, 0.0, 10.0),
            Vector3f::new(0.0, 0.0, -1.0),
        );
        let v0 = Vector3f::new(-5.0, -5.0, 0.0);
        let v1 = Vector3f::new(5.0, -5.0, 0.0);
        let v2 = Vector3f::new(0.0, 5.0, 0.0);

        let hit = ray_triangle_intersect(&ray, &v0, &v1, &v2);
        assert!(hit.is_some());
        let (dist, contact, normal) = hit.unwrap();
        assert!((dist - 10.0).abs() < 1e-4);
        assert_eq!(contact, Vector3f::new(0.0, 0.0, 0.0));
        assert!(normal.z > 0.0);
    }

    #[test]
    fn test_bounding_box_and_sphere_intersection() {
        let bbox = BoundingBox::new(
            Vector3f::new(-1.0, -1.0, -1.0),
            Vector3f::new(1.0, 1.0, 1.0),
        );
        let ray_hit = Ray::new(Vector3f::new(0.0, 0.0, -5.0), Vector3f::new(0.0, 0.0, 1.0));
        let ray_miss = Ray::new(Vector3f::new(5.0, 5.0, -5.0), Vector3f::new(0.0, 0.0, 1.0));

        assert!(bbox.intersects_ray(&ray_hit));
        assert!(!bbox.intersects_ray(&ray_miss));

        let sphere = BoundingSphere::new(Vector3f::ZERO, 2.0);
        assert!(sphere.intersects_ray(&ray_hit));
        assert!(!sphere.intersects_ray(&ray_miss));
    }

    #[test]
    fn test_terrain_elevation_interpolation() {
        // 3x3 elevation samples
        let data = vec![
            100, 200, 300,
            400, 500, 600,
            700, 800, 900,
        ];
        let terrain = Terrain::new(data, vec![]);
        assert_eq!(terrain.width_samples, 3);
        assert_eq!(terrain.height_samples, 3);

        // Center of map should interpolate close to sample 500 * 0.03125
        let center_h = terrain.get_height(1536.0, 1536.0, 3072.0);
        assert!(center_h.is_some());
        let expected = 500.0 * 0.03125;
        assert!((center_h.unwrap() - expected).abs() < 0.5);
    }

    #[test]
    fn test_movement_validation_speed_and_step() {
        let mut geo_map = GeoMap::new(210010000);
        let terrain = Terrain::new(vec![3200], vec![]); // height = 3200 * 0.03125 = 100.0m
        geo_map.set_terrain(terrain);

        let curr = Vector3f::new(100.0, 100.0, 100.0);
        let target_valid = Vector3f::new(105.0, 100.0, 100.0); // 5m in 1.0s = 5m/s (valid)
        let res1 = MovementValidator::validate_step(&geo_map, &curr, &target_valid, 1.0, false, false);
        assert!(res1.is_valid);

        let target_teleport = Vector3f::new(200.0, 100.0, 100.0); // 100m in 1.0s (speed hack)
        let res2 = MovementValidator::validate_step(&geo_map, &curr, &target_teleport, 1.0, false, false);
        assert!(!res2.is_valid);
        assert_eq!(res2.reason, Some("SpeedLimitExceeded"));
    }

    #[test]
    fn test_fall_damage() {
        let safe = FallDetector::calculate_fall_damage(8.0, 1000);
        assert_eq!(safe, 0);

        let mid = FallDetector::calculate_fall_damage(30.0, 1000);
        assert!(mid > 0 && mid < 1000);

        let lethal = FallDetector::calculate_fall_damage(55.0, 1000);
        assert_eq!(lethal, 1000);
    }

    #[test]
    fn test_astar_pathfinding() {
        let mut geo_map = GeoMap::new(210010000);
        let terrain = Terrain::new(vec![3200], vec![]);
        geo_map.set_terrain(terrain);

        let start = Vector3f::new(10.0, 10.0, 100.0);
        let goal = Vector3f::new(50.0, 10.0, 100.0);

        let path = AStarPathfinder::find_path(&geo_map, start, goal, 5.0, 100);
        assert!(path.is_some());
        let waypoints = path.unwrap();
        assert!(!waypoints.is_empty());
        assert_eq!(waypoints.first().unwrap().x, 10.0);
        assert_eq!(waypoints.last().unwrap().x, 50.0);
    }

    #[test]
    fn test_real_geo_data_loading_if_present() {
        let geo_dir = PathBuf::from(r"D:\AION RUST\AionEMU\AionEMU\Produto Final\data\Geo");
        if geo_dir.exists() {
            let config = GeoConfig {
                geo_dir: geo_dir.clone(),
                enable_collision: true,
                enable_doors: true,
                enable_materials: true,
                debug_mode: false,
                ..Default::default()
            };
            let engine = GeoEngine::new(config);
            assert!(engine.initialize().is_ok());

            // Load Poeta map 210010000
            let poeta = engine.load_world(210010000);
            assert!(poeta.is_ok());
            let poeta_map = poeta.unwrap();
            assert_eq!(poeta_map.world_id, 210010000);

            // Poeta spawn point query
            let z = engine.get_z(210010000, 1200.0, 1200.0, None);
            println!("Poeta ground Z at (1200, 1200): {}", z);
            assert!(z != 0.0);
        }
    }
}

/// O heightmap do `.geo` bate com o chao onde o jogo poe os NPCs.
///
/// Guarda de regressao da inversao de eixos do heightmap: o array e `data[x * lado + y]`, e por
/// muito tempo foi lido como `data[y * lado + x]`. Nada quebrava de forma visivel no servidor --
/// `get_z` devolvia um numero plausivel -- e o efeito so aparecia no cliente, com o personagem
/// caindo pelo cenario ou nascendo dentro dele.
///
/// A referencia sao as 992 posicoes de NPC do `210010000_Poeta.xml` (spawn oficial do Java EMU).
/// NPC de mundo aberto fica parado no chao, entao a altura dele **e** a altura do terreno. Os
/// outliers aceitos sao os que ficam em plataforma, ponte ou interior.
///
/// Pula sozinho se os dados nao estiverem no lugar -- eles nao sao versionados junto do codigo.
#[test]
fn heightmap_bate_com_o_chao_dos_npcs_de_poeta() {
    use std::path::PathBuf;

    let geo_dir = PathBuf::from("../../Produto Final/data/Geo");
    let xml_path = PathBuf::from(
        "../../Docs-Refs/JAVA EMU - 2.4 CLASSIC EU/AL-Game/data/static_data/spawns/Npcs/210010000_Poeta.xml",
    );
    if !geo_dir.join("210010000.geo").exists() || !xml_path.exists() {
        eprintln!("pulando: dados de referencia ausentes ({}, {})", geo_dir.display(), xml_path.display());
        return;
    }

    let eng = crate::geoengine::GeoEngine::new(crate::geoengine::GeoConfig {
        geo_dir,
        ..Default::default()
    });
    eng.initialize().unwrap();
    let mapa = eng.load_world(210_010_000).unwrap();
    let terreno = mapa.terrain.as_ref().expect("Poeta tem terreno");

    let xml = std::fs::read_to_string(&xml_path).unwrap();
    let mut pontos = Vec::new();
    for linha in xml.lines() {
        let Some(i) = linha.find("<spot x=\"") else { continue };
        let campos: Vec<f32> = linha[i + 9..]
            .split('"')
            .filter_map(|s| s.trim_end_matches(" y=").trim_end_matches(" z=").trim_end_matches(" h=").parse().ok())
            .collect();
        if campos.len() >= 3 {
            pontos.push((campos[0], campos[1], campos[2]));
        }
    }
    assert!(pontos.len() > 900, "o XML de Poeta tem ~992 spots, li {}", pontos.len());

    let mut dentro_de_1m = 0;
    let mut medidos = 0;
    for (x, y, z) in &pontos {
        if let Some(h) = terreno.get_height(*x, *y, mapa.map_size) {
            medidos += 1;
            if (z - h).abs() < 1.0 {
                dentro_de_1m += 1;
            }
        }
    }

    // Com a indexacao certa: 912 de 992. Com os eixos trocados: 18.
    assert!(
        dentro_de_1m * 10 >= medidos * 8,
        "so {dentro_de_1m} de {medidos} NPCs caem dentro de 1m do terreno -- \
         o heightmap provavelmente voltou a ser lido com x e y trocados"
    );
}
