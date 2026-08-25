//! Gerenciador Central de Restrições (RestrictionsManager).
//! Avalia a cadeia de restrições em ordem de prioridade (Shutdown -> Prison -> Player).

use super::player_restrictions::PlayerRestrictions;
use super::prison_restrictions::PrisonRestrictions;
use super::shutdown_restrictions::ShutdownRestrictions;
use super::restrictions::Restrictions;
use super::types::{ItemInfo, PlayerState, RestrictionError, SkillInfo, TargetState};

pub struct RestrictionsManager {
    shutdown_restrictions: ShutdownRestrictions,
    prison_restrictions: PrisonRestrictions,
    player_restrictions: PlayerRestrictions,
}

impl RestrictionsManager {
    pub fn new() -> Self {
        Self {
            shutdown_restrictions: ShutdownRestrictions::new(false),
            prison_restrictions: PrisonRestrictions::new(),
            player_restrictions: PlayerRestrictions::new(),
        }
    }

    pub fn set_shutdown_status(&mut self, in_progress: bool) {
        self.shutdown_restrictions.is_shutdown_in_progress = in_progress;
    }

    pub fn can_attack(&self, player: &PlayerState, target: Option<&TargetState>) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_attack(player, target)?;
        self.prison_restrictions.can_attack(player, target)?;
        self.player_restrictions.can_attack(player, target)
    }

    pub fn can_affect_by_skill(&self, player: &PlayerState, target: Option<&TargetState>, skill: &SkillInfo) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_affect_by_skill(player, target, skill)?;
        self.prison_restrictions.can_affect_by_skill(player, target, skill)?;
        self.player_restrictions.can_affect_by_skill(player, target, skill)
    }

    pub fn can_use_skill(&self, player: &PlayerState, skill: &SkillInfo) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_use_skill(player, skill)?;
        self.prison_restrictions.can_use_skill(player, skill)?;
        self.player_restrictions.can_use_skill(player, skill)
    }

    pub fn can_chat(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_chat(player)?;
        self.prison_restrictions.can_chat(player)?;
        self.player_restrictions.can_chat(player)
    }

    pub fn can_invite_to_group(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_invite_to_group(player, target)?;
        self.prison_restrictions.can_invite_to_group(player, target)?;
        self.player_restrictions.can_invite_to_group(player, target)
    }

    pub fn can_leave_group(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_leave_group(player)?;
        self.prison_restrictions.can_leave_group(player)?;
        self.player_restrictions.can_leave_group(player)
    }

    pub fn can_invite_to_alliance(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_invite_to_alliance(player, target)?;
        self.prison_restrictions.can_invite_to_alliance(player, target)?;
        self.player_restrictions.can_invite_to_alliance(player, target)
    }

    pub fn can_change_equip(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_change_equip(player)?;
        self.prison_restrictions.can_change_equip(player)?;
        self.player_restrictions.can_change_equip(player)
    }

    pub fn can_use_warehouse(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_use_warehouse(player)?;
        self.prison_restrictions.can_use_warehouse(player)?;
        self.player_restrictions.can_use_warehouse(player)
    }

    pub fn can_trade(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_trade(player, target)?;
        self.prison_restrictions.can_trade(player, target)?;
        self.player_restrictions.can_trade(player, target)
    }

    pub fn can_use_item(&self, player: &PlayerState, item: &ItemInfo) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_use_item(player, item)?;
        self.prison_restrictions.can_use_item(player, item)?;
        self.player_restrictions.can_use_item(player, item)
    }

    pub fn can_open_private_shop(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_open_private_shop(player)?;
        self.prison_restrictions.can_open_private_shop(player)?;
        self.player_restrictions.can_open_private_shop(player)
    }

    pub fn can_duel(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        self.shutdown_restrictions.can_duel(player, target)?;
        self.prison_restrictions.can_duel(player, target)?;
        self.player_restrictions.can_duel(player, target)
    }
}

impl Default for RestrictionsManager {
    fn default() -> Self {
        Self::new()
    }
}
