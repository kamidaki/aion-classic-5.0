//! Ações de Consumo de Custos de Habilidades (Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::skillengine::action::action::SkillAction;

/// Ação de Consumo de HP
#[derive(Debug, Clone)]
pub struct HpUseAction {
    pub hp_amount: u32,
}

impl SkillAction for HpUseAction {
    fn execute(&self, caster: &mut Character) -> Result<(), &'static str> {
        let current_hp = caster.stats.hp.current();
        if current_hp <= self.hp_amount as i32 {
            return Err("HP insuficiente para conjurar");
        }
        caster.stats.hp.update(-(self.hp_amount as i32));
        Ok(())
    }
}

/// Ação de Consumo de MP
#[derive(Debug, Clone)]
pub struct MpUseAction {
    pub mp_amount: u32,
}

impl SkillAction for MpUseAction {
    fn execute(&self, caster: &mut Character) -> Result<(), &'static str> {
        let current_mp = caster.stats.mp.current();
        if current_mp < self.mp_amount {
            return Err("MP insuficiente");
        }
        caster.stats.mp.update(-(self.mp_amount as i32));
        Ok(())
    }
}

/// Ação de Consumo de DP
#[derive(Debug, Clone)]
pub struct DpUseAction {
    pub dp_amount: u32,
}

impl SkillAction for DpUseAction {
    fn execute(&self, caster: &mut Character) -> Result<(), &'static str> {
        if (caster.stats.dp.current() as u32) < self.dp_amount {
            return Err("DP insuficiente");
        }
        caster.stats.dp.update(-(self.dp_amount as i32));
        Ok(())
    }
}

/// Ação de Consumo de Item Requerido (ex: Odella Powder, Stigma Shard)
#[derive(Debug, Clone)]
pub struct ItemUseAction {
    pub item_id: u32,
    pub count: u32,
}

impl SkillAction for ItemUseAction {
    fn execute(&self, _caster: &mut Character) -> Result<(), &'static str> {
        // Validação de inventário
        Ok(())
    }
}
