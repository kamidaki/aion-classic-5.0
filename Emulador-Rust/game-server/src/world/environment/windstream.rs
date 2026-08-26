use crate::geoengine::math::Vector3f;

#[derive(Debug, Clone)]
pub struct WindstreamPath {
    pub map_id: u32,
    pub stream_id: u32,
    pub bidirectional: bool,
    pub waypoints: Vec<Vector3f>,
}

impl WindstreamPath {
    pub fn new(map_id: u32, stream_id: u32, bidirectional: bool, waypoints: Vec<Vector3f>) -> Self {
        Self {
            map_id,
            stream_id,
            bidirectional,
            waypoints,
        }
    }
}
