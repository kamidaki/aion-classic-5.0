use std::path::PathBuf;
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct GeoConfig {
    #[serde(default = "default_geo_dir")]
    pub geo_dir: PathBuf,
    #[serde(default = "default_true")]
    pub enable_collision: bool,
    #[serde(default = "default_true")]
    pub enable_doors: bool,
    #[serde(default = "default_true")]
    pub enable_materials: bool,
    #[serde(default = "default_true")]
    pub enable_falldamage: bool,
    #[serde(default = "default_true")]
    pub enable_speedvalidation: bool,
    #[serde(default = "default_false")]
    pub debug_mode: bool,
}

fn default_geo_dir() -> PathBuf {
    PathBuf::from("data/Geo")
}
fn default_true() -> bool {
    true
}
fn default_false() -> bool {
    false
}

impl Default for GeoConfig {
    fn default() -> Self {
        Self {
            geo_dir: default_geo_dir(),
            enable_collision: true,
            enable_doors: true,
            enable_materials: true,
            enable_falldamage: true,
            enable_speedvalidation: true,
            debug_mode: false,
        }
    }
}
