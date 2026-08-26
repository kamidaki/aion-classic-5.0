//! Serviço de Início de Perseguição / Acompanhamento (FollowStartService - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;

pub struct FollowStartService;

impl FollowStartService {
    /// Calcula a distância e valida se o seguidor precisa se mover em direção ao mestre
    pub fn should_follow(follower_pos: &Coord, target_pos: &Coord, follow_range: f32) -> bool {
        follower_pos.distance(target_pos) > follow_range
    }

    /// Calcula o novo passo de interpolação em direção ao alvo
    pub fn calculate_step(
        current_pos: &Coord,
        target_pos: &Coord,
        speed: f32,
        delta_seconds: f32,
    ) -> Coord {
        let dx = target_pos.x() - current_pos.x();
        let dy = target_pos.y() - current_pos.y();
        let dz = target_pos.z() - current_pos.z();
        let dist = (dx * dx + dy * dy + dz * dz).sqrt();

        if dist < 0.01 {
            return *current_pos;
        }

        let step = (speed * delta_seconds).min(dist);
        Coord::new(
            current_pos.x() + (dx / dist) * step,
            current_pos.y() + (dy / dist) * step,
            current_pos.z() + (dz / dist) * step,
        )
    }
}
