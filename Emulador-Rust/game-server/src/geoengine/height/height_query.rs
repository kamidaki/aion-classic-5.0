use crate::geoengine::models::GeoMap;

pub struct HeightQuery;

impl HeightQuery {
    pub fn get_z(geo_map: &GeoMap, x: f32, y: f32, current_z: Option<f32>) -> f32 {
        geo_map.get_z(x, y, current_z)
    }
}
