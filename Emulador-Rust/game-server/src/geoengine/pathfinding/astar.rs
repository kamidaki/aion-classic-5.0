use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap, HashSet};
use crate::geoengine::math::Vector3f;
use crate::geoengine::models::GeoMap;

#[derive(Clone, PartialEq)]
struct NodeWrapper {
    pos: Vector3f,
    cost: f32,
    heuristic: f32,
}

impl Eq for NodeWrapper {}

impl Ord for NodeWrapper {
    fn cmp(&self, other: &Self) -> Ordering {
        let f_self = self.cost + self.heuristic;
        let f_other = other.cost + other.heuristic;
        f_other.partial_cmp(&f_self).unwrap_or(Ordering::Equal)
    }
}

impl PartialOrd for NodeWrapper {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

pub struct AStarPathfinder;

impl AStarPathfinder {
    /// Finds a 3D obstacle-free path from start to goal across the GeoMap.
    pub fn find_path(
        geo_map: &GeoMap,
        start: Vector3f,
        goal: Vector3f,
        step_size: f32,
        max_iterations: usize,
    ) -> Option<Vec<Vector3f>> {
        // Direct line check first
        if geo_map.can_see(&start, &goal) {
            let start_ground = geo_map.get_z(start.x, start.y, Some(start.z));
            let goal_ground = geo_map.get_z(goal.x, goal.y, Some(goal.z));
            return Some(vec![
                Vector3f::new(start.x, start.y, start_ground),
                Vector3f::new(goal.x, goal.y, goal_ground),
            ]);
        }

        let mut open_set = BinaryHeap::new();
        let mut came_from: HashMap<[i32; 2], Vector3f> = HashMap::new();
        let mut g_score: HashMap<[i32; 2], f32> = HashMap::new();
        let mut closed_set: HashSet<[i32; 2]> = HashSet::new();

        let quantize = |v: &Vector3f| -> [i32; 2] {
            [(v.x / step_size).round() as i32, (v.y / step_size).round() as i32]
        };

        let start_key = quantize(&start);
        let goal_key = quantize(&goal);

        g_score.insert(start_key, 0.0);
        open_set.push(NodeWrapper {
            pos: start,
            cost: 0.0,
            heuristic: start.distance(&goal),
        });

        let offsets = [
            (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
            (0.707, 0.707), (-0.707, 0.707), (0.707, -0.707), (-0.707, -0.707),
        ];

        let mut iterations = 0;
        let mut closest_node = start;
        let mut min_heuristic = start.distance(&goal);

        while let Some(current) = open_set.pop() {
            let current_key = quantize(&current.pos);

            if current_key == goal_key || current.pos.distance(&goal) <= step_size * 1.5 {
                // Reconstruct path
                let mut path = vec![goal];
                let mut curr_k = current_key;
                while let Some(&prev_pos) = came_from.get(&curr_k) {
                    path.push(prev_pos);
                    curr_k = quantize(&prev_pos);
                }
                path.reverse();
                return Some(path);
            }

            if closed_set.contains(&current_key) {
                continue;
            }
            closed_set.insert(current_key);

            iterations += 1;
            if iterations >= max_iterations {
                break;
            }

            let current_g = *g_score.get(&current_key).unwrap_or(&f32::INFINITY);

            for &(dx, dy) in &offsets {
                let next_x = current.pos.x + dx * step_size;
                let next_y = current.pos.y + dy * step_size;
                let next_z = geo_map.get_z(next_x, next_y, Some(current.pos.z));
                let next_pos = Vector3f::new(next_x, next_y, next_z);

                // Step height check
                if (next_z - current.pos.z).abs() > 3.0 {
                    continue; // Too steep
                }

                // Raycast check between current step and next step
                if !geo_map.can_see(&current.pos, &next_pos) {
                    continue; // Wall/obstacle blocking
                }

                let next_key = quantize(&next_pos);
                if closed_set.contains(&next_key) {
                    continue;
                }

                let tentative_g = current_g + current.pos.distance(&next_pos);
                if tentative_g < *g_score.get(&next_key).unwrap_or(&f32::INFINITY) {
                    came_from.insert(next_key, current.pos);
                    g_score.insert(next_key, tentative_g);

                    let h = next_pos.distance(&goal);
                    if h < min_heuristic {
                        min_heuristic = h;
                        closest_node = next_pos;
                    }

                    open_set.push(NodeWrapper {
                        pos: next_pos,
                        cost: tentative_g,
                        heuristic: h,
                    });
                }
            }
        }

        // Return best-effort partial path to closest node if goal not reached
        if closest_node != start {
            let mut path = vec![closest_node];
            let mut curr_k = quantize(&closest_node);
            while let Some(&prev_pos) = came_from.get(&curr_k) {
                path.push(prev_pos);
                curr_k = quantize(&prev_pos);
            }
            path.reverse();
            return Some(path);
        }

        None
    }
}
