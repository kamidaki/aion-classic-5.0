//! Pacote CM_DIALOG_SELECT

#[derive(Debug, Clone)]
pub struct CmDialogSelect {
    pub target_npc_obj_id: u32,
    pub dialog_id: u32,
    pub quest_id: Option<u32>,
}
