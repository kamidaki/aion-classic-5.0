//! Ações Periódicas de HP, MP e DP (Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::skillengine::periodicaction::periodic_action::PeriodicAction;

/// Dreno / Dano Periódico de HP (DoT - Bleed / Poison)
#[derive(Debug, Clone)]
pub struct HpUsePeriodicAction {
    pub value: i32,
}

impl PeriodicAction for HpUsePeriodicAction {
    fn execute_tick(&self, target: &mut Character) -> Result<(), &'static str> {
        target.stats.hp.update(-self.value);
        Ok(())
    }
}

/// Dreno / Regeneração Periódica de MP
#[derive(Debug, Clone)]
pub struct MpUsePeriodicAction {
    pub value: i32,
}

impl PeriodicAction for MpUsePeriodicAction {
    fn execute_tick(&self, target: &mut Character) -> Result<(), &'static str> {
        target.stats.mp.update(self.value);
        Ok(())
    }
}

/// Dreno / Regeneração Periódica de DP
#[derive(Debug, Clone)]
pub struct DpUsePeriodicAction {
    pub value: i32,
}

impl PeriodicAction for DpUsePeriodicAction {
    fn execute_tick(&self, target: &mut Character) -> Result<(), &'static str> {
        target.stats.dp.update(self.value);
        Ok(())
    }
}
