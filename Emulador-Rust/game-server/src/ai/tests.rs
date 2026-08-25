//! Suíte Completa de Testes do Motor de Inteligência Artificial (AI Engine)

#[cfg(test)]
pub mod tests {
    use std::time::Instant;
    use crate::ai::abstract_ai::AbstractAI;
    use crate::ai::ai_engine::{AIEngine, EntityAI};
    use crate::ai::ai_name::AIName;
    use crate::ai::attack_intention::AttackIntention;
    use crate::ai::boss_ai::{BossAI, BossPhase};
    use crate::ai::event::AIEventType;
    use crate::ai::follow::follow_service::FollowStartService;
    use crate::ai::follow::follow_task::FollowSummonTaskAI;
    use crate::ai::guard_ai::{Faction, GuardAI};
    use crate::ai::handler::aggro_handler::AggroEventHandler;
    use crate::ai::handler::returning_handler::ReturningEventHandler;
    use crate::ai::handler::shout_handler::{ShoutEventHandler, ShoutEventType};
    use crate::ai::hate_table::HateTable;
    use crate::ai::kisk_ai::KiskAI;
    use crate::ai::manager::attack_manager::AttackManager;
    use crate::ai::manager::follow_manager::FollowManager;
    use crate::ai::manager::skill_attack_manager::SkillAttackManager;
    use crate::ai::manager::walk_manager::WalkManager;
    use crate::ai::monster_ai::MonsterAI;
    use crate::ai::npc_ai::NpcAI;
    use crate::ai::poll::answer::AIAnswer;
    use crate::ai::poll::npc_polls::NpcAIPolls;
    use crate::ai::poll::question::AIQuestion;
    use crate::ai::scenario::walk_scenario::WalkScenario;
    use crate::ai::servant_ai::ServantAI;
    use crate::ai::state::AIState;
    use crate::ai::trap_ai::TrapAI;
    use crate::character::Character;
    use crate::engine::Coord;
    use crate::entity::Entity;

    #[test]
    fn test_hate_table_mechanics() {
        let mut ht = HateTable::new();
        ht.add_damage_hate(1001, 250);
        assert_eq!(ht.get_highest_target(), Some(1001));

        // Cura de aliado gera metade do hate
        ht.add_heal_hate(1002, 400); // 200 hate
        assert_eq!(ht.get_highest_target(), Some(1001));

        // Taunt do Templário gera hate imediato massivo
        ht.add_taunt_hate(1003, 5000);
        assert_eq!(ht.get_highest_target(), Some(1003));

        // Jogador morre ou usa hide -> remoção de alvo
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
    fn test_guard_faction_hostility() {
        let mut guard = GuardAI::new(7001, Faction::Elyos, 5.0, 20.0);
        assert!(guard.check_enemy_player(2001, Faction::Asmodians, 12.0));
        assert_eq!(guard.get_state(), AIState::Attacking);

        // Guarda Elyos ignora outro Elyos
        let mut guard2 = GuardAI::new(7002, Faction::Elyos, 5.0, 20.0);
        assert!(!guard2.check_enemy_player(1001, Faction::Elyos, 5.0));
        assert_eq!(guard2.get_state(), AIState::Idle);
    }

    #[test]
    fn test_follow_and_summon_teleport() {
        let current_pos = Coord::new(0.0, 0.0, 0.0);
        let master_near = Coord::new(3.0, 4.0, 0.0); // 5m de distância
        let master_far = Coord::new(60.0, 80.0, 0.0); // 100m de distância

        let task = FollowSummonTaskAI::new(1001, 2.0, 6.0);

        // Perto -> move suavemente
        let step = task.tick_follow(&current_pos, &master_near, 0.5);
        assert!(step.x() > 0.0 && step.x() < 3.0);

        // Longe (>50m) -> teleporta instantaneamente para o mestre
        let teleport_pos = task.tick_follow(&current_pos, &master_far, 0.5);
        assert_eq!(teleport_pos.x(), master_far.x());
        assert_eq!(teleport_pos.y(), master_far.y());
    }

    #[test]
    fn test_returning_handler_leash_and_reset() {
        let spawn_pos = Coord::new(100.0, 100.0, 10.0);
        let near_pos = Coord::new(110.0, 100.0, 10.0);
        let far_pos = Coord::new(150.0, 100.0, 10.0); // 50m de distância

        assert!(!ReturningEventHandler::check_leash(&near_pos, &spawn_pos, 30.0));
        assert!(ReturningEventHandler::check_leash(&far_pos, &spawn_pos, 30.0));

        let mut entity = Entity::novo(500, far_pos, 210001, 210001);
        entity.hp.update(-500); // Tomou dano
        let mut state = AIState::Attacking;
        let mut hate_table = HateTable::new();
        hate_table.add_damage_hate(1001, 500);

        ReturningEventHandler::on_return(&mut entity, &mut state, &mut hate_table);
        assert_eq!(state, AIState::Returning);
        assert!(hate_table.is_empty());
        assert_eq!(entity.hp.current(), entity.max_hp); // Full HP regenerado
    }

    #[test]
    fn test_trap_and_servant_mechanics() {
        let mut trap = TrapAI::new(8001, 1001, 3.0, 1234);
        assert_eq!(trap.get_state(), AIState::Idle);

        // Dono passa por cima da armadilha -> não dispara
        assert_eq!(trap.check_trigger(1001, 1.0), None);

        // Inimigo passa a 2m -> dispara
        assert_eq!(trap.check_trigger(2001, 2.0), Some(1234));
        assert_eq!(trap.get_state(), AIState::Dead);

        // Servo / Totem de Invocação
        let mut servant = ServantAI::new(8002, 1001, 4321, 2.0, 10.0);
        assert_eq!(servant.tick_servant(1.0), None); // Ainda no cooldown
        assert_eq!(servant.tick_servant(1.5), Some(4321)); // Dispara habilidade periódica
    }

    #[test]
    fn test_kisk_registration_and_usage() {
        let mut kisk = KiskAI::new(9001, 1001, 2, 6);
        assert_eq!(kisk.get_state(), AIState::Idle);

        // Registra membros
        assert!(kisk.register_player(1002).is_ok());
        assert!(kisk.register_player(1003).is_ok());

        // Consome ressurgimento
        assert!(kisk.use_resurrection());
        assert_eq!(kisk.current_resurrections, 1);
        assert!(kisk.use_resurrection()); // Segunda e última carga
        assert_eq!(kisk.get_state(), AIState::Dead);
    }

    #[test]
    fn test_skill_attack_manager_cooldowns() {
        let mut sam = SkillAttackManager::new();
        sam.add_skill(101, 1, 100, 5.0); // Skill normal pronta
        sam.add_skill(102, 1, 50, 10.0);  // Skill de HP baixo (50%)

        let now = Instant::now();

        // 100% HP -> usa skill 101
        assert_eq!(sam.choose_skill(100, now), Some((101, 1)));
        // Imediatamente depois -> em cooldown
        assert_eq!(sam.choose_skill(100, now), None);

        // 40% HP -> usa skill 102
        assert_eq!(sam.choose_skill(40, now), Some((102, 1)));
    }

    #[test]
    fn test_ai_engine_registration_and_tick() {
        let mut engine = AIEngine::new();
        engine.register_ai(101, AIName::Monster);
        engine.register_ai(102, AIName::Aggressive);
        engine.register_ai(103, AIName::Boss);

        assert_eq!(engine.active_ai.len(), 3);

        // Eventos
        engine.on_ai_event(101, AIEventType::Attacked);
        assert_eq!(engine.active_ai.get(&101).unwrap().get_state(), AIState::Attacking);

        engine.unregister_ai(101);
        assert_eq!(engine.active_ai.len(), 2);
    }
}
