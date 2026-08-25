//! Eventos Processados pelo Motor de IA (AI Events)

#[derive(Debug, Clone, PartialEq)]
pub enum AIEvent {
    Spawn,
    Attacked { attacker_id: u32, damage: i32 },
    SeePlayer { player_id: u32, distance: f32 },
    TargetLost,
    ReachedWaypoint { waypoint_idx: usize },
    HpPhaseChange { current_hp_percent: f32 },
    Die,
    Evade,
    Command { command_id: u32, target_id: Option<u32> },
}
