//! Catálogo Oficial de IDs de Mensagens do Sistema (SystemMessageId - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SystemMessageId {
    WelcomeToAion = 1300000,
    SkillCooldown = 1300010,
    CannotUseInFlight = 1300020,
    InventoryFull = 1300030,
    NotEnoughKinah = 1300040,
    TargetTooFar = 1300050,
    TargetInvalid = 1300060,
    DuelDeclined = 1300070,
    DuelVictory = 1300080,
    DuelDefeat = 1300090,
    GroupInvited = 1300100,
    GroupJoined = 1300110,
    GroupLeft = 1300120,
    InstanceEntryDenied = 1400360,
    ItemEnchantSuccess = 1400400,
    ItemEnchantFailed = 1400401,
}

impl SystemMessageId {
    pub fn id(&self) -> u32 {
        *self as u32
    }
}
