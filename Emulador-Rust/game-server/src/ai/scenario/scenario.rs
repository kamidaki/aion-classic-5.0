//! Trait de Cenários Scriptados de IA (AIScenario - Padrão Java Aion Classic 2.8 / 4.5)

pub trait AIScenario: Send + Sync {
    fn on_scenario_start(&mut self);
    fn on_scenario_step(&mut self, step: u32);
    fn on_scenario_finish(&mut self);
}
