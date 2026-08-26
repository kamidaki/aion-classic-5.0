//! Suíte Completa de Testes do Subsistema de Instâncias

#[cfg(test)]
pub mod tests {
    use std::time::Instant;
    use crate::character::Character;
    use crate::engine::Coord;
    use crate::entity::Entity;
    use crate::instance::handlers::arena_handler::ArenaInstanceHandler;
    use crate::instance::handlers::boss_rush_handler::BossRushInstanceHandler;
    use crate::instance::handlers::dredgion_handler::DredgionInstanceHandler;
    use crate::instance::handlers::general_handler::GeneralInstanceHandler;
    use crate::instance::handlers::instance_handler::InstanceHandler;
    use crate::instance::handlers::tiak_handler::TiakResearchCenterHandler;
    use crate::instance::models::dungeon_gate::DungeonGate;
    use crate::instance::models::instance_reward::InstanceScore;
    use crate::instance::models::rift::Rift;
    use crate::instance::models::siege_location::{SiegeLocation, SiegeState};
    use crate::instance::models::stage_type::StageType;
    use crate::instance::models::world_instance::{InstanceManager, WorldMapInstance};
    use crate::instance::services::instance_service::InstanceService;

    #[test]
    fn instance_lifecycle_and_cleanup() {
        let mut mgr = InstanceManager::new();
        let inst_id = mgr.create_instance(300040000, Some(101), 1000, 100);

        assert_eq!(mgr.instance_count(), 1);
        assert!(mgr.add_player(inst_id, 1));
        assert!(mgr.add_player(inst_id, 2));

        // Player leaves
        assert!(mgr.remove_player(inst_id, 1));
        assert!(mgr.remove_player(inst_id, 2));

        // Cleanup before expiration should retain instance until grace period expires
        assert_eq!(mgr.cleanup(200), 0);

        // Cleanup after grace period
        assert_eq!(mgr.cleanup(500), 1);
        assert_eq!(mgr.instance_count(), 0);
    }

    #[test]
    fn siege_state_transitions_and_conquest() {
        let mut fort = SiegeLocation::new(1011, "Divine Fortress");
        assert_eq!(fort.state, SiegeState::Peaceful);

        fort.start_siege();
        assert_eq!(fort.state, SiegeState::Vulnerable);

        // Legion 55 captures the fort
        fort.resolve_siege(Some(55));
        assert_eq!(fort.state, SiegeState::Peaceful);
        assert_eq!(fort.occupying_legion_id, Some(55));
    }

    #[test]
    fn rift_level_and_usage_limits() {
        let mut rift = Rift::new(
            1,
            210020000,
            220020000,
            Coord::new(100.0, 100.0, 0.0),
            Coord::new(500.0, 500.0, 10.0),
            20,
            32,
            2,
        );

        // Player level 15 (too low)
        assert_eq!(rift.try_teleport(15), None);

        // Player level 25 (valid)
        assert!(rift.try_teleport(25).is_some());
        assert_eq!(rift.current_uses, 1);

        // Player level 30 (valid, reaches max_uses)
        assert!(rift.try_teleport(30).is_some());
        assert_eq!(rift.current_uses, 2);
        assert!(!rift.is_active);

        // Player level 28 (rift closed)
        assert_eq!(rift.try_teleport(28), None);
    }

    #[test]
    fn test_dungeon_scoring_and_gates() {
        let mut gate = DungeonGate::new(1, "Boss Room Gate", Some(185000001));
        assert!(!gate.is_open);
        assert!(!gate.try_unlock(&[185000002, 185000003]));
        assert!(gate.try_unlock(&[185000001]));
        assert!(gate.is_open);

        let mut score = InstanceScore::new();
        score.add_kill(false, 500);
        score.add_kill(true, 15_000);
        assert_eq!(score.get_rank(), 'S');

        score.record_death();
        score.record_death();
        assert_eq!(score.points, 15_100);
    }

    #[test]
    fn test_instance_service_cooldown_and_entry() {
        let mut service = InstanceService::new();
        let now = Instant::now();

        let mut player = Character::new(1001, 1, Coord::new(0.0, 0.0, 0.0));
        player.stats.level = 50;

        // Entrar em Baranath Dredgion (map 300040000)
        let enter_res = service.request_enter_instance(&player, 300040000, Some(10), now, 100);
        assert!(enter_res.is_ok());

        // Segunda entrada imediata na mesma masmorra -> bloqueado por cooldown
        let second_entry = service.request_enter_instance(&player, 300040000, Some(10), now, 101);
        assert!(second_entry.is_err());

        // Jogador level baixo (level 30) tentando entrar em Padmarashka (level 55+)
        let mut low_player = Character::new(1002, 1, Coord::new(0.0, 0.0, 0.0));
        low_player.stats.level = 30;
        let padma_res = service.request_enter_instance(&low_player, 300150000, None, now, 102);
        assert!(padma_res.is_err());
    }

    #[test]
    fn test_dredgion_handler_scoring() {
        let mut dredgion = DredgionInstanceHandler::new();
        let mut inst = WorldMapInstance::new(1, 300040000, None, 7200, 100);
        dredgion.on_instance_create(&mut inst);
        assert_eq!(inst.stage, StageType::Phase1);

        // Elyos destroem Surkana
        dredgion.add_surkana_points(true, 500);
        assert_eq!(dredgion.elyos_score, 500);

        // Asmodians matam jogador Elyos no PvP
        dredgion.add_pvp_kill(false);
        assert_eq!(dredgion.asmodian_score, 60);
        assert_eq!(dredgion.elyos_score, 440);

        // Recompensa para jogador
        let player = Character::new(1001, 1, Coord::new(0.0, 0.0, 0.0));
        let reward = dredgion.do_reward(&player);
        assert!(reward.abyss_points >= 2500);
    }

    #[test]
    fn test_tiak_and_arena_handlers() {
        // Tiak Research Center
        let mut tiak = TiakResearchCenterHandler::new();
        tiak.capture_generator(true);
        assert_eq!(tiak.elyos_points, 500);

        // Arena de PvP
        let mut arena = ArenaInstanceHandler::new(3);
        let player1 = Character::new(1001, 1, Coord::new(0.0, 0.0, 0.0));
        let mut inst = WorldMapInstance::new(2, 300350000, None, 1800, 100);
        arena.on_enter_instance(&player1, &mut inst);

        arena.record_pvp_kill(1001, 1002);
        let rew = arena.do_reward(&player1);
        assert_eq!(rew.abyss_points, 500);
    }

    #[test]
    fn test_boss_rush_handler() {
        let mut rush = BossRushInstanceHandler::new();
        let mut inst = WorldMapInstance::new(3, 300150000, None, 3600, 100);
        rush.on_instance_create(&mut inst);

        let mut boss = Entity::novo(9001, Coord::new(0.0, 0.0, 0.0), 210001, 210001);
        boss.max_hp = 2_000_000;
        rush.on_die_npc(&boss, &mut inst);

        assert!(rush.main_boss_killed);
        assert_eq!(inst.stage, StageType::Complete);
    }
}
