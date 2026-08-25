//! Gerenciamento de Cooldown e Reentrada em Instâncias (InstanceCooltime / CooldownTracker - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::time::Instant;

#[derive(Debug, Clone)]
pub struct InstanceCooltime {
    pub world_id: u32,
    pub name: String,
    pub cooldown_seconds: u64,
    pub max_entries_daily: u32,
    pub min_level: u16,
    pub max_level: u16,
    pub max_members: u32,
}

impl InstanceCooltime {
    pub fn new(world_id: u32, name: &str, cooldown_seconds: u64, max_entries: u32, min_level: u16, max_level: u16, max_members: u32) -> Self {
        Self {
            world_id,
            name: name.to_string(),
            cooldown_seconds,
            max_entries_daily: max_entries,
            min_level,
            max_level,
            max_members,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct PlayerCooldownEntry {
    pub entries_used: u32,
    pub last_entry: Option<Instant>,
}

#[derive(Debug, Clone, Default)]
pub struct InstanceCooldownTracker {
    // player_id -> (world_id -> PlayerCooldownEntry)
    pub player_cooldowns: HashMap<u32, HashMap<u32, PlayerCooldownEntry>>,
}

impl InstanceCooldownTracker {
    pub fn new() -> Self {
        Self {
            player_cooldowns: HashMap::new(),
        }
    }

    /// Verifica se o jogador pode entrar na masmorra especificada
    pub fn can_enter(
        &self,
        player_id: u32,
        cooltime: &InstanceCooltime,
        now: Instant,
    ) -> Result<(), &'static str> {
        if let Some(map_cds) = self.player_cooldowns.get(&player_id) {
            if let Some(entry) = map_cds.get(&cooltime.world_id) {
                if let Some(last) = entry.last_entry {
                    let elapsed = now.duration_since(last).as_secs();
                    if elapsed < cooltime.cooldown_seconds {
                        return Err("Masmorra em tempo de recarga (Cooldown ativo)");
                    }
                }
                if entry.entries_used >= cooltime.max_entries_daily && cooltime.max_entries_daily > 0 {
                    return Err("Limite de entradas diárias atingido para esta masmorra");
                }
            }
        }
        Ok(())
    }

    /// Registra a entrada do jogador na masmorra
    pub fn record_entry(&mut self, player_id: u32, world_id: u32, now: Instant) {
        let map_cds = self.player_cooldowns.entry(player_id).or_default();
        let entry = map_cds.entry(world_id).or_default();
        entry.entries_used += 1;
        entry.last_entry = Some(now);
    }
}
