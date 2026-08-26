#[cfg(test)]
mod tests {
    use std::sync::Arc;
    use crate::geoengine::{GeoConfig, GeoEngine};
    use crate::world::environment::{WeatherManager, WeatherType};
    use crate::world::map::{MapType, WorldMap, WorldMapInstance};
    use crate::world::objects::Creature;
    use crate::world::region::{RegionGrid, RegionStreaming};
    use crate::world::types::{Heading, Point3D, WorldPosition};
    use crate::world::zone::{Zone, ZoneGeometry, ZoneService, ZoneType};
    use crate::world::WorldService;

    #[test]
    fn test_point3d_and_heading() {
        let p1 = Point3D::new(0.0, 0.0, 0.0);
        let p2 = Point3D::new(3.0, 4.0, 0.0);
        assert_eq!(p1.distance_to(&p2), 5.0);
        assert_eq!(p1.distance_2d_to(&p2), 5.0);

        let h = Heading::calculate_heading_to(0.0, 0.0, 10.0, 0.0);
        assert_eq!(h.0, 0); // pointing east
    }

    #[test]
    fn test_region_grid_partition_and_streaming() {
        let grid = RegionGrid::new(210010000, 3072.0, 128.0);
        assert_eq!(grid.grid_width, 24);
        assert_eq!(grid.grid_height, 24);
        assert_eq!(grid.regions.len(), 576);

        let (gx, gy) = grid.get_region_coords(130.0, 260.0);
        assert_eq!(gx, 1);
        assert_eq!(gy, 2);

        let surrounding = grid.get_surrounding_regions(130.0, 260.0);
        assert_eq!(surrounding.len(), 9);

        // Edge test: corner (0, 0) has 4 surrounding regions
        let corner_surrounding = grid.get_surrounding_regions(10.0, 10.0);
        assert_eq!(corner_surrounding.len(), 4);
    }

    #[test]
    fn test_zone_service_containment() {
        let zs = ZoneService::new();

        let safe_zone = Zone::new(
            1,
            "Akarios_Village_Safe".to_string(),
            210010000,
            ZoneType::Safe,
            ZoneGeometry::Cylinder {
                center: crate::geoengine::math::Vector3f::new(500.0, 500.0, 100.0),
                radius: 50.0,
                bottom_z: 80.0,
                top_z: 150.0,
            },
            10,
        );

        let no_fly_zone = Zone::new(
            2,
            "No_Fly_Zone".to_string(),
            210010000,
            ZoneType::NoFly,
            ZoneGeometry::Box {
                min: crate::geoengine::math::Vector3f::new(400.0, 400.0, 0.0),
                max: crate::geoengine::math::Vector3f::new(600.0, 600.0, 300.0),
            },
            5,
        );

        zs.register_zone(safe_zone);
        zs.register_zone(no_fly_zone);

        // Point inside safe zone
        assert!(zs.is_in_zone(210010000, 500.0, 500.0, 100.0, ZoneType::Safe));
        assert!(!zs.is_pvp_allowed(210010000, 500.0, 500.0, 100.0, true)); // Safe zone overrides pvp

        // NoFly zone overrides fly default
        assert!(!zs.is_fly_allowed(210010000, 500.0, 500.0, 100.0, true));

        // Outside zones
        assert!(!zs.is_in_zone(210010000, 1000.0, 1000.0, 100.0, ZoneType::Safe));
        assert!(zs.is_pvp_allowed(210010000, 1000.0, 1000.0, 100.0, true));
    }

    #[test]
    fn test_world_service_integration() {
        let geo_engine = Arc::new(GeoEngine::new(GeoConfig::default()));
        let world_service = WorldService::new(geo_engine);

        world_service.register_map(
            210010000,
            "Poeta".to_string(),
            MapType::Standard,
            3072.0,
            false,
            false,
        );

        let poeta = world_service.get_map(210010000);
        assert!(poeta.is_some());
        let poeta_map = poeta.unwrap();
        assert_eq!(poeta_map.name, "Poeta");

        let inst = world_service.get_instance(210010000, 1);
        assert!(inst.is_some());

        // Weather check
        assert_eq!(world_service.weather_manager().get_weather(210010000), WeatherType::Clear);
        world_service.weather_manager().set_weather(210010000, WeatherType::Rain);
        assert_eq!(world_service.weather_manager().get_weather(210010000), WeatherType::Rain);
    }
}
