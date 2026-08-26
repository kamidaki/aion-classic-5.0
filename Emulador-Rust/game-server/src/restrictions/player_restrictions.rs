//! Implementação de Restrições Padrão de Jogador (PlayerRestrictions).
//! Implementa 100% das regras e verificações do emulador oficial Java Classic (2.4 / 2.8).

use super::restrictions::Restrictions;
use super::types::{
    AbnormalState, CreatureState, ItemInfo, PlayerMode, PlayerState, RestrictionError,
    SkillInfo, SkillType, TargetState,
};

pub struct PlayerRestrictions;

impl PlayerRestrictions {
    pub fn new() -> Self {
        Self
    }

    fn check_fly_player(player: &PlayerState) -> bool {
        !matches!(player.mode, PlayerMode::FlyTeleport | PlayerMode::Windstream)
    }

    fn check_fly_target(target: &TargetState) -> bool {
        !matches!(target.mode, PlayerMode::FlyTeleport | PlayerMode::Windstream)
    }
}

impl Restrictions for PlayerRestrictions {
    fn can_attack(&self, player: &PlayerState, target: Option<&TargetState>) -> Result<(), RestrictionError> {
        let Some(tgt) = target else {
            return Err(RestrictionError::TargetLost);
        };

        if !Self::check_fly_player(player) || !Self::check_fly_target(tgt) {
            return Err(RestrictionError::NoFlyRestriction);
        }

        if tgt.is_dead || matches!(tgt.state, CreatureState::Dead | CreatureState::FloatingCorpse) {
            return Err(RestrictionError::TargetAlreadyDead);
        }

        if player.state == CreatureState::Resting {
            return Err(RestrictionError::CannotAttackInCurrentStance);
        }

        if player.is_bow_equipped && !player.is_arrow_equipped {
            return Err(RestrictionError::CannotAttackNoArrow);
        }

        if player.abnormal_state.contains(AbnormalState::CANT_ATTACK_STATE) {
            return Err(RestrictionError::CannotActInAbnormalState);
        }

        // Validação de facção inimiga (Elyos vs Asmodian)
        if tgt.is_player && player.race == tgt.race {
            return Err(RestrictionError::TargetNotEnemy);
        }

        Ok(())
    }

    fn can_affect_by_skill(&self, player: &PlayerState, target: Option<&TargetState>, skill: &SkillInfo) -> Result<(), RestrictionError> {
        if !Self::check_fly_player(player) {
            return Err(RestrictionError::NoFlyRestriction);
        }

        let Some(tgt) = target else {
            return Err(RestrictionError::TargetLost);
        };

        if tgt.is_player && skill.is_enemy_target && tgt.is_protection_active {
            return Err(RestrictionError::TargetNotEnemy);
        }

        if !Self::check_fly_target(tgt) {
            return Err(RestrictionError::NoFlyRestriction);
        }

        if tgt.is_dead && !skill.has_resurrect_effect {
            return Err(RestrictionError::TargetLost);
        }

        if skill.has_resurrect_effect && (!tgt.is_player || !tgt.is_dead) {
            return Err(RestrictionError::TargetLost);
        }

        if !skill.has_evade_effect && player.abnormal_state.contains(AbnormalState::CANT_ATTACK_STATE) {
            return Err(RestrictionError::CannotActInAbnormalState);
        }

        if player.state == CreatureState::PrivateShop {
            return Err(RestrictionError::CannotUseItemInCurrentStance);
        }

        if tgt.is_player && tgt.is_avatar_transformed && skill.is_hide_skill {
            return Err(RestrictionError::CannotActInAbnormalState);
        }

        Ok(())
    }

    fn can_use_skill(&self, player: &PlayerState, skill: &SkillInfo) -> Result<(), RestrictionError> {
        if !Self::check_fly_player(player) {
            return Err(RestrictionError::NoFlyRestriction);
        }

        if player.is_casting {
            return Err(RestrictionError::CannotCastInCurrentStance);
        }

        if player.state == CreatureState::Resting {
            return Err(RestrictionError::CannotCastInCurrentStance);
        }

        if player.abnormal_state.contains(AbnormalState::CANT_ATTACK_STATE) && !skill.has_evade_effect {
            return Err(RestrictionError::CannotActInAbnormalState);
        }

        if skill.skill_type == SkillType::Magical && player.abnormal_state.contains(AbnormalState::SILENCE) && !skill.has_evade_effect {
            return Err(RestrictionError::CannotCastMagicWhileSilenced);
        }

        if skill.skill_type == SkillType::Physical && (player.abnormal_state.contains(AbnormalState::BIND) || player.abnormal_state.contains(AbnormalState::FEAR)) {
            return Err(RestrictionError::CannotCastPhysicalInFearOrBind);
        }

        if skill.is_disabled {
            return Err(RestrictionError::SkillDisabled);
        }

        if player.is_transformed && player.abnormal_state.contains(AbnormalState::SHAPECHANGE) {
            return Err(RestrictionError::CannotCastInShapechange);
        }

        Ok(())
    }

    fn can_chat(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if !player.is_online || player.is_gagged {
            return Err(RestrictionError::ChatGagged);
        }
        Ok(())
    }

    fn can_invite_to_group(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        if player.group_member_count >= 6 {
            return Err(RestrictionError::PartyFull);
        }

        if player.group_id.is_some() && !player.is_group_leader {
            return Err(RestrictionError::PartyOnlyLeaderCanInvite);
        }

        let Some(tgt) = target else {
            return Err(RestrictionError::PartyNoUserToInvite);
        };

        if tgt.race != player.race {
            return Err(RestrictionError::PartyCantInviteOtherRace);
        }

        if tgt.object_id == player.object_id {
            return Err(RestrictionError::PartyCantInviteSelf);
        }

        if tgt.is_dead {
            return Err(RestrictionError::PartyTargetDead);
        }

        if player.is_dead {
            return Err(RestrictionError::PartyCantInviteWhenDead);
        }

        if player.group_id.is_some() && tgt.group_id == player.group_id {
            return Err(RestrictionError::PartyAlreadyMemberOfOurParty);
        }

        if tgt.group_id.is_some() {
            return Err(RestrictionError::PartyAlreadyMemberOfOtherParty);
        }

        if !Self::check_fly_player(player) || !Self::check_fly_player(tgt) {
            return Err(RestrictionError::PartyTargetBusy);
        }

        Ok(())
    }

    fn can_leave_group(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if !Self::check_fly_player(player) && player.group_id.is_some() {
            return Err(RestrictionError::PartyTargetBusy);
        }
        Ok(())
    }

    fn can_invite_to_alliance(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        let Some(tgt) = target else {
            return Err(RestrictionError::PartyNoUserToInvite);
        };

        if tgt.race != player.race {
            return Err(RestrictionError::PartyCantInviteOtherRace);
        }

        if player.alliance_member_count >= 24 {
            return Err(RestrictionError::AllianceFull);
        }

        if player.alliance_id.is_some() && !player.is_alliance_leader {
            return Err(RestrictionError::AllianceOnlyLeaderCanInvite);
        }

        if tgt.object_id == player.object_id {
            return Err(RestrictionError::PartyCantInviteSelf);
        }

        if tgt.is_dead || player.is_dead {
            return Err(RestrictionError::PartyCantInviteWhenDead);
        }

        if player.alliance_id.is_some() && tgt.alliance_id == player.alliance_id {
            return Err(RestrictionError::AllianceAlreadyMemberOfOurAlliance);
        }

        if tgt.alliance_id.is_some() {
            return Err(RestrictionError::AllianceAlreadyMemberOfOtherAlliance);
        }

        Ok(())
    }

    fn can_change_equip(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if player.is_under_stance || player.abnormal_state.contains(AbnormalState::CANT_ATTACK_STATE) {
            return Err(RestrictionError::CannotActInAbnormalState);
        }
        Ok(())
    }

    fn can_use_warehouse(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if !player.is_online || player.is_trading {
            return Err(RestrictionError::PartnerAlreadyTrading);
        }
        Ok(())
    }

    fn can_trade(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        if !player.is_online || player.is_trading {
            return Err(RestrictionError::PartnerAlreadyTrading);
        }

        if player.abnormal_state.contains(AbnormalState::HIDE) {
            return Err(RestrictionError::CannotTradeWhileInvisible);
        }

        if let Some(tgt) = target {
            if tgt.is_trading {
                return Err(RestrictionError::PartnerAlreadyTrading);
            }
            if tgt.is_dead {
                return Err(RestrictionError::CannotTradeWhenDead);
            }
        }

        Ok(())
    }

    fn can_use_item(&self, player: &PlayerState, item: &ItemInfo) -> Result<(), RestrictionError> {
        if !player.is_online {
            return Err(RestrictionError::TargetLost);
        }

        if player.state == CreatureState::Resting {
            return Err(RestrictionError::CannotUseItemInCurrentStance);
        }

        if player.abnormal_state.contains(AbnormalState::CANT_ATTACK_STATE) {
            return Err(RestrictionError::CannotActInAbnormalState);
        }

        if !Self::check_fly_player(player) {
            return Err(RestrictionError::CannotUseItemWhilePathFlying);
        }

        if let Some(ref zone_req) = item.area_restriction {
            if zone_req == "_ABYSS_CASTLE_AREA_" {
                if !player.is_in_fortress_zone {
                    return Err(RestrictionError::CannotUseItemInCurrentZone);
                }
            } else if zone_req.starts_with("IDARENA_") {
                if !player.is_in_item_use_zone {
                    return Err(RestrictionError::CannotUseItemInCurrentZone);
                }
            } else if !player.current_zone.is_empty() && &player.current_zone != zone_req {
                return Err(RestrictionError::CannotUseItemInCurrentZone);
            }
        }

        Ok(())
    }

    fn can_open_private_shop(&self, player: &PlayerState) -> Result<(), RestrictionError> {
        if player.is_in_combat || !Self::check_fly_player(player) || player.state == CreatureState::Resting || player.is_dead {
            return Err(RestrictionError::CannotActInAbnormalState);
        }
        Ok(())
    }

    fn can_duel(&self, player: &PlayerState, target: Option<&PlayerState>) -> Result<(), RestrictionError> {
        let Some(tgt) = target else {
            return Err(RestrictionError::TargetLost);
        };

        if player.race != tgt.race || tgt.is_dead || player.is_dead || !Self::check_fly_player(player) || !Self::check_fly_player(tgt) {
            return Err(RestrictionError::TargetNotEnemy);
        }

        Ok(())
    }
}
