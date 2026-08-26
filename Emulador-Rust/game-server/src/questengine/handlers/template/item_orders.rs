//! Handler de Missão de Entrega e Pedidos de Itens (ItemOrders - Padrão Java Aion Classic 2.8 / 4.5)

use crate::questengine::handlers::handler_result::HandlerResult;
use crate::questengine::handlers::models::ItemOrdersData;
use crate::questengine::handlers::quest_handler::QuestHandler;
use crate::questengine::model::{QuestDialog, QuestEnv, QuestState, QuestStatus};

#[derive(Debug, Clone)]
pub struct ItemOrders {
    pub quest_id: u32,
    pub data: ItemOrdersData,
}

impl ItemOrders {
    pub fn new(quest_id: u32, data: ItemOrdersData) -> Self {
        Self { quest_id, data }
    }
}

impl QuestHandler for ItemOrders {
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
                _ => {}
            }
        }

        if npc_id == self.data.end_npc_id && state.status == QuestStatus::Start {
            match env.dialog {
                QuestDialog::StartDialog => {
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
