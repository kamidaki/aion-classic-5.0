//! Pacote SM_PARTY_MEMBER_INFO

#[derive(Debug, Clone)]
pub struct SmPartyMemberInfo {
    pub member_id: u32,
    pub name: String,
    pub cur_hp: i32,
    pub max_hp: i32,
    pub cur_mp: i32,
    pub max_mp: i32,
}
