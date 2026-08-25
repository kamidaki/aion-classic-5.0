//! Pacote SM_PARTY_INFO

#[derive(Debug, Clone)]
pub struct SmPartyInfo {
    pub party_id: u32,
    pub leader_id: u32,
    pub loot_rule: u8,
}
