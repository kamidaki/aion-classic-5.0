//! Exceções e Erros em Diálogos de Missão (QuestDialogException - Padrão Java Aion Classic 2.8 / 4.5)

use std::fmt;

#[derive(Debug, Clone)]
pub struct QuestDialogException {
    pub message: String,
    pub quest_id: u32,
    pub dialog_id: u32,
}

impl QuestDialogException {
    pub fn new(quest_id: u32, dialog_id: u32, message: &str) -> Self {
        Self {
            quest_id,
            dialog_id,
            message: message.to_string(),
        }
    }
}

impl fmt::Display for QuestDialogException {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "QuestDialogException (Quest #{}, Dialog #{}): {}",
            self.quest_id, self.dialog_id, self.message
        )
    }
}

impl std::error::Error for QuestDialogException {}
