//! Handler de Missões de Ordens de Ofício (WorkOrders - Padrão Java Aion Classic 2.8 / 4.5)

use crate::questengine::handlers::handler_result::HandlerResult;
use crate::questengine::handlers::models::WorkOrdersData;
use crate::questengine::handlers::quest_handler::QuestHandler;
use crate::questengine::model::{QuestDialog, QuestEnv, QuestState, QuestStatus};

#[derive(Debug, Clone)]
pub struct WorkOrders {
    pub quest_id: u32,
    pub data: WorkOrdersData,
}

impl WorkOrders {
    pub fn new(quest_id: u32, data: WorkOrdersData) -> Self {
        Self { quest_id, data }
    }
}

impl QuestHandler for WorkOrders {
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
                    return HandlerResult::Success;
                }
                QuestDialog::SelectReward | QuestDialog::SelectReward1 => {
                    if state.status == QuestStatus::Reward {
                        state.set_status(QuestStatus::Complete);
                        state.complete_count += 1;
                        return HandlerResult::Success;
                    }
                }
                _ => {}
            }
        }

        HandlerResult::Unknown
    }
}
