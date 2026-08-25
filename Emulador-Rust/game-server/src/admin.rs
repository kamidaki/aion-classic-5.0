//! Sistemas de Administração (GM), Anti-Hack Nativo e Punições

use super::engine::Coord;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum AdminLevel {
    Player = 0,
    Helper = 1,
    Gamemaster = 2,
    SeniorGm = 3,
    Admin = 4,
}

#[derive(Debug, Clone, Default)]
pub struct Punishment {
    pub account_id: u32,
    pub player_id: u32,
    pub is_muted: bool,
    pub mute_until_tick: u64,
    pub is_jailed: bool,
    pub jail_until_tick: u64,
    pub is_banned: bool,
}

impl Punishment {
    pub fn new(account_id: u32, player_id: u32) -> Self {
        Self {
            account_id,
            player_id,
            is_muted: false,
            mute_until_tick: 0,
            is_jailed: false,
            jail_until_tick: 0,
            is_banned: false,
        }
    }

    pub fn apply_mute(&mut self, duration_ticks: u64, current_tick: u64) {
        self.is_muted = true;
        self.mute_until_tick = current_tick + duration_ticks;
    }

    pub fn apply_jail(&mut self, duration_ticks: u64, current_tick: u64) {
        self.is_jailed = true;
        self.jail_until_tick = current_tick + duration_ticks;
    }

    pub fn apply_ban(&mut self) {
        self.is_banned = true;
    }

    pub fn is_active_mute(&self, current_tick: u64) -> bool {
        self.is_muted && current_tick < self.mute_until_tick
    }

    pub fn is_active_jail(&self, current_tick: u64) -> bool {
        self.is_jailed && current_tick < self.jail_until_tick
    }
}

#[derive(Debug, Clone)]
pub struct AntiHackEngine {
    pub last_attack_timestamp: u64,
    pub last_packet_count: u32,
}

impl AntiHackEngine {
    pub fn new() -> Self {
        Self {
            last_attack_timestamp: 0,
            last_packet_count: 0,
        }
    }

    pub fn validate_attack_speed(&mut self, current_time_ms: u64, weapon_attack_speed_ms: u64) -> bool {
        if self.last_attack_timestamp == 0 {
            self.last_attack_timestamp = current_time_ms;
            return true;
        }

        let delta = current_time_ms.saturating_sub(self.last_attack_timestamp);
        let min_allowed = (weapon_attack_speed_ms as f32 * 0.85) as u64; // Tolerância de 15% de jitter de rede

        if delta < min_allowed {
            false // No-Animation / Attack Speed Hack detectado
        } else {
            self.last_attack_timestamp = current_time_ms;
            true
        }
    }

    pub fn validate_movement(old_pos: &Coord, new_pos: &Coord, elapsed_secs: f32, max_speed_m_s: f32) -> bool {
        if elapsed_secs <= 0.0 {
            return true;
        }

        let distance = old_pos.distance(new_pos);
        let max_allowed_distance = max_speed_m_s * elapsed_secs * 1.25; // 25% de margem de tolerância de latência
        distance <= max_allowed_distance
    }

    pub fn validate_packet_rate(packets_in_second: u32) -> bool {
        packets_in_second <= 150 // Limite de 150 pacotes por segundo contra packet flood
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn admin_levels_hierarchy() {
        assert!(AdminLevel::Admin > AdminLevel::SeniorGm);
        assert!(AdminLevel::SeniorGm > AdminLevel::Gamemaster);
        assert!(AdminLevel::Gamemaster > AdminLevel::Helper);
        assert!(AdminLevel::Helper > AdminLevel::Player);
    }

    #[test]
    fn punishment_mute_and_jail_lifecycles() {
        let mut pun = Punishment::new(1, 100);
        assert!(!pun.is_active_mute(100));
        assert!(!pun.is_active_jail(100));

        pun.apply_mute(500, 100);
        assert!(pun.is_active_mute(200));
        assert!(!pun.is_active_mute(650)); // Mute expired

        pun.apply_jail(1000, 100);
        assert!(pun.is_active_jail(500));
        assert!(!pun.is_active_jail(1200)); // Jail expired

        pun.apply_ban();
        assert!(pun.is_banned);
    }

    #[test]
    fn antihack_validations() {
        let mut antihack = AntiHackEngine::new();

        // Valid attack with 1.5s base speed
        assert!(antihack.validate_attack_speed(1000, 1500));
        // Attack speed hack: second attack in 500ms (too fast!)
        assert!(!antihack.validate_attack_speed(1500, 1500));
        // Valid second attack at 2350ms (delta 1350ms >= 1275ms)
        assert!(antihack.validate_attack_speed(2350, 1500));

        // Speedhack: 100 meters in 1 second with max speed 6.0 m/s
        let old_p = Coord::new(0.0, 0.0, 0.0);
        let teleport_p = Coord::new(100.0, 0.0, 0.0);
        assert!(!AntiHackEngine::validate_movement(&old_p, &teleport_p, 1.0, 6.0));

        // Normal walk: 5 meters in 1 second
        let walk_p = Coord::new(5.0, 0.0, 0.0);
        assert!(AntiHackEngine::validate_movement(&old_p, &walk_p, 1.0, 6.0));

        // Packet flood check
        assert!(AntiHackEngine::validate_packet_rate(50));
        assert!(!AntiHackEngine::validate_packet_rate(200));
    }
}
