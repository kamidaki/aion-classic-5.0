//! Controlador Especializado de Efeitos do Jogador (PlayerEffectController - Padrão Java Aion Classic 2.8 / 4.5)

use super::effect_controller::EffectController;
use super::effects_container::ActiveEffect;

#[derive(Debug, Clone, Default)]
pub struct PlayerEffectController {
    pub base: EffectController,
    pub food_buff: Option<ActiveEffect>,
    pub scroll_buff: Option<ActiveEffect>,
    pub transform_buff: Option<ActiveEffect>,
}

impl PlayerEffectController {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn set_food_buff(&mut self, buff: ActiveEffect) {
        self.food_buff = Some(buff);
    }

    pub fn set_scroll_buff(&mut self, buff: ActiveEffect) {
        self.scroll_buff = Some(buff);
    }

    pub fn set_transform_buff(&mut self, buff: ActiveEffect) {
        self.transform_buff = Some(buff);
    }

    pub fn clear_consumable_buffs(&mut self) {
        self.food_buff = None;
        self.scroll_buff = None;
    }
}
