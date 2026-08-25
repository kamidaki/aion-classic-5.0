//! WalkerFormator - Gerenciador de Rotas de Patrulha e Movimentação de NPCs (Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::time::{Duration, Instant};

use crate::engine::Coord;
use crate::entity::Entity;
use crate::spawnengine::types::WalkerRoute;

#[derive(Debug, Default)]
pub struct WalkerFormator {
    routes: HashMap<String, WalkerRoute>,
    /// Mapeamento de entity_id -> (route_id, current_waypoint_index, pause_until_instant)
    active_walkers: HashMap<u32, (String, usize, Instant)>,
}

impl WalkerFormator {
    pub fn new() -> Self {
        Self::default()
    }

    /// Registra uma rota de patrulha
    pub fn register_route(&mut self, route: WalkerRoute) {
        self.routes.insert(route.route_id.clone(), route);
    }

    /// Atribui uma rota de patrulha a uma entidade NPC
    pub fn assign_route(&mut self, entity_id: u32, route_id: impl Into<String>) -> bool {
        let r_id = route_id.into();
        if self.routes.contains_key(&r_id) {
            self.active_walkers.insert(entity_id, (r_id, 0, Instant::now()));
            true
        } else {
            false
        }
    }

    /// Processa o deslocamento dos NPCs patrulheiros para o próximo waypoint
    pub fn tick_walkers(&mut self, entities: &mut [Entity], now: Instant) {
        for entity in entities.iter_mut() {
            let (route_id, current_idx, rest_until) = match self.active_walkers.get_mut(&entity.id()) {
                Some(data) => data,
                None => continue,
            };

            // Se ainda estiver em tempo de pausa no waypoint, aguarda
            if now < *rest_until {
                continue;
            }

            let route = match self.routes.get(route_id) {
                Some(r) if !r.points.is_empty() => r,
                _ => continue,
            };

            let target_point = &route.points[*current_idx];
            let dest = Coord::new(target_point.x, target_point.y, target_point.z);

            // Se alcançou o waypoint de destino (raio de 1.0m)
            if entity.location().distance(&dest) < 1.0 {
                // Configura tempo de descanso no ponto
                if target_point.rest_time_ms > 0 {
                    *rest_until = now + Duration::from_millis(target_point.rest_time_ms as u64);
                }

                // Avança para o próximo waypoint
                if *current_idx + 1 < route.points.len() {
                    *current_idx += 1;
                } else if route.is_loop {
                    *current_idx = 0;
                }
            } else {
                // Interpola movimento suave em direção ao destino (velocidade de caminhada ~2.5m/s)
                let current_loc = entity.location();
                let dir_x = dest.x() - current_loc.x();
                let dir_y = dest.y() - current_loc.y();
                let dir_z = dest.z() - current_loc.z();
                let dist = (dir_x * dir_x + dir_y * dir_y + dir_z * dir_z).sqrt();

                if dist > 0.001 {
                    let step = 0.5f32.min(dist);
                    let new_x = current_loc.x() + (dir_x / dist) * step;
                    let new_y = current_loc.y() + (dir_y / dist) * step;
                    let new_z = current_loc.z() + (dir_z / dist) * step;
                    entity.set_location(Coord::new(new_x, new_y, new_z));
                }
            }
        }
    }

    /// Contagem de rotas registradas
    pub fn route_count(&self) -> usize {
        self.routes.len()
    }
}
