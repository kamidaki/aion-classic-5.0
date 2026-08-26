use rusqlite::{params, Connection, Result};

pub struct GuildDao;

impl GuildDao {
    pub fn criar_guild(conn: &Connection, name: &str, race: u8, leader_id: u32) -> Result<u32> {
        conn.execute(
            "INSERT INTO guilds (name, race, leader_id) VALUES (?1, ?2, ?3)",
            params![name, race as i64, leader_id as i64],
        )?;
        let guild_id = conn.last_insert_rowid() as u32;
        Self::adicionar_membro_guild(conn, guild_id, leader_id, 1)?;
        Ok(guild_id)
    }

    pub fn adicionar_membro_guild(conn: &Connection, guild_id: u32, player_id: u32, rank_index: u8) -> Result<()> {
        conn.execute(
            "INSERT OR REPLACE INTO guild_members (guild_id, player_id, rank_index, contribution) VALUES (?1, ?2, ?3, 0)",
            params![guild_id as i64, player_id as i64, rank_index as i64],
        )?;
        Ok(())
    }

    pub fn remover_membro_guild(conn: &Connection, guild_id: u32, player_id: u32) -> Result<bool> {
        let n = conn.execute(
            "DELETE FROM guild_members WHERE guild_id = ?1 AND player_id = ?2",
            params![guild_id as i64, player_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn guild_do_jogador(conn: &Connection, player_id: u32) -> Result<Option<crate::guild::Guild>> {
        let mut stmt = conn.prepare(
            "SELECT g.id, g.name, g.rank, g.race, g.exp, g.leader_id, g.notice, g.kinah
             FROM guilds g
             INNER JOIN guild_members gm ON gm.guild_id = g.id
             WHERE gm.player_id = ?1",
        )?;
        let mut rows = stmt.query_map(params![player_id as i64], |row| {
            Ok(crate::guild::Guild {
                id: row.get::<_, i64>(0)? as u32,
                name: row.get(1)?,
                rank: row.get::<_, i64>(2)? as u8,
                race: row.get::<_, i64>(3)? as u8,
                exp: row.get::<_, i64>(4)? as u32,
                contribution_points: 0,
                leader_id: row.get::<_, i64>(5)? as u32,
                notice: row.get(6)?,
                kinah: row.get::<_, i64>(7)? as u64,
                members: Vec::new(),
                emblem_png: None,
                active_buffs: Vec::new(),
            })
        })?;

        if let Some(res) = rows.next() {
            let mut guild = res?;
            let mut mstmt = conn.prepare(
                "SELECT gm.player_id, c.name, gm.rank_index, gm.contribution
                 FROM guild_members gm
                 INNER JOIN characters c ON c.id = gm.player_id
                 WHERE gm.guild_id = ?1",
            )?;
            let mrows = mstmt.query_map(params![guild.id as i64], |mrow| {
                Ok(crate::guild::GuildMember {
                    player_id: mrow.get::<_, i64>(0)? as u32,
                    name: mrow.get(1)?,
                    guild_rank_index: mrow.get::<_, i64>(2)? as u8,
                    class_id: 1,
                    level: 50,
                    race: guild.race,
                    is_online: true,
                    last_online: 0,
                    contribution: mrow.get::<_, i64>(3)? as u64,
                    map_id: 110010000,
                })
            })?;
            for m in mrows {
                guild.members.push(m?);
            }
            Ok(Some(guild))
        } else {
            Ok(None)
        }
    }
}
