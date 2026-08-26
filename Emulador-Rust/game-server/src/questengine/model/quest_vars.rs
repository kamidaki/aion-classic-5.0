//! Variáveis de Progresso da Missão (QuestVars - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Default)]
pub struct QuestVars {
    pub var_0: u32,
    pub var_1: u32,
    pub var_2: u32,
    pub var_3: u32,
    pub var_4: u32,
    pub var_5: u32,
}

impl QuestVars {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn get_var(&self, index: usize) -> u32 {
        match index {
            0 => self.var_0,
            1 => self.var_1,
            2 => self.var_2,
            3 => self.var_3,
            4 => self.var_4,
            5 => self.var_5,
            _ => 0,
        }
    }

    pub fn set_var(&mut self, index: usize, value: u32) {
        match index {
            0 => self.var_0 = value,
            1 => self.var_1 = value,
            2 => self.var_2 = value,
            3 => self.var_3 = value,
            4 => self.var_4 = value,
            5 => self.var_5 = value,
            _ => {}
        }
    }
}
