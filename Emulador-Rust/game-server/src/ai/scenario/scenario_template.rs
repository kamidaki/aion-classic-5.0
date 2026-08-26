//! Template de Cenários Scriptados de IA (ScenarioTemplate - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct ScenarioTemplate {
    pub scenario_id: u32,
    pub name: String,
    pub step_count: u32,
}

impl ScenarioTemplate {
    pub fn new(scenario_id: u32, name: impl Into<String>, step_count: u32) -> Self {
        Self {
            scenario_id,
            name: name.into(),
            step_count,
        }
    }
}
