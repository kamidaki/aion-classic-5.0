//! Handler de Missão de Oferendas na Fonte Mágica (FountainRewards - Padrão Java Aion Classic 2.8 / 4.5)

use crate::questengine::handlers::handler_result::HandlerResult;
use crate::questengine::handlers::models::FountainRewardsData;
use crate::questengine::handlers::quest_handler::QuestHandler;
use crate::questengine::model::{QuestDialog, QuestEnv, QuestState, QuestStatus};

#[derive(Debug, Clone)]
pub struct FountainRewards {
    pub quest_id: u32,
    pub data: FountainRewardsData,
}

impl FountainRewards {
    pub fn new(quest_id: u32, data: FountainRewardsData) -> Self {
        Self { quest_id, data }
    }
}

impl QuestHandler for FountainRewards {
    fn get_quest_id(&self) -> u32 {
        self.quest_id
    }

    fn on_dialog(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        let npc_id = env.target_template_id.unwrap_or(0);

        if npc_id == self.data.fountain_npc_id {
            match env.dialog {
                QuestDialog::StartDialog | QuestDialog::UseObject => {
                    state.set_status(QuestStatus::Reward);
                    return HandlerResult::Success;
                }
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
}
