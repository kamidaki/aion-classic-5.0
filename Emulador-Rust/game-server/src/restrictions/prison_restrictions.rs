//! Restrições de Prisão / Cadeia (PrisonRestrictions).
//! Bloqueia combate, chat, troca, armazém e teleporte enquanto o jogador cumpre pena na prisão.

use super::restrictions::Restrictions;
use super::types::{ItemInfo, PlayerState, RestrictionError, SkillInfo, TargetState};

pub struct PrisonRestrictions;

impl PrisonRestrictions {
    pub fn new() -> Self {
        Self
    }
}

impl Restrictions for PrisonRestrictions {
    fn can_attack(&self, player: &PlayerState, _target: Option<&TargetState>) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_affect_by_skill(&self, player: &PlayerState, _target: Option<&TargetState>, _skill: &SkillInfo) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_use_skill(&self, player: &PlayerState, _skill: &SkillInfo) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_chat(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_invite_to_group(&self, player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_leave_group(&self, _player: &PlayerState) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_invite_to_alliance(&self, player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_change_equip(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_use_warehouse(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_trade(&self, player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_use_item(&self, player: &PlayerState, _item: &ItemInfo) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_open_private_shop(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }

    fn can_duel(&self, player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        if player.is_in_prison {
            return Err(RestrictionError::PrisonRestricted);
        }
        Ok(())
    }
}
