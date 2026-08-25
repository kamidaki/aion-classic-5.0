//! Suíte de Testes do Subsistema QuestEngine

#[cfg(test)]
pub mod tests {
    use std::sync::Arc;
    use crate::engine::Coord;
    use crate::questengine::exceptions::QuestDialogException;
    use crate::questengine::handlers::models::*;
    use crate::questengine::handlers::template::*;
    use crate::questengine::handlers::{HandlerResult, QuestHandler};
    use crate::questengine::model::*;
    use crate::questengine::quest_engine::QuestEngine;
    use crate::questengine::task::*;

    #[test]
    fn test_monster_hunt_full_lifecycle() {
        let data = MonsterHuntData::new(203001, 203002)
            .with_monster(Monster::new(210001, 0, 3, 0));
        let handler = Arc::new(MonsterHunt::new(1001, data));

        let mut engine = QuestEngine::new();
        engine.register_handler(handler);

        let mut state = QuestState::new(1001);
        assert_eq!(state.status, QuestStatus::None);

        // 1. Dialogo inicial com NPC aceitando a missao
        let mut env = QuestEnv::new(1, 1001)
            .with_target(1, 203001)
            .with_dialog(QuestDialog::AcceptQuest);
        let res = engine.on_dialog(&mut env, &mut state);
        assert!(res.is_success());
        assert_eq!(state.status, QuestStatus::Start);
        assert_eq!(state.get_quest_var_by_index(0), 0);

        // 2. Mata 3 monstros
        let mut kill_env = QuestEnv::new(1, 1001).with_target(10, 210001);
        assert!(engine.on_kill(&mut kill_env, &mut state).is_success());
        assert_eq!(state.get_quest_var_by_index(0), 1);
        assert_eq!(state.status, QuestStatus::Start);

        assert!(engine.on_kill(&mut kill_env, &mut state).is_success());
        assert_eq!(state.get_quest_var_by_index(0), 2);
        assert_eq!(state.status, QuestStatus::Start);

        assert!(engine.on_kill(&mut kill_env, &mut state).is_success());
        assert_eq!(state.get_quest_var_by_index(0), 3);
        assert_eq!(state.status, QuestStatus::Reward); // Passou para Reward!

        // 3. Entrega a missao ao NPC final
        let mut reward_env = QuestEnv::new(1, 1001)
            .with_target(2, 203002)
            .with_dialog(QuestDialog::SelectReward);
        assert!(engine.on_dialog(&mut reward_env, &mut state).is_success());
        assert_eq!(state.status, QuestStatus::Complete);
        assert_eq!(state.complete_count, 1);
    }

    #[test]
    fn test_report_to_many_multistep() {
        let data = ReportToManyData::new(2001, 2004)
            .with_npc_info(NpcInfos::new(2002, 10, 20))
            .with_npc_info(NpcInfos::new(2003, 10, 20));
        let handler = Arc::new(ReportToMany::new(1002, data));

        let mut engine = QuestEngine::new();
        engine.register_handler(handler);

        let mut state = QuestState::new(1002);

        // Aceita no NPC 2001
        let mut env = QuestEnv::new(1, 1002).with_target(1, 2001).with_dialog(QuestDialog::AcceptQuest);
        assert!(engine.on_dialog(&mut env, &mut state).is_success());
        assert_eq!(state.status, QuestStatus::Start);
        assert_eq!(state.get_quest_var_by_index(0), 0);

        // Fala com o primeiro NPC (2002)
        let mut env2 = QuestEnv::new(1, 1002).with_target(2, 2002);
        assert!(engine.on_dialog(&mut env2, &mut state).is_success());
        assert_eq!(state.get_quest_var_by_index(0), 1);

        // Fala com o segundo NPC (2003) -> muda para Reward
        let mut env3 = QuestEnv::new(1, 1002).with_target(3, 2003);
        assert!(engine.on_dialog(&mut env3, &mut state).is_success());
        assert_eq!(state.get_quest_var_by_index(0), 2);
        assert_eq!(state.status, QuestStatus::Reward);

        // Conclui no NPC 2004
        let mut env4 = QuestEnv::new(1, 1002).with_target(4, 2004).with_dialog(QuestDialog::SelectReward);
        assert!(engine.on_dialog(&mut env4, &mut state).is_success());
        assert_eq!(state.status, QuestStatus::Complete);
    }

    #[test]
    fn test_kill_in_world() {
        let data = KillInWorldData::new(3001, 3002, 210050000, 5);
        let handler = Arc::new(KillInWorld::new(1003, data));

        let mut engine = QuestEngine::new();
        engine.register_handler(handler);

        let mut state = QuestState::new(1003);
        let mut env = QuestEnv::new(1, 1003).with_target(1, 3001).with_dialog(QuestDialog::AcceptQuest);
        assert!(engine.on_dialog(&mut env, &mut state).is_success());

        // Mata em mapa errado -> nada acontece
        assert_eq!(engine.on_kill_in_world(&mut env, &mut state, 220020000), HandlerResult::Unknown);

        // Mata 5 no mapa correto
        for i in 1..=5 {
            assert!(engine.on_kill_in_world(&mut env, &mut state, 210050000).is_success());
            if i < 5 {
                assert_eq!(state.status, QuestStatus::Start);
            }
        }
        assert_eq!(state.status, QuestStatus::Reward);
    }

    #[test]
    fn test_destination_and_zone_checkers() {
        let coord_checker = QuestTasks::new_coord_checker(Coord::new(100.0, 100.0, 50.0), 10.0);
        assert!(coord_checker.check(&Coord::new(105.0, 100.0, 50.0)));
        assert!(!coord_checker.check(&Coord::new(120.0, 100.0, 50.0)));

        let target_checker = QuestTasks::new_target_checker(101, Coord::new(0.0, 0.0, 0.0), 5.0);
        assert!(target_checker.check(&Coord::new(2.0, 2.0, 2.0)));
        assert!(!target_checker.check(&Coord::new(10.0, 0.0, 0.0)));

        let zone_checker = QuestTasks::new_zone_checker(210010001);
        assert!(zone_checker.is_in_zone(210010001));
        assert!(!zone_checker.is_in_zone(210010002));
    }

    #[test]
    fn test_following_npc_check_task() {
        let follow_task = QuestTasks::new_follow_task(1, 100, 15.0);
        let p_pos = Coord::new(10.0, 10.0, 0.0);
        let npc_pos_close = Coord::new(12.0, 12.0, 0.0);
        let npc_pos_far = Coord::new(50.0, 50.0, 0.0);

        assert!(follow_task.is_following_within_range(&p_pos, &npc_pos_close));
        assert!(!follow_task.is_following_within_range(&p_pos, &npc_pos_far));
    }

    #[test]
    fn test_quest_dialog_exception() {
        let exc = QuestDialogException::new(1001, 10, "Invalid dialog transition");
        let display = format!("{}", exc);
        assert!(display.contains("Quest #1001"));
        assert!(display.contains("Dialog #10"));
        assert!(display.contains("Invalid dialog transition"));
    }
}
