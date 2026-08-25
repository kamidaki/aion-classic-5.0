//! Sistema de Petições e Suporte GM (Petition / PetitionType - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum PetitionStatus {
    #[default]
    Pending,
    InProgress,
    Resolved,
    Rejected,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum PetitionType {
    #[default]
    CharacterStuck,
    BugReport,
    QuestIssue,
    Harassment,
    GeneralInquiry,
}

#[derive(Debug, Clone)]
pub struct Petition {
    pub petition_id: u32,
    pub player_id: u32,
    pub player_name: String,
    pub petition_type: PetitionType,
    pub title: String,
    pub message: String,
    pub status: PetitionStatus,
    pub created_at: Instant,
    pub responder_gm_id: Option<u32>,
}
