//! Arenas Competitivas, Matchmaking AutoGroup e Campos de Batalha (Dreadgion)

use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ArenaType {
    Discipline1v1,
    ChaosFFA,
    GloryFFA,
    Dreadgion6v6,
    Tiarkh6v6,
}

impl ArenaType {
    pub fn required_players(&self) -> usize {
        match self {
            ArenaType::Discipline1v1 => 2,
            ArenaType::ChaosFFA => 6,
            ArenaType::GloryFFA => 4,
            ArenaType::Dreadgion6v6 => 12,
            ArenaType::Tiarkh6v6 => 12,
        }
    }

    pub fn max_rounds(&self) -> u8 {
        match self {
            ArenaType::Discipline1v1 => 3,
            _ => 1,
        }
    }
}

#[derive(Debug, Default)]
pub struct AutoGroupQueue {
    entries: Vec<(u32, ArenaType, u16)>, // (player_id, arena_type, level)
}

impl AutoGroupQueue {
    pub fn new() -> Self {
        Self { entries: Vec::new() }
    }

    pub fn register(&mut self, player_id: u32, arena_type: ArenaType, level: u16) -> bool {
        if !self.entries.iter().any(|(id, _, _)| *id == player_id) {
            self.entries.push((player_id, arena_type, level));
            true
        } else {
            false
        }
    }

    pub fn unregister(&mut self, player_id: u32) -> bool {
        if let Some(pos) = self.entries.iter().position(|(id, _, _)| *id == player_id) {
            self.entries.remove(pos);
            true
        } else {
            false
        }
    }

    pub fn try_match(&mut self, arena_type: ArenaType) -> Option<Vec<u32>> {
        let req = arena_type.required_players();
        let matching_indices: Vec<usize> = self.entries
            .iter()
            .enumerate()
            .filter(|(_, (_, t, _))| *t == arena_type)
            .map(|(idx, _)| idx)
            .take(req)
            .collect();

        if matching_indices.len() == req {
            let mut matched_players = Vec::new();
            // Remove from highest to lowest index to prevent shift issues
            for &idx in matching_indices.iter().rev() {
                let (id, _, _) = self.entries.remove(idx);
                matched_players.push(id);
            }
            matched_players.reverse();
            Some(matched_players)
        } else {
            None
        }
    }
}

#[derive(Debug, Clone)]
pub struct ArenaMatch {
    pub match_id: u32,
    pub arena_type: ArenaType,
    pub scores: HashMap<u32, i32>,
    pub current_round: u8,
    pub max_rounds: u8,
    pub round_end_tick: u64,
}

impl ArenaMatch {
    pub fn new(match_id: u32, arena_type: ArenaType, players: &[u32], start_tick: u64, round_duration_ticks: u64) -> Self {
        let mut scores = HashMap::new();
        for &id in players {
            scores.insert(id, 0);
        }

        Self {
            match_id,
            arena_type,
            scores,
            current_round: 1,
            max_rounds: arena_type.max_rounds(),
            round_end_tick: start_tick + round_duration_ticks,
        }
    }

    pub fn record_kill(&mut self, killer_id: u32, victim_id: u32) {
        if let Some(score) = self.scores.get_mut(&killer_id) {
            *score += 1000;
        }
        if let Some(score) = self.scores.get_mut(&victim_id) {
            *score = (*score - 300).max(0);
        }
    }

    pub fn record_surkana(&mut self, player_id: u32) {
        if let Some(score) = self.scores.get_mut(&player_id) {
            *score += 800;
        }
    }

    pub fn get_winner(&self) -> Option<u32> {
        self.scores.iter().max_by_key(|(_, score)| *score).map(|(&id, _)| id)
    }

    pub fn calculate_reward(&self, player_id: u32) -> (u32, u32) {
        let is_winner = self.get_winner() == Some(player_id);
        let insignia_id = 186000030; // Crucible Insignia
        let count = if is_winner { 250 } else { 100 };
        (insignia_id, count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn autogroup_queue_and_matchmaking() {
        let mut queue = AutoGroupQueue::new();
        assert!(queue.register(1, ArenaType::Discipline1v1, 65));
        assert!(queue.register(2, ArenaType::ChaosFFA, 65)); // Different arena

        // Not enough for 1v1
        assert_eq!(queue.try_match(ArenaType::Discipline1v1), None);

        // Player 3 joins 1v1
        assert!(queue.register(3, ArenaType::Discipline1v1, 65));

        // Match found!
        let matched = queue.try_match(ArenaType::Discipline1v1);
        assert_eq!(matched, Some(vec![1, 3]));

        // Queue now contains only Player 2
        assert_eq!(queue.entries.len(), 1);
    }

    #[test]
    fn arena_match_scoring_and_winner_rewards() {
        let players = vec![101, 102];
        let mut match_1v1 = ArenaMatch::new(1, ArenaType::Discipline1v1, &players, 100, 1000);

        // Player 101 kills 102
        match_1v1.record_kill(101, 102);
        assert_eq!(match_1v1.scores.get(&101), Some(&1000));
        assert_eq!(match_1v1.scores.get(&102), Some(&0));

        // Player 101 destroys Surkana
        match_1v1.record_surkana(101);
        assert_eq!(match_1v1.scores.get(&101), Some(&1800));

        // Winner is 101
        assert_eq!(match_1v1.get_winner(), Some(101));

        let (item, count) = match_1v1.calculate_reward(101);
        assert_eq!(item, 186000030);
        assert_eq!(count, 250); // Winner reward

        let (_, count_loser) = match_1v1.calculate_reward(102);
        assert_eq!(count_loser, 100); // Loser reward
    }
}
