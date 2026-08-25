use rusqlite::{params, Connection, OptionalExtension, Result};

/// Dados de um personagem gravados no SQLite
#[derive(Debug, Clone)]
pub struct PersistedCharacter {
    pub id: u32,
    pub account_id: u32,
    pub name: String,
    pub level: u16,
    pub exp: u64,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub map_id: u32,
    pub heading: u8,
    pub hp: u32,
    pub mp: u32,
    pub aparencia: Vec<u8>,
    pub kit_inicial: u8,
}

pub struct CharacterDao;

impl CharacterDao {
    /// Cria um novo personagem com coordenadas de spawn e equipamentos 100% dinâmicos (vindos do XML)
    pub fn criar_personagem_com_xml(
        conn: &Connection,
        username: &str,
        nome: &str,
        aparencia: &[u8],
        ponto_opt: Option<crate::game::mundo::PontoDeEntrada>,
        itens: &[(u32, u32)],
    ) -> Result<PersistedCharacter> {
        use crate::dao::account_dao::AccountDao;
        use crate::dao::inventory_dao::InventoryDao;
        use crate::dao::skill_dao::SkillDao;
        use crate::game::mundo;

        let account_id = AccountDao::ensure_account(conn, username)?;

        let raca = aparencia
            .get(56..60)
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);
        let classe = aparencia
            .get(60..64)
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);
        
        let ponto = ponto_opt.unwrap_or_else(|| mundo::ponto_de_entrada(raca));
        let (base_hp, base_mp) = Self::base_stats_for_class(classe);

        let tem_aparencia = !aparencia.is_empty();
        let kit_inicial_flag = if !itens.is_empty() || tem_aparencia { 1 } else { 0 };

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

        if !itens.is_empty() {
            InventoryDao::salvar_itens_iniciais(conn, id, itens)?;
        }

        if tem_aparencia {
            let skills = SkillDao::initial_skills_for_class(classe);
            let _ = SkillDao::salvar_skills(conn, id, &skills);
        }

        Ok(PersistedCharacter {
            id,
            account_id: account_id as u32,
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
            aparencia: aparencia.to_vec(),
            kit_inicial: kit_inicial_flag,
        })
    }

    pub fn criar_personagem(
        conn: &Connection,
        username: &str,
        nome: &str,
        aparencia: &[u8],
    ) -> Result<PersistedCharacter> {
        Self::criar_personagem_com_xml(conn, username, nome, aparencia, None, &[])
    }

    pub fn base_stats_for_class(classe: u32) -> (u32, u32) {
        match classe {
            0 | 1 | 2 => (1278, 577),  // Warrior, Gladiator, Templar
            3 | 4 | 5 => (1043, 674),  // Scout, Assassin, Ranger
            6 | 7 | 8 => (872, 1349),  // Mage, Sorcerer, Spiritmaster
            9 | 10 | 11 => (1134, 1146), // Priest, Cleric, Chanter
            _ => (1000, 1000),
        }
    }

    pub fn deletar_personagem(conn: &Connection, username: &str, character_id: u32) -> Result<bool> {
        use crate::dao::account_dao::AccountDao;
        let account_id = match AccountDao::get_account_id(conn, username)? {
            Some(id) => id,
            None => return Ok(false),
        };

        let affected = conn.execute(
            "DELETE FROM characters WHERE id = ?1 AND account_id = ?2",
            params![character_id as i64, account_id as i64],
        )?;

        if affected > 0 {
            let _ = conn.execute("DELETE FROM character_items WHERE character_id = ?1", params![character_id as i64]);
            let _ = conn.execute("DELETE FROM character_skills WHERE character_id = ?1", params![character_id as i64]);
            let _ = conn.execute("DELETE FROM character_quests WHERE character_id = ?1", params![character_id as i64]);
            let _ = conn.execute("DELETE FROM character_friends WHERE character_id = ?1 OR friend_id = ?1", params![character_id as i64]);
            let _ = conn.execute("DELETE FROM character_mail WHERE recipient_id = ?1", params![character_id as i64]);
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn personagens_da_conta(conn: &Connection, username: &str) -> Result<Vec<PersistedCharacter>> {
        use crate::dao::account_dao::AccountDao;
        let account_id = match AccountDao::get_account_id(conn, username)? {
            Some(id) => id,
            None => return Ok(Vec::new()),
        };

        let mut stmt = conn.prepare(
            "SELECT id, account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia, kit_inicial
             FROM characters
             WHERE account_id = ?1
             ORDER BY id ASC",
        )?;

        let rows = stmt.query_map(params![account_id as i64], |row| {
            Ok(PersistedCharacter {
                id: row.get::<_, i64>(0)? as u32,
                account_id: row.get::<_, i64>(1)? as u32,
                name: row.get(2)?,
                level: row.get::<_, i64>(3)? as u16,
                exp: row.get::<_, i64>(4)? as u64,
                x: row.get::<_, f64>(5)? as f32,
                y: row.get::<_, f64>(6)? as f32,
                z: row.get::<_, f64>(7)? as f32,
                map_id: row.get::<_, i64>(8)? as u32,
                heading: row.get::<_, i64>(9)? as u8,
                hp: row.get::<_, i64>(10)? as u32,
                mp: row.get::<_, i64>(11)? as u32,
                aparencia: row.get(12)?,
                kit_inicial: row.get::<_, i64>(13)? as u8,
            })
        })?;

        let mut result = Vec::new();
        for r in rows {
            result.push(r?);
        }
        Ok(result)
    }

    pub fn save_character(
        conn: &Connection,
        char_id: u32,
        x: f32,
        y: f32,
        z: f32,
        map_id: u32,
        heading: u8,
        level: u16,
        exp: u64,
        hp: u32,
        mp: u32,
    ) -> Result<()> {
        conn.execute(
            "UPDATE characters
             SET x = ?1, y = ?2, z = ?3, map_id = ?4, heading = ?5,
                 level = ?6, exp = ?7, hp = ?8, mp = ?9
             WHERE id = ?10",
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
                char_id as i64,
            ],
        )?;
        Ok(())
    }

    pub fn get_character_by_id(conn: &Connection, char_id: u32) -> Result<Option<PersistedCharacter>> {
        let mut stmt = conn.prepare(
            "SELECT id, account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia, kit_inicial
             FROM characters
             WHERE id = ?1",
        )?;

        let row = stmt
            .query_row(params![char_id as i64], |row| {
                Ok(PersistedCharacter {
                    id: row.get::<_, i64>(0)? as u32,
                    account_id: row.get::<_, i64>(1)? as u32,
                    name: row.get(2)?,
                    level: row.get::<_, i64>(3)? as u16,
                    exp: row.get::<_, i64>(4)? as u64,
                    x: row.get::<_, f64>(5)? as f32,
                    y: row.get::<_, f64>(6)? as f32,
                    z: row.get::<_, f64>(7)? as f32,
                    map_id: row.get::<_, i64>(8)? as u32,
                    heading: row.get::<_, i64>(9)? as u8,
                    hp: row.get::<_, i64>(10)? as u32,
                    mp: row.get::<_, i64>(11)? as u32,
                    aparencia: row.get(12)?,
                    kit_inicial: row.get::<_, i64>(13)? as u8,
                })
            })
            .optional()?;

        Ok(row)
    }

    pub fn get_character_by_name(conn: &Connection, name: &str) -> Result<Option<PersistedCharacter>> {
        let mut stmt = conn.prepare(
            "SELECT id, account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia, kit_inicial
             FROM characters
             WHERE name = ?1",
        )?;

        let row = stmt
            .query_row(params![name], |row| {
                Ok(PersistedCharacter {
                    id: row.get::<_, i64>(0)? as u32,
                    account_id: row.get::<_, i64>(1)? as u32,
                    name: row.get(2)?,
                    level: row.get::<_, i64>(3)? as u16,
                    exp: row.get::<_, i64>(4)? as u64,
                    x: row.get::<_, f64>(5)? as f32,
                    y: row.get::<_, f64>(6)? as f32,
                    z: row.get::<_, f64>(7)? as f32,
                    map_id: row.get::<_, i64>(8)? as u32,
                    heading: row.get::<_, i64>(9)? as u8,
                    hp: row.get::<_, i64>(10)? as u32,
                    mp: row.get::<_, i64>(11)? as u32,
                    aparencia: row.get(12)?,
                    kit_inicial: row.get::<_, i64>(13)? as u8,
                })
            })
            .optional()?;

        Ok(row)
    }

    pub fn verificar_nome_em_uso(conn: &Connection, name: &str) -> Result<bool> {
        let count: i64 = conn.query_row(
            "SELECT COUNT(1) FROM characters WHERE LOWER(name) = LOWER(?1)",
            params![name],
            |row| row.get(0),
        )?;
        Ok(count > 0)
    }

    pub fn get_first_character(conn: &Connection, username: &str) -> Result<Option<PersistedCharacter>> {
        let chars = Self::personagens_da_conta(conn, username)?;
        Ok(chars.into_iter().next())
    }

    pub fn buscar_personagem_por_nome(conn: &Connection, name: &str) -> Result<Option<PersistedCharacter>> {
        Self::get_character_by_name(conn, name)
    }
}
