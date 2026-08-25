//! Objetos Interativos, Kisks, Portas Estáticas, Windstreams e Clima

use super::engine::Coord;

#[derive(Debug, Clone)]
pub struct Kisk {
    pub kisk_id: u32,
    pub owner_id: u32,
    pub location: Coord,
    pub max_resurrections: u16,
    pub current_resurrections: u16,
    pub expires_at_tick: u64,
    pub hp: i32,
    pub max_hp: i32,
    pub bound_players: Vec<u32>,
}

impl Kisk {
    pub fn new(kisk_id: u32, owner_id: u32, location: Coord, max_res: u16, duration_ticks: u64, current_tick: u64) -> Self {
        Self {
            kisk_id,
            owner_id,
            location,
            max_resurrections: max_res,
            current_resurrections: 0,
            expires_at_tick: current_tick + duration_ticks,
            hp: 20000,
            max_hp: 20000,
            bound_players: vec![owner_id],
        }
    }

    pub fn is_active(&self, current_tick: u64) -> bool {
        self.hp > 0 && self.current_resurrections < self.max_resurrections && current_tick < self.expires_at_tick
    }

    pub fn bind_player(&mut self, player_id: u32, max_bound: usize) -> bool {
        if self.bound_players.len() < max_bound && !self.bound_players.contains(&player_id) {
            self.bound_players.push(player_id);
            true
        } else {
            false
        }
    }

    pub fn use_resurrection(&mut self, player_id: u32, current_tick: u64) -> Option<Coord> {
        if self.is_active(current_tick) && self.bound_players.contains(&player_id) {
            self.current_resurrections += 1;
            Some(self.location)
        } else {
            None
        }
    }
}

#[derive(Debug, Clone)]
pub struct StaticDoor {
    pub door_id: u32,
    pub map_id: u32,
    pub location: Coord,
    pub is_open: bool,
    pub required_key_id: Option<u32>,
}

impl StaticDoor {
    pub fn new(door_id: u32, map_id: u32, location: Coord, required_key_id: Option<u32>) -> Self {
        Self {
            door_id,
            map_id,
            location,
            is_open: false,
            required_key_id,
        }
    }

    pub fn try_toggle(&mut self, player_keys: &[u32]) -> bool {
        if let Some(req_key) = self.required_key_id {
            if !player_keys.contains(&req_key) {
                return false;
            }
        }

        self.is_open = !self.is_open;
        true
    }
}

#[derive(Debug, Clone)]
pub struct Windstream {
    pub stream_id: u32,
    pub map_id: u32,
    pub waypoints: Vec<Coord>,
}

impl Windstream {
    pub fn new(stream_id: u32, map_id: u32, waypoints: Vec<Coord>) -> Self {
        Self {
            stream_id,
            map_id,
            waypoints,
        }
    }

    pub fn get_waypoint(&self, step: usize) -> Option<Coord> {
        self.waypoints.get(step).copied()
    }
}

#[derive(Debug, Clone)]
pub struct WindstreamService {
    pub streams: std::collections::HashMap<u32, Windstream>,
}

impl Default for WindstreamService {
    fn default() -> Self {
        Self::new()
    }
}

impl WindstreamService {
    pub fn new() -> Self {
        let mut streams = std::collections::HashMap::new();
        // Inggison Windstream 1
        streams.insert(
            1,
            Windstream::new(
                1,
                210050000,
                vec![
                    Coord::new(1300.0, 1400.0, 300.0),
                    Coord::new(1350.0, 1450.0, 320.0),
                    Coord::new(1400.0, 1500.0, 310.0),
                    Coord::new(1450.0, 1550.0, 290.0),
                ],
            ),
        );
        // Gelkmaros Windstream 2
        streams.insert(
            2,
            Windstream::new(
                2,
                220050000,
                vec![
                    Coord::new(1600.0, 1700.0, 350.0),
                    Coord::new(1650.0, 1750.0, 370.0),
                    Coord::new(1700.0, 1800.0, 360.0),
                ],
            ),
        );
        Self { streams }
    }

    pub fn get_stream(&self, stream_id: u32) -> Option<&Windstream> {
        self.streams.get(&stream_id)
    }

    pub fn get_waypoints(&self, stream_id: u32) -> Option<Vec<(f32, f32, f32)>> {
        self.streams.get(&stream_id).map(|s| {
            s.waypoints.iter().map(|c| (c.x(), c.y(), c.z())).collect()
        })
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WeatherCondition {
    Clear = 0,
    LightRain = 1,
    Thunderstorm = 2,
    Snow = 3,
    VolcanicAsh = 4,
    VoidFog = 5,
}

pub struct WeatherService;

impl WeatherService {
    pub fn get_weather(map_id: u32, tick: u64) -> WeatherCondition {
        // Clima determinístico por zona e ciclo de 10.000 ticks
        let phase = (tick / 1000) % 4;
        match map_id {
            210040000 => { // Heiron
                if phase == 1 { WeatherCondition::LightRain } else { WeatherCondition::Clear }
            }
            220040000 => { // Beluslan
                if phase == 2 { WeatherCondition::Snow } else { WeatherCondition::Clear }
            }
            400010000 => WeatherCondition::VoidFog, // Reshanta Abyss
            _ => WeatherCondition::Clear,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kisk_binding_and_resurrection_limits() {
        let mut kisk = Kisk::new(
            1,
            10,
            Coord::new(200.0, 300.0, 50.0),
            2,
            5000,
            100,
        );

        assert!(kisk.bind_player(20, 6));
        assert_eq!(kisk.bound_players.len(), 2);

        // Player 20 resurrects
        assert_eq!(kisk.use_resurrection(20, 200), Some(Coord::new(200.0, 300.0, 50.0)));
        assert_eq!(kisk.current_resurrections, 1);

        // Player 10 resurrects (reaches limit of 2)
        assert_eq!(kisk.use_resurrection(10, 300), Some(Coord::new(200.0, 300.0, 50.0)));
        assert_eq!(kisk.current_resurrections, 2);

        // Third attempt fails because limit is exhausted
        assert_eq!(kisk.use_resurrection(20, 400), None);
        assert!(!kisk.is_active(400));
    }

    #[test]
    fn static_door_key_unlock() {
        let mut locked_door = StaticDoor::new(
            101,
            300040000,
            Coord::new(10.0, 10.0, 0.0),
            Some(185000001), // Requires Temple Key
        );

        // Attempt open without key
        assert!(!locked_door.try_toggle(&[]));
        assert!(!locked_door.is_open);

        // Attempt open with key
        assert!(locked_door.try_toggle(&[185000001]));
        assert!(locked_door.is_open);
    }

    #[test]
    fn windstream_waypoints_and_weather() {
        let stream = Windstream::new(
            1,
            210050000,
            vec![
                Coord::new(0.0, 0.0, 10.0),
                Coord::new(50.0, 50.0, 20.0),
                Coord::new(100.0, 100.0, 30.0),
            ],
        );

        assert_eq!(stream.get_waypoint(0), Some(Coord::new(0.0, 0.0, 10.0)));
        assert_eq!(stream.get_waypoint(2), Some(Coord::new(100.0, 100.0, 30.0)));
        assert_eq!(stream.get_waypoint(5), None);

        assert_eq!(WeatherService::get_weather(400010000, 5000), WeatherCondition::VoidFog);
    }
}
