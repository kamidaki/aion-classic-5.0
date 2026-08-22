use super::engine::Coord;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChatChannel {
    Normal = 0,
    Shout = 1,
    Whisper = 2,
    Group = 3,
    Alliance = 4,
    Legion = 5,
    World = 6,
    System = 7,
}

#[derive(Debug, Clone, PartialEq)]
pub enum GmCommand {
    Spawn { npc_id: u32 },
    Teleport { map_id: u32, x: f32, y: f32, z: f32 },
    AddItem { item_id: u32, count: u32 },
    SetLevel { level: u16 },
    GodMode,
    Unknown(String),
}

impl GmCommand {
    pub fn parse(text: &str) -> Option<Self> {
        let trimmed = text.trim();
        if !trimmed.starts_with('.') {
            return None;
        }

        let parts: Vec<&str> = trimmed.split_whitespace().collect();
        if parts.is_empty() {
            return None;
        }

        match parts[0] {
            ".spawn" if parts.len() >= 2 => {
                let npc_id = parts[1].parse().unwrap_or(0);
                Some(GmCommand::Spawn { npc_id })
            }
            ".teleport" if parts.len() >= 5 => {
                let map_id = parts[1].parse().unwrap_or(0);
                let x = parts[2].parse().unwrap_or(0.0);
                let y = parts[3].parse().unwrap_or(0.0);
                let z = parts[4].parse().unwrap_or(0.0);
                Some(GmCommand::Teleport { map_id, x, y, z })
            }
            ".additem" if parts.len() >= 3 => {
                let item_id = parts[1].parse().unwrap_or(0);
                let count = parts[2].parse().unwrap_or(1);
                Some(GmCommand::AddItem { item_id, count })
            }
            ".setlevel" if parts.len() >= 2 => {
                let level = parts[1].parse().unwrap_or(1);
                Some(GmCommand::SetLevel { level })
            }
            ".god" => Some(GmCommand::GodMode),
            _ => Some(GmCommand::Unknown(trimmed.to_string())),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum AbyssRank {
    Soldier9 = 1,
    Soldier8 = 2,
    Soldier7 = 3,
    Soldier6 = 4,
    Soldier5 = 5,
    Soldier4 = 6,
    Soldier3 = 7,
    Soldier2 = 8,
    Soldier1 = 9,
    Star1Officer = 10,
    Star2Officer = 11,
    Star3Officer = 12,
    Star4Officer = 13,
    Star5Officer = 14,
    General = 15,
    GreatGeneral = 16,
    Commander = 17,
    ArmyGovernor = 18,
}

impl AbyssRank {
    pub fn ap_threshold(&self) -> u32 {
        match self {
            AbyssRank::Soldier9 => 0,
            AbyssRank::Soldier8 => 1_200,
            AbyssRank::Soldier7 => 4_220,
            AbyssRank::Soldier6 => 10_990,
            AbyssRank::Soldier5 => 23_500,
            AbyssRank::Soldier4 => 42_700,
            AbyssRank::Soldier3 => 69_700,
            AbyssRank::Soldier2 => 105_600,
            AbyssRank::Soldier1 => 150_800,
            _ => 214_100, // Oficiais e Generais
        }
    }

    pub fn from_ap(ap: u32) -> Self {
        if ap >= 214_100 {
            AbyssRank::Star1Officer
        } else if ap >= 150_800 {
            AbyssRank::Soldier1
        } else if ap >= 105_600 {
            AbyssRank::Soldier2
        } else if ap >= 69_700 {
            AbyssRank::Soldier3
        } else if ap >= 42_700 {
            AbyssRank::Soldier4
        } else if ap >= 23_500 {
            AbyssRank::Soldier5
        } else if ap >= 10_990 {
            AbyssRank::Soldier6
        } else if ap >= 4_220 {
            AbyssRank::Soldier7
        } else if ap >= 1_200 {
            AbyssRank::Soldier8
        } else {
            AbyssRank::Soldier9
        }
    }

    pub fn calculate_pvp_ap_gain(killer_rank: AbyssRank, victim_rank: AbyssRank, level_diff: i16) -> u32 {
        let base_ap = (victim_rank as u32) * 120;
        let rank_multiplier = if (killer_rank as u32) < (victim_rank as u32) {
            1.3
        } else {
            1.0
        };

        let level_multiplier = match level_diff {
            d if d <= -5 => 1.5,
            d if d >= 5 => 0.2,
            _ => 1.0,
        };

        (base_ap as f32 * rank_multiplier * level_multiplier) as u32
    }

    pub fn calculate_pvp_ap_loss(victim_rank: AbyssRank) -> u32 {
        (victim_rank as u32) * 40
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LootRule {
    FreeForAll,
    RoundRobin,
    LeaderOnly,
    DiceRoll,
}

#[derive(Debug, Clone)]
pub struct Party {
    pub id: u32,
    pub leader_id: u32,
    pub members: Vec<u32>,
    pub loot_rule: LootRule,
}

impl Party {
    pub fn new(id: u32, leader_id: u32) -> Self {
        Self {
            id,
            leader_id,
            members: vec![leader_id],
            loot_rule: LootRule::RoundRobin,
        }
    }

    pub fn add_member(&mut self, player_id: u32) -> bool {
        if self.members.len() >= 6 || self.members.contains(&player_id) {
            false
        } else {
            self.members.push(player_id);
            true
        }
    }

    pub fn remove_member(&mut self, player_id: u32) -> bool {
        if let Some(pos) = self.members.iter().position(|&id| id == player_id) {
            self.members.remove(pos);
            if self.leader_id == player_id && !self.members.is_empty() {
                self.leader_id = self.members[0];
            }
            true
        } else {
            false
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DuelState {
    Requested,
    Countdown(u8),
    Active,
    Finished { winner_id: u32 },
}

#[derive(Debug, Clone)]
pub struct Duel {
    pub player1_id: u32,
    pub player2_id: u32,
    pub center: Coord,
    pub radius: f32,
    pub state: DuelState,
}

impl Duel {
    pub fn new(p1: u32, p2: u32, center: Coord) -> Self {
        Self {
            player1_id: p1,
            player2_id: p2,
            center,
            radius: 30.0,
            state: DuelState::Requested,
        }
    }

    pub fn is_in_duel_arena(&self, pos: &Coord) -> bool {
        self.center.distance(pos) <= self.radius
    }

    pub fn start(&mut self) {
        self.state = DuelState::Active;
    }

    pub fn check_hp_resolution(&mut self, p1_hp: i32, p2_hp: i32) -> Option<u32> {
        if p1_hp <= 1 {
            self.state = DuelState::Finished { winner_id: self.player2_id };
            Some(self.player2_id)
        } else if p2_hp <= 1 {
            self.state = DuelState::Finished { winner_id: self.player1_id };
            Some(self.player1_id)
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gm_command_parsing() {
        assert_eq!(
            GmCommand::parse(".spawn 210001"),
            Some(GmCommand::Spawn { npc_id: 210001 })
        );
        assert_eq!(
            GmCommand::parse(".teleport 110010000 1200.5 500.2 210.0"),
            Some(GmCommand::Teleport {
                map_id: 110010000,
                x: 1200.5,
                y: 500.2,
                z: 210.0,
            })
        );
        assert_eq!(
            GmCommand::parse(".additem 182400001 5000"),
            Some(GmCommand::AddItem {
                item_id: 182400001,
                count: 5000,
            })
        );
        assert_eq!(GmCommand::parse(".god"), Some(GmCommand::GodMode));
        assert_eq!(GmCommand::parse("Olá mundo"), None);
    }

    #[test]
    fn abyss_rank_and_ap_calculations() {
        assert_eq!(AbyssRank::from_ap(500), AbyssRank::Soldier9);
        assert_eq!(AbyssRank::from_ap(15_000), AbyssRank::Soldier6);
        assert_eq!(AbyssRank::from_ap(300_000), AbyssRank::Star1Officer);

        let gain = AbyssRank::calculate_pvp_ap_gain(AbyssRank::Soldier9, AbyssRank::Soldier1, 0);
        let loss = AbyssRank::calculate_pvp_ap_loss(AbyssRank::Soldier1);
        assert!(gain > 0, "Ganho de AP deve ser positivo");
        assert!(loss > 0, "Perda de AP deve ser positiva");
    }

    #[test]
    fn party_management_and_duel_arena() {
        let mut party = Party::new(101, 1);
        assert!(party.add_member(2));
        assert!(party.add_member(3));
        assert_eq!(party.members.len(), 3);

        party.remove_member(1); // Leader leaves
        assert_eq!(party.leader_id, 2, "Liderança deve passar para o próximo membro");

        let mut duel = Duel::new(1, 2, Coord::new(100.0, 100.0, 0.0));
        assert!(duel.is_in_duel_arena(&Coord::new(115.0, 100.0, 0.0)));
        assert!(!duel.is_in_duel_arena(&Coord::new(140.0, 100.0, 0.0)));

        duel.start();
        let winner = duel.check_hp_resolution(1, 500);
        assert_eq!(winner, Some(2), "Player 2 deve vencer quando Player 1 atinge 1 de HP");
    }
}
