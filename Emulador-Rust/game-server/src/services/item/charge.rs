//! Serviço de Potencializadores / Conditioning / Augmentation (ItemChargeService).
//! Controla pontos de condicionamento, consumo em combate e concessão de atributos bônus.

use crate::data::item::ItemTemplate;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct ChargeState {
    pub current_points: u32,
    pub max_points: u32,
    pub charge_level: u8, // 0 = Inativo, 1 = Nível 1, 2 = Nível 2
}

pub struct ItemChargeService;

impl ItemChargeService {
    pub fn new_charge_state(item: &ItemTemplate) -> Option<ChargeState> {
        if item.modifiers.charge_capacity > 0 {
            Some(ChargeState {
                current_points: 0,
                max_points: item.modifiers.charge_capacity,
                charge_level: 0,
            })
        } else {
            None
        }
    }

    /// Recarrega pontos de condicionamento em um NPC ou item consumível.
    pub fn recharge(state: &mut ChargeState, points: u32) {
        state.current_points = (state.current_points + points).min(state.max_points);
        if state.current_points >= state.max_points / 2 {
            state.charge_level = 2;
        } else if state.current_points > 0 {
            state.charge_level = 1;
        } else {
            state.charge_level = 0;
        }
    }

    /// Consome pontos em combate (ex: 1 ponto por ataque ou dano sofrido).
    pub fn consume_point(state: &mut ChargeState, points: u32) -> bool {
        if state.current_points > 0 {
            state.current_points = state.current_points.saturating_sub(points);
            if state.current_points == 0 {
                state.charge_level = 0;
            } else if state.current_points < state.max_points / 2 {
                state.charge_level = 1;
            }
            true
        } else {
            false
        }
    }
}
