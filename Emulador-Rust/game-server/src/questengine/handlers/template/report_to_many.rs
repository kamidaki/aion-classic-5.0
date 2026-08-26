//! Handler de Missão de Reportar a Múltiplos NPCs (ReportToMany - Padrão Java Aion Classic 2.8 / 4.5)

use crate::questengine::handlers::handler_result::HandlerResult;
use crate::questengine::handlers::models::ReportToManyData;
use crate::questengine::handlers::quest_handler::QuestHandler;
use crate::questengine::model::{QuestDialog, QuestEnv, QuestState, QuestStatus};

#[derive(Debug, Clone)]
pub struct ReportToMany {
    pub quest_id: u32,
    pub data: ReportToManyData,
}

impl ReportToMany {
    pub fn new(quest_id: u32, data: ReportToManyData) -> Self {
        Self { quest_id, data }
    }
}

impl QuestHandler for ReportToMany {
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

        let step = state.get_quest_var_by_index(0) as usize;
        if step < self.data.npc_infos.len() {
            let current_target = &self.data.npc_infos[step];
            if npc_id == current_target.npc_id {
                let next_step = (step + 1) as u32;
                state.set_quest_var_by_index(0, next_step);
                if next_step as usize >= self.data.npc_infos.len() {
                    state.set_status(QuestStatus::Reward);
                }
                return HandlerResult::Success;
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
}
