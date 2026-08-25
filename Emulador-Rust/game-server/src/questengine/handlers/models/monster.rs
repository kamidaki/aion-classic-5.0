//! Dados de Monstro Alvo para Caça (Monster - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct Monster {
    pub npc_id: u32,
    pub var_index: usize,
    pub count: u32,
    pub end_var: u32,
}

impl Monster {
    pub fn new(npc_id: u32, var_index: usize, count: u32, end_var: u32) -> Self {
        Self {
            npc_id,
            var_index,
            count,
            end_var,
        }
    }
}
