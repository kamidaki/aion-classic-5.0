use std::collections::HashMap;
use std::sync::Arc;
use super::region::Region;

pub struct RegionGrid {
    pub map_id: u32,
    pub cell_size: f32,
    pub grid_width: u32,
    pub grid_height: u32,
    pub regions: HashMap<u32, Arc<Region>>,
}

impl RegionGrid {
    pub fn new(map_id: u32, map_size: f32, cell_size: f32) -> Self {
        let grid_width = (map_size / cell_size).ceil() as u32;
        let grid_height = (map_size / cell_size).ceil() as u32;
        let mut regions = HashMap::new();

        for gy in 0..grid_height {
            for gx in 0..grid_width {
                let region_id = gy * grid_width + gx;
                regions.insert(region_id, Arc::new(Region::new(region_id, gx, gy)));
            }
        }

        Self {
            map_id,
            cell_size,
            grid_width,
            grid_height,
            regions,
        }
    }

    #[inline]
    pub fn get_region_coords(&self, x: f32, y: f32) -> (u32, u32) {
        let gx = ((x / self.cell_size).floor() as i32).clamp(0, (self.grid_width - 1) as i32) as u32;
        let gy = ((y / self.cell_size).floor() as i32).clamp(0, (self.grid_height - 1) as i32) as u32;
        (gx, gy)
    }

    #[inline]
    pub fn get_region_id(&self, x: f32, y: f32) -> u32 {
        let (gx, gy) = self.get_region_coords(x, y);
        gy * self.grid_width + gx
    }

    pub fn get_region(&self, region_id: u32) -> Option<&Arc<Region>> {
        self.regions.get(&region_id)
    }

    pub fn get_region_at(&self, x: f32, y: f32) -> Option<&Arc<Region>> {
        let rid = self.get_region_id(x, y);
        self.get_region(rid)
    }

    /// Returns the 3x3 neighboring regions surrounding the given (x, y) coordinates.
    pub fn get_surrounding_regions(&self, x: f32, y: f32) -> Vec<Arc<Region>> {
        let (gx, gy) = self.get_region_coords(x, y);
        let mut result = Vec::with_capacity(9);

        let min_x = if gx > 0 { gx - 1 } else { 0 };
        let max_x = (gx + 1).min(self.grid_width - 1);
        let min_y = if gy > 0 { gy - 1 } else { 0 };
        let max_y = (gy + 1).min(self.grid_height - 1);

        for y_idx in min_y..=max_y {
            for x_idx in min_x..=max_x {
                let rid = y_idx * self.grid_width + x_idx;
                if let Some(reg) = self.regions.get(&rid) {
                    result.push(reg.clone());
                }
            }
        }

        result
    }
}
