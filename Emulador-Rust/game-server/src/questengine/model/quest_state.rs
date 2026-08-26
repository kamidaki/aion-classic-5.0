//! Estado de Progresso de uma Missão por Jogador (QuestState - Padrão Java Aion Classic 2.8 / 4.5)

use super::quest_status::QuestStatus;
use super::quest_vars::QuestVars;
use super::quest_timer::QuestTimer;

#[derive(Debug, Clone)]
pub struct QuestState {
    pub quest_id: u32,
    pub status: QuestStatus,
    pub quest_vars: QuestVars,
    pub complete_count: u32,
    pub reward: u32,
    pub timer: Option<QuestTimer>,
}

impl QuestState {
    pub fn new(quest_id: u32) -> Self {
        Self {
            quest_id,
            status: QuestStatus::None,
            quest_vars: QuestVars::new(),
            complete_count: 0,
            reward: 0,
            timer: None,
        }
    }

    pub fn is_started(&self) -> bool {
        self.status == QuestStatus::Start
    }

    pub fn is_reward(&self) -> bool {
        self.status == QuestStatus::Reward
    }

    pub fn is_complete(&self) -> bool {
        self.status == QuestStatus::Complete
    }

    pub fn get_quest_var_by_index(&self, index: usize) -> u32 {
        self.quest_vars.get_var(index)
    }

    pub fn set_quest_var_by_index(&mut self, index: usize, value: u32) {
        self.quest_vars.set_var(index, value);
    }

    pub fn set_status(&mut self, status: QuestStatus) {
        self.status = status;
    }

    pub fn set_reward(&mut self, reward: u32) {
        self.reward = reward;
    }
}
