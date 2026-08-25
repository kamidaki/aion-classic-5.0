use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct GeoConfig {
    pub geo_dir: PathBuf,
    pub enable_collision: bool,
    pub enable_doors: bool,
    pub enable_materials: bool,
    pub debug_mode: bool,
}

impl Default for GeoConfig {
    fn default() -> Self {
        Self {
            geo_dir: PathBuf::from("data/Geo"),
            enable_collision: true,
            enable_doors: true,
            enable_materials: true,
            debug_mode: false,
        }
    }
}
