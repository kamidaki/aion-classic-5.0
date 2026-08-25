//! Restrições durante Contagem Regressiva de Desligamento (ShutdownRestrictions).
//! Impede início de trocas, compras em lojas privadas e aberturas de armazém.

use super::restrictions::Restrictions;
use super::types::{ItemInfo, PlayerState, RestrictionError, SkillInfo, TargetState};

pub struct ShutdownRestrictions {
    pub is_shutdown_in_progress: bool,
}

impl ShutdownRestrictions {
    pub fn new(is_shutdown_in_progress: bool) -> Self {
        Self { is_shutdown_in_progress }
    }
}

impl Restrictions for ShutdownRestrictions {
    fn can_attack(&self, _player: &PlayerState, _target: Option<&TargetState>) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_affect_by_skill(&self, _player: &PlayerState, _target: Option<&TargetState>, _skill: &SkillInfo) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_use_skill(&self, _player: &PlayerState, _skill: &SkillInfo) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_chat(&self, _player: &PlayerState) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_invite_to_group(&self, _player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_leave_group(&self, _player: &PlayerState) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_invite_to_alliance(&self, _player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_change_equip(&self, _player: &PlayerState) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_use_warehouse(&self, _player: &PlayerState) -> Result<(), RestrictionError> {
        if self.is_shutdown_in_progress {
            return Err(RestrictionError::ShutdownRestricted);
        }
        Ok(())
    }

    fn can_trade(&self, _player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        if self.is_shutdown_in_progress {
            return Err(RestrictionError::ShutdownRestricted);
        }
        Ok(())
    }

    fn can_use_item(&self, _player: &PlayerState, _item: &ItemInfo) -> Result<(), RestrictionError> {
        Ok(())
    }

    fn can_open_private_shop(&self, _player: &PlayerState) -> Result<(), RestrictionError> {
        if self.is_shutdown_in_progress {
            return Err(RestrictionError::ShutdownRestricted);
        }
        Ok(())
    }

    fn can_duel(&self, _player: &PlayerState, _target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        Ok(())
    }
}
