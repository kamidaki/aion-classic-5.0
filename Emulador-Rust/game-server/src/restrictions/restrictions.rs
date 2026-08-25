//! Interface central de Restrições (Restrictions Trait).

use super::types::{ItemInfo, PlayerState, RestrictionError, SkillInfo, TargetState};

pub trait Restrictions: Send + Sync {
    fn can_attack(&self, player: &PlayerState, target: Option<&TargetState>) -> Result<(), RestrictionError>;
    fn can_affect_by_skill(&self, player: &PlayerState, target: Option<&TargetState>, skill: &SkillInfo) -> Result<(), RestrictionError>;
    fn can_use_skill(&self, player: &PlayerState, skill: &SkillInfo) -> Result<(), RestrictionError>;
    fn can_chat(&self, player: &PlayerState) -> Result<(), RestrictionError>;
    fn can_invite_to_group(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError>;
    fn can_leave_group(&self, player: &PlayerState) -> Result<(), RestrictionError>;
    fn can_invite_to_alliance(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError>;
    fn can_change_equip(&self, player: &PlayerState) -> Result<(), RestrictionError>;
    fn can_use_warehouse(&self, player: &PlayerState) -> Result<(), RestrictionError>;
    fn can_trade(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError>;
    fn can_use_item(&self, player: &PlayerState, item: &ItemInfo) -> Result<(), RestrictionError>;
    fn can_open_private_shop(&self, player: &PlayerState) -> Result<(), RestrictionError>;
    fn can_duel(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError>;
}
