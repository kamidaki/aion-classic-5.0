//! Ambiente de Contexto de Evento de Missão (QuestEnv - Padrão Java Aion Classic 2.8 / 4.5)

use super::quest_dialog::QuestDialog;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct QuestEnv {
    pub player_id: u32,
    pub target_obj_id: Option<u32>,
    pub target_template_id: Option<u32>,
    pub quest_id: u32,
    pub dialog: QuestDialog,
    pub extended_vars: HashMap<String, u32>,
}

impl QuestEnv {
    pub fn new(player_id: u32, quest_id: u32) -> Self {
        Self {
            player_id,
            target_obj_id: None,
            target_template_id: None,
            quest_id,
            dialog: QuestDialog::default(),
            extended_vars: HashMap::new(),
        }
    }

    pub fn with_target(mut self, target_obj_id: u32, target_template_id: u32) -> Self {
        self.target_obj_id = Some(target_obj_id);
        self.target_template_id = Some(target_template_id);
        self
    }

    pub fn with_dialog(mut self, dialog: QuestDialog) -> Self {
        self.dialog = dialog;
        self
    }

    pub fn get_var(&self, name: &str) -> u32 {
        self.extended_vars.get(name).copied().unwrap_or(0)
    }

    pub fn set_var(&mut self, name: &str, value: u32) {
        self.extended_vars.insert(name.to_string(), value);
    }
}
