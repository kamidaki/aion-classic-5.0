//! Modelos de Drops e Tabelas de Recompensas de Monstros (DropTemplate / NpcDrop - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct DropTemplateModel {
    pub item_id: u32,
    pub min_amount: u32,
    pub max_amount: u32,
    pub chance_percent: f32,
}

#[derive(Debug, Clone, Default)]
pub struct NpcDropModel {
    pub npc_id: u32,
    pub drops: Vec<DropTemplateModel>,
}
