use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct Guild {
    pub id: u32,
    pub name: String,
    pub rank: u8, // 1-10
    pub race: u8,
    pub exp: u32,
    pub contribution_points: u32,
    pub leader_id: u32,
    pub notice: String,
    pub kinah: u64,
    pub members: Vec<GuildMember>,
    pub emblem_png: Option<Vec<u8>>,
    pub active_buffs: Vec<GuildBuff>,
}

#[derive(Debug, Clone)]
pub struct GuildMember {
    pub player_id: u32,
    pub name: String,
    pub guild_rank_index: u8,
    pub class_id: u8,
    pub level: u8,
    pub race: u8,
    pub is_online: bool,
    pub last_online: u32,
    pub contribution: u64,
    pub map_id: u32,
}

#[derive(Debug, Clone)]
pub struct GuildBuff {
    pub buff_id: u32,
    pub remaining_ms: u32,
    pub level: u32,
}

impl Guild {
    pub fn new(id: u32, name: String, race: u8, leader_id: u32) -> Self {
        Self {
            id,
            name,
            rank: 1,
            race,
            exp: 0,
            contribution_points: 0,
            leader_id,
            notice: "Welcome to our Legion!".to_string(),
            kinah: 0,
            members: Vec::new(),
            emblem_png: None,
            active_buffs: Vec::new(),
        }
    }

    pub fn add_member(&mut self, member: GuildMember) {
        self.members.retain(|m| m.player_id != member.player_id);
        self.members.push(member);
    }

    pub fn remove_member(&mut self, player_id: u32) -> bool {
        let initial_len = self.members.len();
        self.members.retain(|m| m.player_id != player_id);
        self.members.len() < initial_len
    }

    pub const CHUNK_SIZE: usize = 512;

    pub fn build_emblem_packets(&self) -> Vec<crate::game::message::server::GuildEmblemImgData> {
        let Some(ref png_data) = self.emblem_png else {
            return Vec::new();
        };
        let total_chunks = (png_data.len() + Self::CHUNK_SIZE - 1) / Self::CHUNK_SIZE;
        png_data
            .chunks(Self::CHUNK_SIZE)
            .enumerate()
            .map(|(i, chunk)| {
                crate::game::message::server::GuildEmblemImgData::new(
                    self.id,
                    i as u16,
                    total_chunks as u16,
                    chunk.to_vec(),
                )
            })
            .collect()
    }
}

#[derive(Debug, Default)]
pub struct GuildManager {
    pub guilds: HashMap<u32, Guild>,
    pub player_guild_map: HashMap<u32, u32>,
    next_guild_id: u32,
}

impl GuildManager {
    pub fn new() -> Self {
        Self {
            guilds: HashMap::new(),
            player_guild_map: HashMap::new(),
            next_guild_id: 1,
        }
    }

    pub fn create_guild(&mut self, name: String, race: u8, leader_id: u32, leader_name: String, class_id: u8, level: u8) -> u32 {
        let id = self.next_guild_id;
        self.next_guild_id = self.next_guild_id.wrapping_add(1);

        let mut guild = Guild::new(id, name, race, leader_id);
        let leader_member = GuildMember {
            player_id: leader_id,
            name: leader_name,
            guild_rank_index: 1, // Brigade General
            class_id,
            level,
            race,
            is_online: true,
            last_online: 0,
            contribution: 0,
            map_id: 110010000,
        };
        guild.add_member(leader_member);

        self.player_guild_map.insert(leader_id, id);
        self.guilds.insert(id, guild);
        id
    }

    pub fn get_guild_for_player(&self, player_id: u32) -> Option<&Guild> {
        let guild_id = self.player_guild_map.get(&player_id)?;
        self.guilds.get(guild_id)
    }

    pub fn get_guild_mut_for_player(&mut self, player_id: u32) -> Option<&mut Guild> {
        let guild_id = *self.player_guild_map.get(&player_id)?;
        self.guilds.get_mut(&guild_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_guild_lifecycle_and_emblem_chunks() {
        let mut gm = GuildManager::new();
        let g_id = gm.create_guild(
            "Valhalla".to_string(),
            0,
            1001,
            "Thor".to_string(),
            1,
            50,
        );

        let g = gm.get_guild_mut_for_player(1001).expect("guild deve existir");
        assert_eq!(g.name, "Valhalla");
        assert_eq!(g.members.len(), 1);

        // Adiciona dados de emblema de 1025 bytes -> 3 chunks de 512
        let fake_png = vec![0x89; 1025];
        g.emblem_png = Some(fake_png);

        let chunks = g.build_emblem_packets();
        assert_eq!(chunks.len(), 3);
        assert_eq!(chunks[0].chunk_index, 0);
        assert_eq!(chunks[0].total_chunks, 3);
        assert_eq!(chunks[0].data.len(), 512);
        assert_eq!(chunks[1].chunk_index, 1);
        assert_eq!(chunks[1].data.len(), 512);
        assert_eq!(chunks[2].chunk_index, 2);
        assert_eq!(chunks[2].data.len(), 1);
    }
}
