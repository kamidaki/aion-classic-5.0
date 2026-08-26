use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TeleportType {
    Flight,
    Portal,
    Statue,
    Direct,
}

#[derive(Debug, Clone)]
pub struct TeleportLocation {
    pub loc_id: u32,
    pub map_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub price: u64,
    pub required_level: u8,
    pub required_race: Option<u8>, // 0: Elyos, 1: Asmodian
}

#[derive(Debug, Clone, Default)]
pub struct TeleportService {
    pub locations: HashMap<u32, TeleportLocation>,
}

impl TeleportService {
    pub fn new() -> Self {
        let mut locations = HashMap::new();

        // 1. Sanctum Teleport Locations (Wire captured: 1352.14, 1514.12, 569.04, heading 90)
        locations.insert(
            1,
            TeleportLocation {
                loc_id: 1,
                map_id: 110010000, // Sanctum
                x: 1352.14,
                y: 1514.12,
                z: 569.04,
                heading: 90,
                price: 120,
                required_level: 10,
                required_race: Some(0),
            },
        );
        locations.insert(
            100001,
            TeleportLocation {
                loc_id: 100001,
                map_id: 110010000,
                x: 1352.14,
                y: 1514.12,
                z: 569.04,
                heading: 90,
                price: 0,
                required_level: 1,
                required_race: Some(0),
            },
        );

        // 2. Pandaemonium Teleport Locations (Wire captured: 1649.59, 1399.40, 194.40, heading 0)
        locations.insert(
            2,
            TeleportLocation {
                loc_id: 2,
                map_id: 120010000, // Pandaemonium
                x: 1649.59,
                y: 1399.40,
                z: 194.40,
                heading: 0,
                price: 120,
                required_level: 10,
                required_race: Some(1),
            },
        );
        locations.insert(
            200001,
            TeleportLocation {
                loc_id: 200001,
                map_id: 120010000,
                x: 1649.59,
                y: 1399.40,
                z: 194.40,
                heading: 0,
                price: 0,
                required_level: 1,
                required_race: Some(1),
            },
        );

        // 3. Poeta (Akarios Village)
        locations.insert(
            11,
            TeleportLocation {
                loc_id: 11,
                map_id: 210010000,
                x: 820.0,
                y: 1240.0,
                z: 118.0,
                heading: 0,
                price: 50,
                required_level: 1,
                required_race: Some(0),
            },
        );

        // 4. Ishalgen (Aldelle Village)
        locations.insert(
            12,
            TeleportLocation {
                loc_id: 12,
                map_id: 220010000,
                x: 575.0,
                y: 2530.0,
                z: 280.0,
                heading: 0,
                price: 50,
                required_level: 1,
                required_race: Some(1),
            },
        );

        // 5. Reshanta / Core Abyss
        locations.insert(
            50,
            TeleportLocation {
                loc_id: 50,
                map_id: 400010000,
                x: 2150.0,
                y: 1980.0,
                z: 2850.0,
                heading: 0,
                price: 1500,
                required_level: 25,
                required_race: None,
            },
        );

        // 6. Kaisinel Academy (Elyos Intro/Tutorial)
        locations.insert(
            101,
            TeleportLocation {
                loc_id: 101,
                map_id: 110070000,
                x: 457.0,
                y: 251.0,
                z: 127.04,
                heading: 0,
                price: 0,
                required_level: 1,
                required_race: Some(0),
            },
        );

        // 7. Asmodae Intro (Asmodian Intro/Tutorial)
        locations.insert(
            102,
            TeleportLocation {
                loc_id: 102,
                map_id: 120070000,
                x: 457.0,
                y: 251.0,
                z: 127.04,
                heading: 0,
                price: 0,
                required_level: 1,
                required_race: Some(1),
            },
        );

        Self { locations }
    }

    pub fn create_teleport_packet(
        loc: &TeleportLocation,
        instance_id: u32,
    ) -> crate::message::server::RequestTeleport {
        crate::message::server::RequestTeleport::new(
            1, // zone teleport
            loc.map_id,
            instance_id,
            loc.x,
            loc.y,
            loc.z,
            loc.heading,
        )
    }

    pub fn validate_and_teleport(
        &self,
        loc_id: u32,
        player_level: u8,
        player_race: u8,
        player_kinah: u64,
    ) -> Result<(&TeleportLocation, u64), &'static str> {
        let loc = self.locations.get(&loc_id).ok_or("Local de teleporte desconhecido")?;

        if player_level < loc.required_level {
            return Err("Nivel insuficiente para este destino");
        }

        if let Some(req_race) = loc.required_race {
            if req_race != player_race {
                return Err("Destino exclusivo da faccao oposta");
            }
        }

        if player_kinah < loc.price {
            return Err("Kinah insuficiente para transporte");
        }

        let remaining = player_kinah - loc.price;
        Ok((loc, remaining))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_teleport_validation() {
        let tp = TeleportService::new();

        // 1. Teleporte valido para Sanctum
        let (loc, remaining) = tp
            .validate_and_teleport(1, 15, 0, 5000)
            .expect("deve permitir teleporte");
        assert_eq!(loc.map_id, 110010000);
        assert_eq!(remaining, 4880);

        // 2. Faccão errada (Asmodian tentando ir pra Sanctum)
        assert!(tp.validate_and_teleport(1, 15, 1, 5000).is_err());

        // 3. Level insuficiente
        assert!(tp.validate_and_teleport(1, 5, 0, 5000).is_err());

        // 4. Kinah insuficiente
        assert!(tp.validate_and_teleport(1, 15, 0, 50).is_err());
    }
}
