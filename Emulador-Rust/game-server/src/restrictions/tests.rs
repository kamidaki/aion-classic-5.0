#[cfg(test)]
mod tests {
    use crate::restrictions::{
        AbnormalState, CreatureState, ItemInfo, PlayerMode, PlayerState, RestrictionError,
        RestrictionsManager, SkillInfo, SkillType, TargetState,
    };

    fn make_test_player() -> PlayerState {
        PlayerState {
            object_id: 10001,
            name: "DaevaOne".to_string(),
            race: 0, // Elyos
            level: 50,
            is_online: true,
            is_dead: false,
            state: CreatureState::Normal,
            mode: PlayerMode::Normal,
            abnormal_state: AbnormalState::NONE,
            is_casting: false,
            is_in_combat: false,
            is_trading: false,
            is_gagged: false,
            is_in_prison: false,
            is_transformed: false,
            is_avatar_transformed: false,
            is_protection_active: false,
            is_arrow_equipped: true,
            is_bow_equipped: false,
            is_under_stance: false,
            current_zone: "Poeta".to_string(),
            is_in_fortress_zone: false,
            is_in_item_use_zone: false,
            group_id: None,
            is_group_leader: false,
            group_member_count: 0,
            alliance_id: None,
            is_alliance_leader: false,
            alliance_member_count: 0,
        }
    }

    fn make_test_target() -> TargetState {
        TargetState {
            object_id: 20001,
            name: "AsmodianEnemy".to_string(),
            race: 1, // Asmodian
            is_player: true,
            is_dead: false,
            state: CreatureState::Normal,
            mode: PlayerMode::Normal,
            is_in_combat: false,
            is_protection_active: false,
            is_transformed: false,
            is_avatar_transformed: false,
            is_trading: false,
            group_id: None,
            is_group_leader: false,
            alliance_id: None,
        }
    }

    #[test]
    fn test_cannot_attack_without_arrows_when_bow_equipped() {
        let manager = RestrictionsManager::new();
        let mut player = make_test_player();
        let target = make_test_target();

        player.is_bow_equipped = true;
        player.is_arrow_equipped = false;

        assert_eq!(
            manager.can_attack(&player, Some(&target)),
            Err(RestrictionError::CannotAttackNoArrow)
        );

        player.is_arrow_equipped = true;
        assert_eq!(manager.can_attack(&player, Some(&target)), Ok(()));
    }

    #[test]
    fn test_cannot_attack_same_race_player() {
        let manager = RestrictionsManager::new();
        let player = make_test_player();
        let mut target = make_test_target();
        target.race = 0; // Same Elyos race

        assert_eq!(
            manager.can_attack(&player, Some(&target)),
            Err(RestrictionError::TargetNotEnemy)
        );
    }

    #[test]
    fn test_flight_restrictions_block_skills_and_attacks() {
        let manager = RestrictionsManager::new();
        let mut player = make_test_player();
        let target = make_test_target();
        let skill = SkillInfo::default();

        player.mode = PlayerMode::Windstream;
        assert_eq!(
            manager.can_attack(&player, Some(&target)),
            Err(RestrictionError::NoFlyRestriction)
        );
        assert_eq!(
            manager.can_use_skill(&player, &skill),
            Err(RestrictionError::NoFlyRestriction)
        );
    }

    #[test]
    fn test_silence_and_bind_restrictions() {
        let manager = RestrictionsManager::new();
        let mut player = make_test_player();

        let mut magic_skill = SkillInfo::default();
        magic_skill.skill_type = SkillType::Magical;

        let mut physical_skill = SkillInfo::default();
        physical_skill.skill_type = SkillType::Physical;

        // Silence blocks magic
        player.abnormal_state = AbnormalState::SILENCE;
        assert_eq!(
            manager.can_use_skill(&player, &magic_skill),
            Err(RestrictionError::CannotCastMagicWhileSilenced)
        );
        assert_eq!(manager.can_use_skill(&player, &physical_skill), Ok(()));

        // Bind blocks physical
        player.abnormal_state = AbnormalState::BIND;
        assert_eq!(
            manager.can_use_skill(&player, &physical_skill),
            Err(RestrictionError::CannotCastPhysicalInFearOrBind)
        );
    }

    #[test]
    fn test_group_invitations_race_and_capacity() {
        let manager = RestrictionsManager::new();
        let mut player = make_test_player();
        let mut target_player = make_test_player();
        target_player.object_id = 10002;

        // Success
        assert_eq!(manager.can_invite_to_group(&player, Some(&target_player)), Ok(()));

        // Cant invite other race
        target_player.race = 1;
        assert_eq!(
            manager.can_invite_to_group(&player, Some(&target_player)),
            Err(RestrictionError::PartyCantInviteOtherRace)
        );

        // Party full
        target_player.race = 0;
        player.group_member_count = 6;
        assert_eq!(
            manager.can_invite_to_group(&player, Some(&target_player)),
            Err(RestrictionError::PartyFull)
        );
    }

    #[test]
    fn test_prison_restrictions_block_actions() {
        let manager = RestrictionsManager::new();
        let mut player = make_test_player();
        let target = make_test_target();

        player.is_in_prison = true;

        assert_eq!(
            manager.can_attack(&player, Some(&target)),
            Err(RestrictionError::PrisonRestricted)
        );
        assert_eq!(
            manager.can_chat(&player),
            Err(RestrictionError::PrisonRestricted)
        );
        assert_eq!(
            manager.can_trade(&player, None),
            Err(RestrictionError::PrisonRestricted)
        );
    }

    #[test]
    fn test_shutdown_restrictions_block_trading_and_warehouse() {
        let mut manager = RestrictionsManager::new();
        let player = make_test_player();

        manager.set_shutdown_status(true);

        assert_eq!(
            manager.can_trade(&player, None),
            Err(RestrictionError::ShutdownRestricted)
        );
        assert_eq!(
            manager.can_use_warehouse(&player),
            Err(RestrictionError::ShutdownRestricted)
        );
    }

    #[test]
    fn test_area_restricted_item_usage() {
        let manager = RestrictionsManager::new();
        let mut player = make_test_player();
        let item = ItemInfo {
            item_id: 186000001,
            is_arrow: false,
            area_restriction: Some("_ABYSS_CASTLE_AREA_".to_string()),
        };

        // Out of fortress zone
        player.is_in_fortress_zone = false;
        assert_eq!(
            manager.can_use_item(&player, &item),
            Err(RestrictionError::CannotUseItemInCurrentZone)
        );

        // Inside fortress zone
        player.is_in_fortress_zone = true;
        assert_eq!(manager.can_use_item(&player, &item), Ok(()));
    }
}
