use crate::geoengine::bounding::BoundingBox;

#[derive(Debug, Clone)]
pub struct MaterialZone {
    pub zone_name: String,
    pub world_id: u32,
    pub region_id: u32,
    pub material_id: u8,
    pub bounding_box: BoundingBox,
}

impl MaterialZone {
    pub fn new(
        zone_name: String,
        world_id: u32,
        region_id: u32,
        material_id: u8,
        bounding_box: BoundingBox,
    ) -> Self {
        Self {
            zone_name,
            world_id,
            region_id,
            material_id,
            bounding_box,
        }
    }
}
