//! Tipos, Estados e Códigos de Erro de Restrições (Restrictions Subsystem).

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum CreatureState {
    #[default]
    Normal = 0,
    Resting = 1,
    Dead = 2,
    FloatingCorpse = 3,
    PrivateShop = 4,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum PlayerMode {
    #[default]
    Normal = 0,
    Windstream = 1,
    FlyTeleport = 2,
    Flying = 3,
    Gliding = 4,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct AbnormalState(pub u32);

impl AbnormalState {
    pub const NONE: Self = Self(0);
    pub const CANT_ATTACK_STATE: Self = Self(1 << 0);
    pub const SILENCE: Self = Self(1 << 1);
    pub const BIND: Self = Self(1 << 2);
    pub const FEAR: Self = Self(1 << 3);
    pub const HIDE: Self = Self(1 << 4);
    pub const STUN: Self = Self(1 << 5);
    pub const PARALYZE: Self = Self(1 << 6);
    pub const SLEEP: Self = Self(1 << 7);
    pub const SHAPECHANGE: Self = Self(1 << 8);

    #[inline]
    pub fn contains(&self, other: Self) -> bool {
        (self.0 & other.0) != 0
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum SkillType {
    #[default]
    Physical,
    Magical,
}

#[derive(Debug, Clone, Default)]
pub struct SkillInfo {
    pub skill_id: u32,
    pub skill_type: SkillType,
    pub has_evade_effect: bool,
    pub has_resurrect_effect: bool,
    pub is_hide_skill: bool,
    pub is_recall_instant: bool,
    pub is_disabled: bool,
    pub is_enemy_target: bool,
}

#[derive(Debug, Clone, Default)]
pub struct ItemInfo {
    pub item_id: u32,
    pub is_arrow: bool,
    pub area_restriction: Option<String>,
}

#[derive(Debug, Clone, Default)]
pub struct PlayerState {
    pub object_id: u32,
    pub name: String,
    pub race: u8,            // 0 = Elyos, 1 = Asmodian
    pub level: u8,
    pub is_online: bool,
    pub is_dead: bool,
    pub state: CreatureState,
    pub mode: PlayerMode,
    pub abnormal_state: AbnormalState,
    pub is_casting: bool,
    pub is_in_combat: bool,
    pub is_trading: bool,
    pub is_gagged: bool,
    pub is_in_prison: bool,
    pub is_transformed: bool,
    pub is_avatar_transformed: bool,
    pub is_protection_active: bool,
    pub is_arrow_equipped: bool,
    pub is_bow_equipped: bool,
    pub is_under_stance: bool,
    pub current_zone: String,
    pub is_in_fortress_zone: bool,
    pub is_in_item_use_zone: bool,
    pub group_id: Option<u32>,
    pub is_group_leader: bool,
    pub group_member_count: usize,
    pub alliance_id: Option<u32>,
    pub is_alliance_leader: bool,
    pub alliance_member_count: usize,
}

#[derive(Debug, Clone, Default)]
pub struct TargetState {
    pub object_id: u32,
    pub name: String,
    pub race: u8,
    pub is_player: bool,
    pub is_dead: bool,
    pub state: CreatureState,
    pub mode: PlayerMode,
    pub is_in_combat: bool,
    pub is_protection_active: bool,
    pub is_transformed: bool,
    pub is_avatar_transformed: bool,
    pub is_trading: bool,
    pub group_id: Option<u32>,
    pub is_group_leader: bool,
    pub alliance_id: Option<u32>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RestrictionError {
    TargetLost,
    NoFlyRestriction,
    CannotCastInCurrentStance,
    CannotActInAbnormalState,
    CannotCastMagicWhileSilenced,
    CannotCastPhysicalInFearOrBind,
    SkillDisabled,
    CannotCastInShapechange,
    CannotAttackNoArrow,
    CannotAttackInCurrentStance,
    TargetNotEnemy,
    TargetAlreadyDead,
    PartnerAlreadyTrading,
    CannotTradeWhileInvisible,
    CannotTradeWhenDead,
    CannotUseItemInCurrentStance,
    CannotUseItemWhilePathFlying,
    CannotUseItemInCurrentZone,
    PartyFull,
    PartyOnlyLeaderCanInvite,
    PartyNoUserToInvite,
    PartyCantInviteOtherRace,
    PartyCantInviteSelf,
    PartyTargetDead,
    PartyCantInviteWhenDead,
    PartyAlreadyMemberOfOurParty,
    PartyAlreadyMemberOfOtherParty,
    PartyTargetBusy,
    AllianceFull,
    AllianceOnlyLeaderCanInvite,
    AllianceAlreadyMemberOfOurAlliance,
    AllianceAlreadyMemberOfOtherAlliance,
    ChatGagged,
    PrisonRestricted,
    ShutdownRestricted,
}
