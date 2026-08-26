use std::collections::HashSet;

#[derive(Debug, Clone, Default)]
pub struct Terrain {
    pub data: Vec<i16>,
    pub size: usize,
    pub width_samples: usize,
    pub height_samples: usize,
    pub cutouts: HashSet<u32>,
    pub base_height: f32,
    pub height_scale: f32,
}

impl Terrain {
    pub fn new(data: Vec<i16>, cutouts: Vec<u32>) -> Self {
        let size = data.len();
        // Aion maps are typically square grids (e.g. 512x512, 1024x1024, 1536x1536, 2048x2048)
        let side = (size as f64).sqrt().round() as usize;
        let cutout_set: HashSet<u32> = cutouts.into_iter().collect();

        Self {
            data,
            size,
            width_samples: side,
            height_samples: side,
            cutouts: cutout_set,
            base_height: 0.0,
            height_scale: 0.03125, // 1/32 scale factor standard for Aion heightmaps
        }
    }

    pub fn is_cutout(&self, grid_x: usize, grid_y: usize) -> bool {
        if self.width_samples == 0 {
            return false;
        }
        // Mesma ordem do heightmap (ver `get_height`). NAO foi medido em separado: os buracos
        // sao poucos (48 em Poeta) e nenhuma das posicoes de referencia cai em cima de um.
        let index = (grid_x * self.width_samples + grid_y) as u32;
        self.cutouts.contains(&index)
    }

    /// Gets exact interpolated terrain height at world coordinates (x, y).
    /// Map coordinates typically span 0.0 to 3072.0 or 2048.0.
    pub fn get_height(&self, x: f32, y: f32, map_size: f32) -> Option<f32> {
        if self.data.is_empty() || self.width_samples <= 1 || self.height_samples <= 1 {
            return if !self.data.is_empty() {
                Some(self.data[0] as f32 * self.height_scale)
            } else {
                None
            };
        }

        if x < 0.0 || x >= map_size || y < 0.0 || y >= map_size {
            return None;
        }

        // Normalize coordinates to grid sample coordinates
        let norm_x = (x / map_size) * (self.width_samples - 1) as f32;
        let norm_y = (y / map_size) * (self.height_samples - 1) as f32;

        let x0 = norm_x.floor() as usize;
        let y0 = norm_y.floor() as usize;
        let x1 = (x0 + 1).min(self.width_samples - 1);
        let y1 = (y0 + 1).min(self.height_samples - 1);

        if self.is_cutout(x0, y0) {
            return None; // Terrain hole
        }

        let frac_x = norm_x - (x0 as f32);
        let frac_y = norm_y - (y0 as f32);

        // O array do `.geo` e indexado por **x primeiro**: `data[x * lado + y]`.
        //
        // Medido contra as 992 posicoes de NPC do `210010000_Poeta.xml` (spawn oficial do Java
        // EMU, NPC parado no chao). Com `y * lado + x` a mediana do erro de altura e 24,5m e so
        // 18 dos 992 caem dentro de 1m; com `x * lado + y` a mediana e 0,10m e 912 dos 992 caem
        // dentro de 1m. Os ~80 restantes sao NPC em plataforma, ponte ou interior.
        let idx00 = x0 * self.width_samples + y0;
        let idx10 = x1 * self.width_samples + y0;
        let idx01 = x0 * self.width_samples + y1;
        let idx11 = x1 * self.width_samples + y1;

        if idx11 >= self.data.len() {
            return None;
        }

        let h00 = self.data[idx00] as f32 * self.height_scale;
        let h10 = self.data[idx10] as f32 * self.height_scale;
        let h01 = self.data[idx01] as f32 * self.height_scale;
        let h11 = self.data[idx11] as f32 * self.height_scale;

        // Bilinear interpolation
        let top = h00 * (1.0 - frac_x) + h10 * frac_x;
        let bottom = h01 * (1.0 - frac_x) + h11 * frac_x;
        let final_h = top * (1.0 - frac_y) + bottom * frac_y;

        Some(final_h)
    }
}
