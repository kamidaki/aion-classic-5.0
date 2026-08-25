use rusqlite::{params, Connection, OptionalExtension, Result};

#[derive(Debug, Clone)]
pub struct PersistedCharacter {
    pub id: u32,
    pub account_id: i64,
    pub name: String,
    pub level: u16,
    pub exp: u64,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub map_id: u32,
    pub heading: u8,
    pub hp: i32,
    pub mp: u32,
    pub aparencia: Option<Vec<u8>>,
}

pub struct CharacterDao;

impl CharacterDao {
    /// HP e MP base para nível 1 por classe
    pub fn base_stats_for_class(class_id: u32) -> (i32, u32) {
        match class_id {
            1 | 2 => (1278, 577),     // Warrior / Gladiator / Templar
            3 | 4 | 5 => (1148, 634), // Scout / Assassin / Ranger
            6 | 7 | 8 => (976, 1022), // Mage / Sorcerer / Spiritmaster
            9 | 10 | 11 => (1050, 908), // Priest / Cleric / Chanter
            _ => (1000, 500),
        }
    }

    /// Cria um personagem novo na conta com kit inicial e skills associadas
    pub fn criar_personagem(
        conn: &Connection,
        username: &str,
        nome: &str,
        aparencia: &[u8],
    ) -> Result<PersistedCharacter> {
        use crate::game::mundo;
        use crate::dao::account_dao::AccountDao;
        use crate::dao::inventory_dao::InventoryDao;
        use crate::dao::skill_dao::SkillDao;

        let account_id = AccountDao::ensure_account(conn, username)?;

        let raca = aparencia
            .get(56..60)
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);
        let classe = aparencia
            .get(60..64)
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);
        let ponto = mundo::ponto_de_entrada(raca);
        let (base_hp, base_mp) = Self::base_stats_for_class(classe);

        let tem_aparencia = !aparencia.is_empty();
        let kit_inicial_flag = if tem_aparencia { 1 } else { 0 };

        conn.execute(
            "INSERT INTO characters(account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia, kit_inicial)
             VALUES (?1, ?2, 1, 0, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
            params![
                account_id,
                nome,
                ponto.x,
                ponto.y,
                ponto.z,
                ponto.mapa as i64,
                ponto.direcao as i64,
                base_hp as i64,
                base_mp as i64,
                aparencia,
                kit_inicial_flag
            ],
        )?;
        let id = conn.last_insert_rowid() as u32;

        if tem_aparencia {
            let kit = InventoryDao::kit_for_class(classe);
            for (pos, (item_id, qtd)) in kit.iter().enumerate() {
                let _ = conn.execute(
                    "INSERT INTO character_items(character_id, item_id, quantidade, posicao) VALUES (?1, ?2, ?3, ?4)",
                    params![id as i64, *item_id as i64, *qtd as i64, pos as i64],
                );
            }

            let skills = SkillDao::initial_skills_for_class(classe);
            let _ = SkillDao::salvar_skills(conn, id, &skills);
        }

        Ok(PersistedCharacter {
            id,
            account_id,
            name: nome.to_string(),
            level: 1,
            exp: 0,
            x: ponto.x,
            y: ponto.y,
            z: ponto.z,
            map_id: ponto.mapa,
            heading: ponto.direcao,
            hp: base_hp,
            mp: base_mp,
            aparencia: Some(aparencia.to_vec()),
        })
    }

    /// Personagens da conta, na ordem em que foram criados
    pub fn personagens_da_conta(
        conn: &Connection,
        username: &str,
    ) -> Result<Vec<PersistedCharacter>> {
        let account_id: i64 = conn.query_row(
            "SELECT id FROM account_data WHERE name = ?1 COLLATE NOCASE",
            params![username],
            |row| row.get(0),
        )?;

        let mut stmt = conn.prepare(
            "SELECT id, account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia
             FROM characters WHERE account_id = ?1 ORDER BY id",
        )?;
        let linhas = stmt.query_map(params![account_id], |row| {
            Ok(PersistedCharacter {
                id: row.get::<_, i64>(0)? as u32,
                account_id: row.get(1)?,
                name: row.get(2)?,
                level: row.get::<_, i64>(3)? as u16,
                exp: row.get::<_, i64>(4)? as u64,
                x: row.get(5)?,
                y: row.get(6)?,
                z: row.get(7)?,
                map_id: row.get::<_, i64>(8)? as u32,
                heading: row.get::<_, i64>(9)? as u8,
                hp: row.get::<_, i64>(10)? as i32,
                mp: row.get::<_, i64>(11)? as u32,
                aparencia: row.get(12)?,
            })
        })?;

        linhas.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    /// Verifica se o nickname já existe no banco
    pub fn verificar_nome_em_uso(conn: &Connection, name: &str) -> Result<bool> {
        let count: i64 = conn.query_row(
            "SELECT COUNT(1) FROM characters WHERE name = ?1 COLLATE NOCASE",
            params![name],
            |row| row.get(0),
        )?;
        Ok(count > 0)
    }

    /// Deleta um personagem pertencente à conta
    pub fn deletar_personagem(conn: &Connection, username: &str, character_id: u32) -> Result<bool> {
        let account_id: Option<i64> = conn
            .query_row(
                "SELECT id FROM account_data WHERE name = ?1 COLLATE NOCASE",
                params![username],
                |row| row.get(0),
            )
            .optional()?;
        let Some(account_id) = account_id else {
            return Ok(false);
        };

        let _ = conn.execute("DELETE FROM character_items WHERE character_id = ?1", params![character_id]);
        let _ = conn.execute("DELETE FROM character_skills WHERE character_id = ?1", params![character_id]);
        let _ = conn.execute("DELETE FROM player_quests WHERE character_id = ?1", params![character_id]);
        let _ = conn.execute("DELETE FROM character_mail WHERE character_id = ?1", params![character_id]);
        let _ = conn.execute("DELETE FROM guild_members WHERE player_id = ?1", params![character_id]);
        let _ = conn.execute("DELETE FROM character_buddies WHERE player_id = ?1 OR buddy_id = ?1", params![character_id]);
        let _ = conn.execute("DELETE FROM broker_listings WHERE seller_id = ?1", params![character_id]);
        let _ = conn.execute("DELETE FROM broker_history WHERE player_id = ?1", params![character_id]);

        let rows = conn.execute(
            "DELETE FROM characters WHERE id = ?1 AND account_id = ?2",
            params![character_id, account_id],
        )?;

        Ok(rows > 0)
    }

    pub fn get_first_character(
        conn: &Connection,
        username: &str,
    ) -> Result<Option<PersistedCharacter>> {
        use crate::dao::account_dao::AccountDao;
        let account_id = AccountDao::ensure_account(conn, username)?;

        let existing: Option<PersistedCharacter> = conn
            .query_row(
                "SELECT id, account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia
                 FROM characters WHERE account_id = ?1 LIMIT 1",
                params![account_id],
                |row| {
                    Ok(PersistedCharacter {
                        id: row.get::<_, i64>(0)? as u32,
                        account_id: row.get(1)?,
                        name: row.get(2)?,
                        level: row.get::<_, i64>(3)? as u16,
                        exp: row.get::<_, i64>(4)? as u64,
                        x: row.get(5)?,
                        y: row.get(6)?,
                        z: row.get(7)?,
                        map_id: row.get::<_, i64>(8)? as u32,
                        heading: row.get::<_, i64>(9)? as u8,
                        hp: row.get::<_, i64>(10)? as i32,
                        mp: row.get::<_, i64>(11)? as u32,
                        aparencia: row.get(12)?,
                    })
                },
            )
            .ok();

        Ok(existing)
    }

    pub fn buscar_personagem_por_nome(conn: &Connection, name: &str) -> Result<Option<PersistedCharacter>> {
        let mut stmt = conn.prepare(
            "SELECT id, account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia
             FROM characters WHERE name = ?1",
        )?;
        let mut rows = stmt.query_map(params![name], |row| {
            Ok(PersistedCharacter {
                id: row.get::<_, i64>(0)? as u32,
                account_id: row.get(1)?,
                name: row.get(2)?,
                level: row.get::<_, i64>(3)? as u16,
                exp: row.get::<_, i64>(4)? as u64,
                x: row.get(5)?,
                y: row.get(6)?,
                z: row.get(7)?,
                map_id: row.get::<_, i64>(8)? as u32,
                heading: row.get::<_, i64>(9)? as u8,
                hp: row.get(10)?,
                mp: row.get::<_, i64>(11)? as u32,
                aparencia: row.get(12)?,
            })
        })?;
        if let Some(r) = rows.next() {
            Ok(Some(r?))
        } else {
            Ok(None)
        }
    }

    pub fn save_character(
        conn: &Connection,
        id: u32,
        x: f32,
        y: f32,
        z: f32,
        map_id: u32,
        heading: u8,
        level: u16,
        exp: u64,
        hp: i32,
        mp: u32,
    ) -> Result<()> {
        conn.execute(
            "UPDATE characters
             SET x=?1, y=?2, z=?3, map_id=?4, heading=?5, level=?6, exp=?7, hp=?8, mp=?9,
                 updated_at=strftime('%s','now')
             WHERE id=?10",
            params![
                x,
                y,
                z,
                map_id as i64,
                heading as i64,
                level as i64,
                exp as i64,
                hp as i64,
                mp as i64,
                id as i64
            ],
        )?;
        Ok(())
    }
}
