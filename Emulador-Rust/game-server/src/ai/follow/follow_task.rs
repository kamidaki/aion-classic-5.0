//! Tarefa de Perseguição de Invocação / Mestre (FollowSummonTaskAI - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::ai::follow::follow_service::FollowStartService;

#[derive(Debug, Clone)]
pub struct FollowSummonTaskAI {
    pub master_id: u32,
    pub follow_distance: f32,
    pub teleport_distance: f32,
    pub speed: f32,
}

impl FollowSummonTaskAI {
    pub fn new(master_id: u32, follow_distance: f32, speed: f32) -> Self {
        Self {
            master_id,
            follow_distance,
            teleport_distance: 50.0, // Teleporta para o mestre se ficar a mais de 50m
            speed,
        }
    }

    /// Processa o tick de perseguição da invocação / pet
    pub fn tick_follow(
        &self,
        current_pos: &Coord,
        master_pos: &Coord,
        delta_seconds: f32,
    ) -> Coord {
        let dist = current_pos.distance(master_pos);

        // Se estiver muito longe (>50m), teleporta instantaneamente para o mestre
        if dist > self.teleport_distance {
            return *master_pos;
        }

        // Se estiver fora do raio de parada, move suavemente em direção ao mestre
        if dist > self.follow_distance {
            FollowStartService::calculate_step(current_pos, master_pos, self.speed, delta_seconds)
        } else {
            *current_pos
        }
    }
}
