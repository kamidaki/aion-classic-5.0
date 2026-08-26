use std::collections::HashSet;
use super::grid::RegionGrid;

pub struct RegionStreaming;

impl RegionStreaming {
    /// Computes which entities entered and left the player's 3x3 surrounding visual area
    /// when transitioning from (old_x, old_y) to (new_x, new_y).
    pub fn compute_visibility_diff(
        grid: &RegionGrid,
        old_x: f32,
        old_y: f32,
        new_x: f32,
        new_y: f32,
    ) -> (Vec<u32>, Vec<u32>) {
        let old_regions = grid.get_surrounding_regions(old_x, old_y);
        let new_regions = grid.get_surrounding_regions(new_x, new_y);

        let mut old_players = HashSet::new();
        for r in &old_regions {
            for p in r.get_players() {
                old_players.insert(p);
            }
        }

        let mut new_players = HashSet::new();
        for r in &new_regions {
            for p in r.get_players() {
                new_players.insert(p);
            }
        }

        let entered: Vec<u32> = new_players.difference(&old_players).copied().collect();
        let left: Vec<u32> = old_players.difference(&new_players).copied().collect();

        (entered, left)
    }
}
