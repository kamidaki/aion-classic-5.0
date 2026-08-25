//! EnvironmentService - Gerenciamento de Rotas de Corrente de Vento e Clima (Padrão Java AION)

use crate::environment::WindstreamService;
use crate::message::{client as c, server as s};
use crate::{Messages, ServerUpdate};

pub struct EnvironmentService;

impl EnvironmentService {
    /// Processa entrada e saída de caminhos de corrente de vento (Windstream)
    pub fn handle_wind_path(
        character_id: u32,
        client_id: u16,
        wind_path: &c::WindPath,
        windstream_service: &WindstreamService,
        messages: &mut Messages,
    ) {
        println!(
            "INFO: [EnvironmentService] Player {} WindPath request (stream_id: {}, action: {})",
            character_id, wind_path.windstream_id, wind_path.action
        );

        if wind_path.action == 1 {
            // Entrar na corrente
            let waypoints = windstream_service
                .get_waypoints(wind_path.windstream_id)
                .unwrap_or_else(|| {
                    vec![
                        (1300.0, 1400.0, 300.0),
                        (1350.0, 1450.0, 320.0),
                        (1400.0, 1500.0, 310.0),
                        (1450.0, 1550.0, 290.0),
                    ]
                });
            let duration_ms = (waypoints.len() as f32) * 2000.0;
            messages.extend_direct(
                client_id,
                [
                    ServerUpdate::new(s::Message::WindPathResult(s::WindPathResult::new(
                        character_id,
                        wind_path.windstream_id,
                        waypoints,
                        duration_ms,
                    ))),
                    ServerUpdate::new(s::Message::WindStateInfo(s::WindStateInfo::new(
                        character_id,
                        wind_path.windstream_id,
                        1,
                        22.0,
                    ))),
                ],
            );
        } else {
            // Sair da corrente
            messages.push_direct(
                client_id,
                ServerUpdate::new(s::Message::WindStateInfo(s::WindStateInfo::new(
                    character_id,
                    wind_path.windstream_id,
                    0,
                    0.0,
                ))),
            );
        }
    }
}
