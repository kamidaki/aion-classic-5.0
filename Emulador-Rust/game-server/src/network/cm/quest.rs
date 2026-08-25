//! Pacotes Client de Diálogos, Missões e Coleta (CM)

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ShowDialog {
    pub target_obj_id: u32,
    pub dialog_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DialogSelect {
    pub target_obj_id: u32,
    pub dialog_id: u32,
    pub quest_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Gather {
    pub target_obj_id: u32,
    pub action: u8,
}
