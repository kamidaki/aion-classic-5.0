//! Regras de Fusão de Armas de Duas Mãos (Armsfusion / Arms Combining) do Aion Classic.

#[derive(Debug, Clone, Default)]
pub struct ItemComposeTemplate {
    pub id: u32,
    pub name: String,
    pub group_desc: String,
    pub fee: u64,
    pub same_rate: u32,
    pub same_result: String,
    pub up_rate: u32,
    pub up_result: String,
    pub top_rate: u32,
    pub top_result: String,
}
