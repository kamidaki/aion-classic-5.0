//! Handler de Missão de Matar Monstros Spawnados (KillSpawned - Padrão Java Aion Classic 2.8 / 4.5)

use crate::questengine::handlers::handler_result::HandlerResult;
use crate::questengine::handlers::models::KillSpawnedData;
use crate::questengine::handlers::quest_handler::QuestHandler;
use crate::questengine::model::{QuestDialog, QuestEnv, QuestState, QuestStatus};

#[derive(Debug, Clone)]
pub struct KillSpawned {
    pub quest_id: u32,
    pub data: KillSpawnedData,
}

impl KillSpawned {
    pub fn new(quest_id: u32, data: KillSpawnedData) -> Self {
        Self { quest_id, data }
    }
}

impl QuestHandler for KillSpawned {
    fn get_quest_id(&self) -> u32 {
        self.quest_id
    }

    fn on_dialog(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        let npc_id = env.target_template_id.unwrap_or(0);

        if npc_id == self.data.start_npc_id {
            match env.dialog {
                QuestDialog::StartDialog => {
                    if state.status == QuestStatus::None {
                        return HandlerResult::Success;
                    }
                }
                QuestDialog::AcceptQuest => {
                    state.set_status(QuestStatus::Start);
                    state.set_quest_var_by_index(0, 0);
                    return HandlerResult::Success;
                }
                _ => {}
            }
        }

        if npc_id == self.data.end_npc_id && state.status == QuestStatus::Reward {
            match env.dialog {
                QuestDialog::SelectReward | QuestDialog::SelectReward1 => {
                    state.set_status(QuestStatus::Complete);
                    state.complete_count += 1;
                    return HandlerResult::Success;
                }
                _ => {}
            }
        }

        HandlerResult::Unknown
    }

    fn on_kill(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if state.status != QuestStatus::Start {
            return HandlerResult::Unknown;
        }

        let target_id = env.target_template_id.unwrap_or(0);
        for spawned in &self.data.spawned_monsters {
            if spawned.npc_id == target_id {
                state.set_status(QuestStatus::Reward);
                return HandlerResult::Success;
            }
        }

        HandlerResult::Unknown
    }
}
