//! Motor Central de Inteligência Artificial (AI Engine) - Padrão Java AION 4.8

pub mod state;
pub mod event;
pub mod hate_table;
pub mod walk_manager;
pub mod abstract_ai;
pub mod npc_ai;
pub mod monster_ai;
pub mod aggressive_ai;
pub mod boss_ai;
pub mod guard_ai;
pub mod trap_ai;

pub use state::{AIState, AISubState};
pub use event::AIEvent;
pub use hate_table::{HateTable, HateEntry};
pub use walk_manager::WalkManager;
pub use abstract_ai::{AbstractAI, BaseAI};
pub use npc_ai::NpcAI;
pub use monster_ai::MonsterAI;
pub use aggressive_ai::AggressiveNpcAI;
pub use boss_ai::{BossAI, BossPhase};
pub use guard_ai::{GuardAI, Faction};
pub use trap_ai::TrapAI;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hate_table_threat_mechanics() {
        let mut ht = HateTable::new();
        assert!(ht.is_empty());

        // Dano direto: 1 dano = 1 ponto de hate
        ht.add_damage_hate(1001, 250);
        assert_eq!(ht.get_highest_target(), Some(1001));

        // Cura de aliado: 1 cura = 0.5 ponto de hate (Clérigo cura 400 = 200 de hate)
        ht.add_heal_hate(1002, 400);
        assert_eq!(ht.get_highest_target(), Some(1001)); // 1001 ainda tem mais (250 > 200)

        // Taunt de Templário: +5000 de hate instantâneo
        ht.add_taunt_hate(1003, 5000);
        assert_eq!(ht.get_highest_target(), Some(1003));

        // Jogador morre ou usa Hide -> remove alvo
        ht.remove_target(1003);
        assert_eq!(ht.get_highest_target(), Some(1001));
    }

    #[test]
    fn test_boss_ai_phases_and_enrage() {
        let mut boss = BossAI::new(9901, 3.0, 20.0, 2.0);
        assert_eq!(boss.current_phase, BossPhase::Phase1Normal);

        // 75% HP -> Fase 2 (Adds)
        assert_eq!(boss.update_hp_phase(74.0), Some(BossPhase::Phase2Adds));
        assert!(boss.adds_spawned);

        // 50% HP -> Fase 3 (AoE Cast)
        assert_eq!(boss.update_hp_phase(49.0), Some(BossPhase::Phase3AoECast));
        assert!(boss.aoe_casted);

        // 25% HP -> Fase 4 (Enrage: +100% dano, +50% atk speed)
        assert_eq!(boss.update_hp_phase(24.0), Some(BossPhase::Phase4Enrage));
        assert!(boss.is_enraged);
        assert_eq!(boss.damage_multiplier, 2.0);
        assert_eq!(boss.attack_speed_multiplier, 1.5);
    }

    #[test]
    fn test_aggressive_and_guard_ai_detection() {
        let mut aggro_ai = AggressiveNpcAI::new(5001, 2.0, 15.0, 1.5);
        // Jogador longe (25m) -> não detecta
        assert!(!aggro_ai.check_see_player(1001, 25.0));
        assert_eq!(aggro_ai.get_state(), AIState::Idle);

        // Jogador perto (10m) -> detecta e entra em combate
        assert!(aggro_ai.check_see_player(1001, 10.0));
        assert_eq!(aggro_ai.get_state(), AIState::Attacking);

        // Guarda Elyos detecta Asmodian
        let mut guard = GuardAI::new(7001, Faction::Elyos, 5.0, 20.0);
        assert!(guard.check_enemy_player(2001, Faction::Asmodians, 12.0));
        assert_eq!(guard.get_state(), AIState::Attacking);

        // Guarda Elyos ignora outro Elyos
        let mut guard2 = GuardAI::new(7002, Faction::Elyos, 5.0, 20.0);
        assert!(!guard2.check_enemy_player(1001, Faction::Elyos, 5.0));
        assert_eq!(guard2.get_state(), AIState::Idle);
    }

    #[test]
    fn test_walk_manager_waypoints_patrol() {
        let waypoints = vec![
            (100.0, 100.0, 10.0),
            (120.0, 100.0, 10.0),
            (140.0, 100.0, 10.0),
        ];
        let mut wm = WalkManager::new(waypoints, 3.0);
        assert_eq!(wm.get_current_waypoint(), Some((100.0, 100.0, 10.0)));

        assert_eq!(wm.advance_to_next_waypoint(), Some((120.0, 100.0, 10.0)));
        assert!(wm.is_paused);
        assert!(!wm.tick_pause(1.0)); // Ainda faltam 2s
        assert!(wm.tick_pause(2.5));  // Pausa terminou
        assert!(!wm.is_paused);
    }
}
