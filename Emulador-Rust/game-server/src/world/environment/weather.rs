use std::collections::HashMap;
use std::sync::RwLock;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WeatherType {
    Clear = 0,
    Cloudy = 1,
    Rain = 2,
    Snow = 3,
    SandStorm = 4,
    Fog = 5,
}

pub struct WeatherManager {
    weather_map: RwLock<HashMap<u32, WeatherType>>,
}

impl WeatherManager {
    pub fn new() -> Self {
        Self {
            weather_map: RwLock::new(HashMap::new()),
        }
    }

    pub fn get_weather(&self, map_id: u32) -> WeatherType {
        let guard = self.weather_map.read().unwrap();
        guard.get(&map_id).copied().unwrap_or(WeatherType::Clear)
    }

    pub fn set_weather(&self, map_id: u32, weather: WeatherType) {
        let mut guard = self.weather_map.write().unwrap();
        guard.insert(map_id, weather);
    }
}
