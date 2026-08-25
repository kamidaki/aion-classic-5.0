//! Gerenciador de Endereços MAC Banidos (BannedMacManager - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashSet;
use std::time::Instant;

#[derive(Debug, Clone)]
pub struct BannedMacEntry {
    pub mac_address: String,
    pub banned_until: Option<Instant>,
    pub reason: String,
}

#[derive(Debug, Default)]
pub struct BannedMacManager {
    banned_macs: HashSet<String>,
}

impl BannedMacManager {
    pub fn new() -> Self {
        Self {
            banned_macs: HashSet::new(),
        }
    }

    pub fn ban_mac(&mut self, mac: &str) {
        self.banned_macs.insert(mac.to_uppercase());
    }

    pub fn unban_mac(&mut self, mac: &str) -> bool {
        self.banned_macs.remove(&mac.to_uppercase())
    }

    pub fn is_banned(&self, mac: &str) -> bool {
        self.banned_macs.contains(&mac.to_uppercase())
    }
}
