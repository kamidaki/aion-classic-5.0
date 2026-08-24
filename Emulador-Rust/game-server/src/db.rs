use rusqlite::{params, Connection, OptionalExtension, Result};
use std::path::Path;

pub struct Db {
    conn: Connection,
}

/// Faixa em que o cliente 4.5 espera id de objeto de item.
///
/// Os 119 itens que a captura mostra tem todos id comecando em `0xC0`; os ids de entidade de NPC,
/// em `0x80`. Sao faixas separadas, e misturar as duas confunde o cliente sobre o que e cada
/// coisa em cena.
const OBJ_ID_BASE: u32 = 0xC000_0000;

/// Uma linha da bolsa, como ela sai do banco.
#[derive(Debug, Clone)]
pub struct ItemPersistido {
    pub obj_id: u32,
    pub item_id: u32,
    pub quantidade: u64,
    pub posicao: u16,
}

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
    /// Bloco de 140 bytes que o cliente mandou ao criar o personagem: nome, genero, raca,
    /// classe, voz, cores, os 52 bytes de rosto e a altura. E identico ao trecho 4..144 do
    /// registro da lista -- ver `game::message::lista_personagens::escreve_registro`.
    pub aparencia: Option<Vec<u8>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuestPersistida {
    pub quest_id: u32,
    pub status: String,
    pub quest_vars: u32,
    pub complete_count: u32,
}

impl Db {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let db = Self { conn };
        db.init_schema()?;
        Ok(db)
    }

    fn init_schema(&self) -> Result<()> {
        self.conn.execute_batch(
            "
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL DEFAULT '',
                access_level INTEGER NOT NULL DEFAULT 0,
                membership INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                last_ip TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL REFERENCES accounts(id),
                name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                exp INTEGER NOT NULL DEFAULT 0,
                x REAL NOT NULL,
                y REAL NOT NULL,
                z REAL NOT NULL,
                map_id INTEGER NOT NULL DEFAULT 110070000,
                heading INTEGER NOT NULL DEFAULT 0,
                hp INTEGER NOT NULL DEFAULT 100,
                mp INTEGER NOT NULL DEFAULT 100,
                aparencia BLOB,
                kit_inicial INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_characters_account ON characters(account_id);
            CREATE TABLE IF NOT EXISTS character_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL REFERENCES characters(id),
                item_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 1,
                posicao INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_items_character ON character_items(character_id);
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                account_name TEXT NOT NULL,
                account_id INTEGER NOT NULL DEFAULT 1,
                session_key INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                expires_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS player_quests (
                character_id INTEGER NOT NULL REFERENCES characters(id),
                quest_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                quest_vars INTEGER DEFAULT 0,
                complete_count INTEGER DEFAULT 0,
                PRIMARY KEY(character_id, quest_id)
            );
            CREATE INDEX IF NOT EXISTS idx_quests_character ON player_quests(character_id);
            CREATE TABLE IF NOT EXISTS character_mail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id INTEGER NOT NULL REFERENCES characters(id),
                sender_id INTEGER NOT NULL DEFAULT 0,
                sender_name TEXT NOT NULL DEFAULT 'System',
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                letter_type INTEGER NOT NULL DEFAULT 0,
                is_read INTEGER NOT NULL DEFAULT 0,
                item_template_id INTEGER NOT NULL DEFAULT 0,
                item_quantity INTEGER NOT NULL DEFAULT 0,
                kinah_amount INTEGER NOT NULL DEFAULT 0,
                timestamp INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_mail_recipient ON character_mail(recipient_id);
            CREATE TABLE IF NOT EXISTS guilds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                rank INTEGER NOT NULL DEFAULT 1,
                race INTEGER NOT NULL DEFAULT 0,
                exp INTEGER NOT NULL DEFAULT 0,
                leader_id INTEGER NOT NULL,
                notice TEXT NOT NULL DEFAULT '',
                kinah INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS guild_members (
                guild_id INTEGER NOT NULL REFERENCES guilds(id),
                player_id INTEGER NOT NULL REFERENCES characters(id),
                rank_index INTEGER NOT NULL DEFAULT 5,
                contribution INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, player_id)
            );
            CREATE INDEX IF NOT EXISTS idx_guild_members_player ON guild_members(player_id);
            CREATE TABLE IF NOT EXISTS character_buddies (
                player_id INTEGER NOT NULL REFERENCES characters(id),
                buddy_id INTEGER NOT NULL REFERENCES characters(id),
                PRIMARY KEY (player_id, buddy_id)
            );
            CREATE INDEX IF NOT EXISTS idx_buddies_player ON character_buddies(player_id);
            CREATE TABLE IF NOT EXISTS broker_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                seller_name TEXT NOT NULL,
                item_template_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_unit INTEGER NOT NULL,
                expiry_ts INTEGER NOT NULL,
                quality INTEGER NOT NULL DEFAULT 0,
                enhance_level INTEGER NOT NULL DEFAULT 0,
                is_sold INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_broker_active ON broker_listings(is_sold, expiry_ts);
            CREATE TABLE IF NOT EXISTS broker_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                item_template_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                type INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_broker_history_player ON broker_history(player_id);
            CREATE TABLE IF NOT EXISTS character_skills (
                character_id INTEGER NOT NULL REFERENCES characters(id),
                skill_id INTEGER NOT NULL,
                skill_level INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (character_id, skill_id)
            );
            CREATE INDEX IF NOT EXISTS idx_skills_character ON character_skills(character_id);
            ",
        )?;

        // Compatibilidade com colunas legadas se existirem
        let _ = self.conn.execute("ALTER TABLE characters ADD COLUMN aparencia BLOB", []);
        let _ = self.conn.execute("ALTER TABLE characters ADD COLUMN kit_inicial INTEGER NOT NULL DEFAULT 0", []);
        let _ = self.conn.execute("ALTER TABLE characters ADD COLUMN map_id INTEGER NOT NULL DEFAULT 110070000", []);
        let _ = self.conn.execute("ALTER TABLE characters ADD COLUMN heading INTEGER NOT NULL DEFAULT 0", []);
        let _ = self.conn.execute("ALTER TABLE accounts ADD COLUMN name TEXT", []);
        let _ = self.conn.execute("ALTER TABLE accounts ADD COLUMN username TEXT", []);
        let _ = self.conn.execute("ALTER TABLE accounts ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''", []);
        let _ = self.conn.execute("ALTER TABLE accounts ADD COLUMN access_level INTEGER NOT NULL DEFAULT 0", []);
        let _ = self.conn.execute("ALTER TABLE accounts ADD COLUMN membership INTEGER NOT NULL DEFAULT 0", []);
        let _ = self.conn.execute("ALTER TABLE accounts ADD COLUMN last_ip TEXT NOT NULL DEFAULT ''", []);
        let _ = self.conn.execute("ALTER TABLE accounts ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0", []);

        let _ = self.conn.execute("ALTER TABLE sessions ADD COLUMN account_name TEXT", []);
        let _ = self.conn.execute("ALTER TABLE sessions ADD COLUMN username TEXT", []);
        let _ = self.conn.execute("ALTER TABLE sessions ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1", []);
        let _ = self.conn.execute("ALTER TABLE sessions ADD COLUMN session_key INTEGER NOT NULL DEFAULT 0", []);
        let _ = self.conn.execute("ALTER TABLE sessions ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0", []);
        let _ = self.conn.execute("ALTER TABLE sessions ADD COLUMN expires_at INTEGER NOT NULL DEFAULT 0", []);

        Ok(())
    }

    /// Look up the username associated with a session token. Returns None if
    /// the token is unknown (e.g. client connected directly without going
    /// through STS).
    pub fn lookup_session(&self, token: &str) -> Result<Option<String>> {
        let token = token.trim_end_matches(' ').trim();

        self.conn
            .query_row(
                "SELECT COALESCE(NULLIF(account_name, ''), username) FROM sessions WHERE token = ?1 OR session_key = ?1",
                params![token],
                |row| row.get::<_, String>(0),
            )
            .map(Some)
            .or_else(|e| match e {
                rusqlite::Error::QueryReturnedNoRows => Ok(None),
                other => Err(other),
            })
    }

    /// Personagens da conta, na ordem em que foram criados.
    pub fn personagens_da_conta(
        &self,
        username: &str,
    ) -> Result<Vec<PersistedCharacter>> {
        let account_id: i64 = self.conn.query_row(
            "SELECT id FROM accounts WHERE name = ?1 OR username = ?1 COLLATE NOCASE",
            params![username],
            |row| row.get(0),
        )?;

        let mut stmt = self.conn.prepare(
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

    /// Cria um personagem novo na conta e devolve o que ficou no banco.
    pub fn criar_personagem(
        &self,
        username: &str,
        nome: &str,
        aparencia: &[u8],
    ) -> Result<PersistedCharacter> {
        use crate::game::mundo;

        self.conn.execute(
            "INSERT OR IGNORE INTO accounts(name, password_hash, access_level, membership, created_at) VALUES (?1, ?1, 0, 0, strftime('%s','now'))",
            params![username],
        )?;
        let account_id: i64 = self.conn.query_row(
            "SELECT id FROM accounts WHERE name = ?1 OR username = ?1 COLLATE NOCASE",
            params![username],
            |row| row.get(0),
        )?;

        // A raca esta no offset 60 do registro, e o bloco comeca no offset 4 -- ver
        // `message::molde::campo`. Sem bloco vale asmodiano, que e a raca do molde.
        let raca = aparencia
            .get(56..60)
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);
        let ponto = mundo::ponto_de_entrada(raca);

        self.conn.execute(
            "INSERT INTO characters(account_id, name, level, exp, x, y, z, map_id, heading, hp, mp, aparencia)
             VALUES (?1, ?2, 1, 0, ?3, ?4, ?5, ?6, ?7, 100, 100, ?8)",
            params![
                account_id,
                nome,
                ponto.x,
                ponto.y,
                ponto.z,
                ponto.mapa as i64,
                ponto.direcao as i64,
                aparencia
            ],
        )?;
        let id = self.conn.last_insert_rowid();

        Ok(PersistedCharacter {
            id: id as u32,
            account_id,
            name: nome.to_string(),
            level: 1,
            exp: 0,
            x: ponto.x,
            y: ponto.y,
            z: ponto.z,
            map_id: ponto.mapa,
            heading: ponto.direcao,
            hp: 100,
            mp: 100,
            aparencia: Some(aparencia.to_vec()),
        })
    }

    /// Deleta um personagem pertencente ao usuário especificado e remove seus itens associados.
    pub fn deletar_personagem(&self, username: &str, character_id: u32) -> Result<bool> {
        let account_id: Option<i64> = self
            .conn
            .query_row(
                "SELECT id FROM accounts WHERE name = ?1 OR username = ?1 COLLATE NOCASE",
                params![username],
                |row| row.get(0),
            )
            .optional()?;
        let Some(account_id) = account_id else {
            return Ok(false);
        };

        self.conn.execute(
            "DELETE FROM character_items WHERE character_id = ?1",
            params![character_id],
        )?;

        let rows = self.conn.execute(
            "DELETE FROM characters WHERE id = ?1 AND account_id = ?2",
            params![character_id, account_id],
        )?;

        Ok(rows > 0)
    }

    pub fn load_or_create_character(
        &self,
        username: &str,
    ) -> Result<PersistedCharacter> {
        use crate::game::mundo;

        self.conn.execute(
            "INSERT OR IGNORE INTO accounts(name, password_hash, access_level, membership, created_at) VALUES (?1, ?1, 0, 0, strftime('%s','now'))",
            params![username],
        )?;
        let account_id: i64 = self.conn.query_row(
            "SELECT id FROM accounts WHERE name = ?1 OR username = ?1 COLLATE NOCASE",
            params![username],
            |row| row.get(0),
        )?;

        let existing: Option<PersistedCharacter> = self
            .conn
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

        if let Some(c) = existing {
            return Ok(c);
        }

        self.conn.execute(
            "INSERT INTO characters(account_id, name, level, exp, x, y, z, map_id, heading, hp, mp)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
            params![
                account_id,
                "Azphelumbra",
                14_i64,
                226_334_i64,
                mundo::X,
                mundo::Y,
                mundo::Z,
                mundo::MAPA as i64,
                mundo::DIRECAO as i64,
                1148_i64,
                1080_i64,
            ],
        )?;
        let id = self.conn.last_insert_rowid() as u32;

        Ok(PersistedCharacter {
            id,
            account_id,
            name: "Azphelumbra".into(),
            level: 14,
            exp: 226_334,
            x: mundo::X,
            y: mundo::Y,
            z: mundo::Z,
            map_id: mundo::MAPA,
            heading: mundo::DIRECAO,
            hp: 1148,
            mp: 1080,
            // O personagem fixo nao veio de uma criacao, entao nao tem bloco: cai no molde.
            aparencia: None,
        })
    }

    /// Entrega o kit inicial a um personagem que ainda nao o recebeu.
    ///
    /// Devolve `true` se entregou agora. A marca fica no personagem, nao na bolsa: gastar os
    /// itens nao faz o kit voltar no login seguinte.
    pub fn garante_kit_inicial(
        &self,
        character_id: u32,
        itens: &[(u32, u32)],
    ) -> Result<bool> {
        // Personagem que nao esta no banco -- o da bisseccao, por exemplo -- nao tem kit a
        // receber. Nao e erro: e um personagem que so existe em memoria.
        let ja: Option<i64> = self
            .conn
            .query_row(
                "SELECT kit_inicial FROM characters WHERE id = ?1",
                params![character_id as i64],
                |row| row.get(0),
            )
            .optional()?;
        if ja != Some(0) {
            return Ok(false);
        }

        // A casa da bolsa e a ordem do kit. O cliente arruma sozinho depois.
        for (posicao, (item_id, quantidade)) in itens.iter().enumerate() {
            self.conn.execute(
                "INSERT INTO character_items(character_id, item_id, quantidade, posicao)
                 VALUES (?1, ?2, ?3, ?4)",
                params![
                    character_id as i64,
                    *item_id as i64,
                    *quantidade as i64,
                    posicao as i64
                ],
            )?;
        }

        self.conn.execute(
            "UPDATE characters SET kit_inicial = 1 WHERE id = ?1",
            params![character_id as i64],
        )?;
        Ok(true)
    }

    /// O que esta na bolsa, na ordem das casas.
    ///
    /// O `id` da linha vira o id de objeto do item. O cliente 4.5 espera esse numero na faixa que
    /// comeca em `0xC0`: na captura, os 119 itens do servidor oficial estao todos la.
    pub fn itens_do_personagem(&self, character_id: u32) -> Result<Vec<ItemPersistido>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, item_id, quantidade, posicao FROM character_items
             WHERE character_id = ?1 ORDER BY posicao, id",
        )?;
        let linhas = stmt.query_map(params![character_id as i64], |row| {
            Ok(ItemPersistido {
                obj_id: OBJ_ID_BASE | (row.get::<_, i64>(0)? as u32 & !OBJ_ID_BASE),
                item_id: row.get::<_, i64>(1)? as u32,
                quantidade: row.get::<_, i64>(2)? as u64,
                posicao: row.get::<_, i64>(3)? as u16,
            })
        })?;
        linhas.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub const KINAH_ITEM_ID: u32 = 182_400_001;

    /// Adiciona item ou empilha no inventário persistido
    pub fn adicionar_item(
        &self,
        character_id: u32,
        item_id: u32,
        quantidade: u64,
        posicao: u16,
    ) -> Result<u32> {
        let existente: Option<(i64, i64)> = self
            .conn
            .query_row(
                "SELECT id, quantidade FROM character_items WHERE character_id = ?1 AND item_id = ?2 AND posicao = ?3",
                params![character_id as i64, item_id as i64, posicao as i64],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .optional()?;

        if let Some((row_id, qtd_atual)) = existente {
            let nova_qtd = qtd_atual + quantidade as i64;
            self.conn.execute(
                "UPDATE character_items SET quantidade = ?1 WHERE id = ?2",
                params![nova_qtd, row_id],
            )?;
            Ok(OBJ_ID_BASE | (row_id as u32 & !OBJ_ID_BASE))
        } else {
            self.conn.execute(
                "INSERT INTO character_items (character_id, item_id, quantidade, posicao) VALUES (?1, ?2, ?3, ?4)",
                params![character_id as i64, item_id as i64, quantidade as i64, posicao as i64],
            )?;
            let row_id = self.conn.last_insert_rowid();
            Ok(OBJ_ID_BASE | (row_id as u32 & !OBJ_ID_BASE))
        }
    }

    /// Remove item do inventário do personagem
    pub fn remover_item(&self, character_id: u32, item_id: u32, quantidade: u64) -> Result<bool> {
        let mut restante = quantidade as i64;
        let mut stmt = self.conn.prepare(
            "SELECT id, quantidade FROM character_items WHERE character_id = ?1 AND item_id = ?2 ORDER BY posicao ASC",
        )?;
        let rows: Vec<(i64, i64)> = stmt
            .query_map(params![character_id as i64, item_id as i64], |r| Ok((r.get(0)?, r.get(1)?)))?
            .filter_map(std::result::Result::ok)
            .collect();

        for (row_id, qtd) in rows {
            if restante <= 0 {
                break;
            }
            if qtd <= restante {
                self.conn.execute("DELETE FROM character_items WHERE id = ?1", params![row_id])?;
                restante -= qtd;
            } else {
                self.conn.execute("UPDATE character_items SET quantidade = ?1 WHERE id = ?2", params![qtd - restante, row_id])?;
                restante = 0;
            }
        }

        Ok(restante == 0)
    }

    /// Consulta saldo de Kinah
    pub fn obter_kinah(&self, character_id: u32) -> Result<u64> {
        let total: i64 = self
            .conn
            .query_row(
                "SELECT COALESCE(SUM(quantidade), 0) FROM character_items WHERE character_id = ?1 AND item_id = ?2",
                params![character_id as i64, Self::KINAH_ITEM_ID as i64],
                |row| row.get(0),
            )?;
        Ok(total.max(0) as u64)
    }

    /// Altera o saldo de Kinah (positivo = ganho, negativo = gasto)
    pub fn alterar_kinah(&self, character_id: u32, delta: i64) -> Result<bool> {
        let saldo_atual = self.obter_kinah(character_id)? as i64;
        if saldo_atual + delta < 0 {
            return Ok(false); // Saldo insuficiente
        }
        if delta > 0 {
            self.adicionar_item(character_id, Self::KINAH_ITEM_ID, delta as u64, 0)?;
        } else if delta < 0 {
            self.remover_item(character_id, Self::KINAH_ITEM_ID, (-delta) as u64)?;
        }
        Ok(true)
    }

    pub fn save_character(
        &self,
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
        self.conn.execute(
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

    /// Salva as skills ativas do personagem
    pub fn salvar_skills(&self, char_id: u32, skills: &[(u32, u8)]) -> Result<()> {
        let mut stmt = self.conn.prepare(
            "INSERT INTO character_skills (character_id, skill_id, skill_level)
             VALUES (?1, ?2, ?3)
             ON CONFLICT(character_id, skill_id) DO UPDATE SET skill_level = excluded.skill_level"
        )?;
        for &(skill_id, skill_level) in skills {
            stmt.execute(params![char_id as i64, skill_id as i64, skill_level as i64])?;
        }
        Ok(())
    }

    /// Carrega as skills do personagem
    pub fn carregar_skills(&self, char_id: u32) -> Result<Vec<(u32, u8)>> {
        let mut stmt = self.conn.prepare(
            "SELECT skill_id, skill_level FROM character_skills WHERE character_id = ?1"
        )?;
        let rows = stmt.query_map(params![char_id as i64], |row| {
            let sid: i64 = row.get(0)?;
            let lvl: i64 = row.get(1)?;
            Ok((sid as u32, lvl as u8))
        })?;
        let mut res = Vec::new();
        for r in rows {
            res.push(r?);
        }
        Ok(res)
    }

    /// Executa migração e validações de integridade do banco SQLite
    pub fn migrate(&self) -> Result<()> {
        self.conn.execute_batch("
            PRAGMA journal_mode = WAL;
            PRAGMA busy_timeout = 5000;
            PRAGMA synchronous = NORMAL;
            PRAGMA foreign_keys = ON;
        ")?;
        self.init_schema()?;
        self.conn.execute_batch("PRAGMA user_version = 2;")?;
        Ok(())
    }

    /// Salva ou atualiza o estado de uma missão do personagem
    pub fn salvar_quest(
        &self,
        character_id: u32,
        quest_id: u32,
        status: &str,
        quest_vars: u32,
        complete_count: u32,
    ) -> Result<()> {
        self.conn.execute(
            "INSERT INTO player_quests (character_id, quest_id, status, quest_vars, complete_count)
             VALUES (?1, ?2, ?3, ?4, ?5)
             ON CONFLICT(character_id, quest_id) DO UPDATE SET
             status = excluded.status, quest_vars = excluded.quest_vars, complete_count = excluded.complete_count",
            params![character_id as i64, quest_id as i64, status, quest_vars as i64, complete_count as i64],
        )?;
        Ok(())
    }

    /// Salva estado da quest usando tipos numéricos
    pub fn save_quest(
        &self,
        character_id: u32,
        quest_id: u32,
        status: u8,
        flags: u32,
        vars: [u32; 4],
        _start_ts: u32,
    ) -> Result<()> {
        let status_str = match status {
            0 => "START",
            1 => "COMPLETE",
            _ => "REWARD",
        };
        self.salvar_quest(character_id, quest_id, status_str, vars[0], flags)
    }

    /// Retorna todas as missões ativas ou concluídas do personagem
    pub fn quests_do_personagem(&self, character_id: u32) -> Result<Vec<QuestPersistida>> {
        let mut stmt = self.conn.prepare(
            "SELECT quest_id, status, quest_vars, complete_count FROM player_quests WHERE character_id = ?1",
        )?;
        let rows = stmt.query_map(params![character_id as i64], |row| {
            Ok(QuestPersistida {
                quest_id: row.get::<_, i64>(0)? as u32,
                status: row.get(1)?,
                quest_vars: row.get::<_, i64>(2)? as u32,
                complete_count: row.get::<_, i64>(3)? as u32,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn salvar_carta(
        &self,
        recipient_id: u32,
        sender_name: &str,
        title: &str,
        body: &str,
        letter_type: u8,
        item_template_id: u32,
        item_quantity: u32,
        kinah_amount: u64,
    ) -> Result<u32> {
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        self.conn.execute(
            "INSERT INTO character_mail (recipient_id, sender_name, title, body, letter_type, item_template_id, item_quantity, kinah_amount, timestamp)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                recipient_id as i64,
                sender_name,
                title,
                body,
                letter_type as i64,
                item_template_id as i64,
                item_quantity as i64,
                kinah_amount as i64,
                ts as i64,
            ],
        )?;
        Ok(self.conn.last_insert_rowid() as u32)
    }

    pub fn cartas_do_personagem(&self, recipient_id: u32) -> Result<Vec<crate::game::mail::Letter>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, sender_name, recipient_id, title, body, item_template_id, item_quantity, kinah_amount, letter_type, is_read, timestamp
             FROM character_mail WHERE recipient_id = ?1 ORDER BY id ASC",
        )?;
        let rows = stmt.query_map(params![recipient_id as i64], |row| {
            let ltype_num: u8 = row.get::<_, i64>(8)? as u8;
            let ltype = match ltype_num {
                1 => crate::game::mail::LetterType::Express,
                2 => crate::game::mail::LetterType::System,
                3 => crate::game::mail::LetterType::Blackcloud,
                _ => crate::game::mail::LetterType::Regular,
            };
            Ok(crate::game::mail::Letter {
                id: row.get::<_, i64>(0)? as u32,
                sender_name: row.get(1)?,
                recipient_id: row.get::<_, i64>(2)? as u32,
                title: row.get(3)?,
                message: row.get(4)?,
                attached_item_id: row.get::<_, i64>(5)? as u32,
                attached_item_count: row.get::<_, i64>(6)? as u32,
                attached_kinah: row.get::<_, i64>(7)? as u64,
                letter_type: ltype,
                is_read: row.get::<_, i64>(9)? != 0,
                is_express: ltype_num == 1,
                timestamp_sec: row.get::<_, i64>(10)? as u64,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn marcar_carta_lida(&self, letter_id: u32) -> Result<bool> {
        let n = self.conn.execute(
            "UPDATE character_mail SET is_read = 1 WHERE id = ?1",
            params![letter_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn deletar_carta(&self, letter_id: u32) -> Result<bool> {
        let n = self.conn.execute(
            "DELETE FROM character_mail WHERE id = ?1 AND kinah_amount = 0 AND item_template_id = 0",
            params![letter_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn extrair_anexos_carta(&self, letter_id: u32) -> Result<bool> {
        let n = self.conn.execute(
            "UPDATE character_mail SET kinah_amount = 0, item_template_id = 0, item_quantity = 0 WHERE id = ?1",
            params![letter_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn criar_guild(&self, name: &str, race: u8, leader_id: u32) -> Result<u32> {
        self.conn.execute(
            "INSERT INTO guilds (name, race, leader_id) VALUES (?1, ?2, ?3)",
            params![name, race as i64, leader_id as i64],
        )?;
        let guild_id = self.conn.last_insert_rowid() as u32;
        self.adicionar_membro_guild(guild_id, leader_id, 1)?;
        Ok(guild_id)
    }

    pub fn adicionar_membro_guild(&self, guild_id: u32, player_id: u32, rank_index: u8) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO guild_members (guild_id, player_id, rank_index, contribution) VALUES (?1, ?2, ?3, 0)",
            params![guild_id as i64, player_id as i64, rank_index as i64],
        )?;
        Ok(())
    }

    pub fn remover_membro_guild(&self, guild_id: u32, player_id: u32) -> Result<bool> {
        let n = self.conn.execute(
            "DELETE FROM guild_members WHERE guild_id = ?1 AND player_id = ?2",
            params![guild_id as i64, player_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn guild_do_jogador(&self, player_id: u32) -> Result<Option<crate::game::guild::Guild>> {
        let mut stmt = self.conn.prepare(
            "SELECT g.id, g.name, g.rank, g.race, g.exp, g.leader_id, g.notice, g.kinah
             FROM guilds g
             INNER JOIN guild_members gm ON gm.guild_id = g.id
             WHERE gm.player_id = ?1",
        )?;
        let mut rows = stmt.query_map(params![player_id as i64], |row| {
            Ok(crate::game::guild::Guild {
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
            // Carrega membros
            let mut mstmt = self.conn.prepare(
                "SELECT gm.player_id, c.name, gm.rank_index, gm.contribution
                 FROM guild_members gm
                 INNER JOIN characters c ON c.id = gm.player_id
                 WHERE gm.guild_id = ?1",
            )?;
            let mrows = mstmt.query_map(params![guild.id as i64], |mrow| {
                Ok(crate::game::guild::GuildMember {
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

    pub fn adicionar_amigo(&self, player_id: u32, buddy_id: u32) -> Result<()> {
        self.conn.execute(
            "INSERT OR IGNORE INTO character_buddies (player_id, buddy_id) VALUES (?1, ?2)",
            params![player_id as i64, buddy_id as i64],
        )?;
        Ok(())
    }

    pub fn remover_amigo(&self, player_id: u32, buddy_id: u32) -> Result<bool> {
        let n = self.conn.execute(
            "DELETE FROM character_buddies WHERE player_id = ?1 AND buddy_id = ?2",
            params![player_id as i64, buddy_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn amigos_do_personagem(&self, player_id: u32) -> Result<Vec<crate::game::message::server::BuddyEntry>> {
        let mut stmt = self.conn.prepare(
            "SELECT c.id, c.name, c.level, c.map_id
             FROM character_buddies b
             INNER JOIN characters c ON c.id = b.buddy_id
             WHERE b.player_id = ?1",
        )?;
        let rows = stmt.query_map(params![player_id as i64], |row| {
            Ok(crate::game::message::server::BuddyEntry {
                player_id: row.get::<_, i64>(0)? as u32,
                name: row.get(1)?,
                is_online: true,
                map_id: row.get::<_, i64>(3)? as u32,
                level: row.get::<_, i64>(2)? as u8,
                class_id: 1,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn buscar_personagem_por_nome(&self, name: &str) -> Result<Option<PersistedCharacter>> {
        let mut stmt = self.conn.prepare(
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

    pub fn salvar_anuncio_broker(
        &self,
        seller_id: u32,
        seller_name: &str,
        item_template_id: u32,
        quantity: u32,
        price_per_unit: u64,
        expiry_ts: u64,
        quality: u8,
        enhance_level: u8,
    ) -> Result<u32> {
        self.conn.execute(
            "INSERT INTO broker_listings (seller_id, seller_name, item_template_id, quantity, price_per_unit, expiry_ts, quality, enhance_level, is_sold)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 0)",
            params![
                seller_id as i64,
                seller_name,
                item_template_id as i64,
                quantity as i64,
                price_per_unit as i64,
                expiry_ts as i64,
                quality as i64,
                enhance_level as i64,
            ],
        )?;
        Ok(self.conn.last_insert_rowid() as u32)
    }

    pub fn listar_anuncios_broker(
        &self,
        page: u32,
        page_size: u8,
    ) -> Result<(u32, Vec<crate::game::message::server::GlobalTradeListingEntry>)> {
        let total: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM broker_listings WHERE is_sold = 0",
            [],
            |r| r.get(0),
        )?;

        let offset = (page as i64) * (page_size as i64);
        let mut stmt = self.conn.prepare(
            "SELECT id, item_template_id, quantity, price_per_unit, seller_name, expiry_ts, quality, enhance_level
             FROM broker_listings
             WHERE is_sold = 0
             ORDER BY id DESC
             LIMIT ?1 OFFSET ?2",
        )?;
        let rows = stmt.query_map(params![page_size as i64, offset], |row| {
            Ok(crate::game::message::server::GlobalTradeListingEntry {
                listing_id: row.get::<_, i64>(0)? as u32,
                item_template_id: row.get::<_, i64>(1)? as u32,
                quantity: row.get::<_, i64>(2)? as u32,
                price_per_unit: row.get::<_, i64>(3)? as u64,
                seller_name: row.get(4)?,
                expiry_timestamp: row.get::<_, i64>(5)? as u64,
                quality: row.get::<_, i64>(6)? as u8,
                enhance_level: row.get::<_, i64>(7)? as u8,
            })
        })?;
        let entries = rows.collect::<std::result::Result<Vec<_>, _>>()?;
        Ok((total as u32, entries))
    }

    pub fn comprar_anuncio_broker(&self, listing_id: u32) -> Result<Option<(u32, String, u32, u32, u64)>> {
        let mut stmt = self.conn.prepare(
            "SELECT seller_id, seller_name, item_template_id, quantity, price_per_unit
             FROM broker_listings WHERE id = ?1 AND is_sold = 0",
        )?;
        let mut rows = stmt.query_map(params![listing_id as i64], |row| {
            Ok((
                row.get::<_, i64>(0)? as u32,
                row.get::<_, String>(1)?,
                row.get::<_, i64>(2)? as u32,
                row.get::<_, i64>(3)? as u32,
                row.get::<_, i64>(4)? as u64,
            ))
        })?;
        if let Some(r) = rows.next() {
            let res = r?;
            self.conn.execute("UPDATE broker_listings SET is_sold = 1 WHERE id = ?1", params![listing_id as i64])?;
            Ok(Some(res))
        } else {
            Ok(None)
        }
    }

    pub fn salvar_historico_broker(
        &self,
        player_id: u32,
        item_template_id: u32,
        quantity: u32,
        price: u64,
        timestamp: u64,
        trade_type: u8,
    ) -> Result<()> {
        self.conn.execute(
            "INSERT INTO broker_history (player_id, item_template_id, quantity, price, timestamp, type)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                player_id as i64,
                item_template_id as i64,
                quantity as i64,
                price as i64,
                timestamp as i64,
                trade_type as i64,
            ],
        )?;
        Ok(())
    }

    pub fn historico_vendas_item(
        &self,
        item_template_id: u32,
        quality: u8,
    ) -> Result<Vec<crate::game::message::server::GlobalTradeSaleslogEntry>> {
        let mut stmt = self.conn.prepare(
            "SELECT item_template_id, quantity, price, timestamp
             FROM broker_history
             WHERE item_template_id = ?1
             ORDER BY timestamp DESC
             LIMIT 50",
        )?;
        let rows = stmt.query_map(params![item_template_id as i64], |row| {
            Ok(crate::game::message::server::GlobalTradeSaleslogEntry {
                item_template_id: row.get::<_, i64>(0)? as u32,
                quantity: row.get::<_, i64>(1)? as u32,
                price: row.get::<_, i64>(2)? as u64,
                timestamp: row.get::<_, i64>(3)? as u64,
                quality,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn preco_medio_item(&self, item_template_id: u32) -> Result<u64> {
        let avg: Option<f64> = self.conn.query_row(
            "SELECT AVG(price) FROM broker_history WHERE item_template_id = ?1",
            params![item_template_id as i64],
            |r| r.get(0),
        )?;
        Ok(avg.unwrap_or(0.0) as u64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn in_memory() -> Db {
        let conn = Connection::open_in_memory().unwrap();
        let db = Db { conn };
        db.init_schema().unwrap();
        db
    }

    #[test]
    fn load_or_create_is_idempotent_and_persists_updates() {
        let db = in_memory();

        let a = db.load_or_create_character("alice").unwrap();
        assert_eq!(a.name, "Azphelumbra");
        assert_eq!(a.level, 14);
        assert_eq!(a.x, crate::game::mundo::X, "personagem novo nasce no ponto de entrada");

        let b = db.load_or_create_character("alice").unwrap();
        assert_eq!(a.id, b.id, "second call must return same character id");
        assert_eq!(a.account_id, b.account_id);

        db.save_character(a.id, 100.0, 200.0, 300.0, 110010000, 45, 20, 999_999, 500, 250)
            .unwrap();

        let c = db.load_or_create_character("alice").unwrap();
        assert_eq!(c.id, a.id);
        assert_eq!(c.level, 20);
        assert_eq!(c.exp, 999_999);
        assert_eq!(c.x, 100.0);
        assert_eq!(c.y, 200.0);
        assert_eq!(c.z, 300.0);
        assert_eq!(c.map_id, 110010000);
        assert_eq!(c.heading, 45);
        assert_eq!(c.hp, 500);
        assert_eq!(c.mp, 250);
    }

    #[test]
    fn kit_inicial_e_entregue_uma_vez_so() {
        let db = in_memory();
        let c = db.load_or_create_character("alice").unwrap();

        let kit = [(182_400_001u32, 1000u32), (100_000_094, 1), (160_000_001, 12)];
        assert!(db.garante_kit_inicial(c.id, &kit).unwrap(), "primeira vez entrega");
        assert!(
            !db.garante_kit_inicial(c.id, &kit).unwrap(),
            "segunda vez nao entrega de novo"
        );

        let itens = db.itens_do_personagem(c.id).unwrap();
        assert_eq!(itens.len(), 3, "o kit nao foi duplicado");
        assert_eq!(itens[0].item_id, 182_400_001);
        assert_eq!(itens[0].quantidade, 1000);
        assert_eq!(itens[0].posicao, 0);
        assert_eq!(itens[2].posicao, 2, "a casa da bolsa segue a ordem do kit");
        for item in &itens {
            assert_eq!(
                item.obj_id & 0xFF00_0000,
                0xC000_0000,
                "id de objeto na faixa que o cliente espera de item"
            );
        }
    }

    #[test]
    fn different_usernames_get_different_accounts_and_characters() {
        let db = in_memory();
        let a = db.load_or_create_character("alice").unwrap();
        let b = db.load_or_create_character("bob").unwrap();
        assert_ne!(a.account_id, b.account_id);
        assert_ne!(a.id, b.id);
    }

    #[test]
    fn deletar_personagem_remove_registro_e_itens() {
        let db = in_memory();
        let c = db.load_or_create_character("alice").unwrap();
        let kit = [(182_400_001u32, 1000u32)];
        db.garante_kit_inicial(c.id, &kit).unwrap();

        assert!(db.deletar_personagem("alice", c.id).unwrap(), "deve deletar com sucesso");
        assert!(!db.deletar_personagem("alice", c.id).unwrap(), "segunda tentativa nao deve achar nada");

        let itens = db.itens_do_personagem(c.id).unwrap();
        assert!(itens.is_empty(), "itens associados devem ter sido removidos");
    }

    #[test]
    fn item_adicionar_remover_e_kinah_saldo() {
        let db = in_memory();
        let c = db.load_or_create_character("alice").unwrap();

        // Adiciona 500 kinah
        assert!(db.alterar_kinah(c.id, 500).unwrap());
        assert_eq!(db.obter_kinah(c.id).unwrap(), 500);

        // Tenta gastar 600 kinah (deve falhar por saldo insuficiente)
        assert!(!db.alterar_kinah(c.id, -600).unwrap());
        assert_eq!(db.obter_kinah(c.id).unwrap(), 500);

        // Gasta 200 kinah
        assert!(db.alterar_kinah(c.id, -200).unwrap());
        assert_eq!(db.obter_kinah(c.id).unwrap(), 300);

        // Adiciona pocao de HP (id: 160000001)
        db.adicionar_item(c.id, 160_000_001, 10, 1).unwrap();
        assert!(db.remover_item(c.id, 160_000_001, 4).unwrap());
        let itens = db.itens_do_personagem(c.id).unwrap();
        let pocao = itens.iter().find(|i| i.item_id == 160_000_001).unwrap();
        assert_eq!(pocao.quantidade, 6);
    }

    #[test]
    fn quest_salvar_e_carregar_progresso() {
        let db = in_memory();
        let c = db.load_or_create_character("alice").unwrap();

        // Inicia quest 1001
        db.salvar_quest(c.id, 1001, "IN_PROGRESS", 1, 0).unwrap();
        let quests = db.quests_do_personagem(c.id).unwrap();
        assert_eq!(quests.len(), 1);
        assert_eq!(quests[0].quest_id, 1001);
        assert_eq!(quests[0].status, "IN_PROGRESS");
        assert_eq!(quests[0].quest_vars, 1);

        // Atualiza progresso da quest 1001 para REWARDABLE
        db.salvar_quest(c.id, 1001, "REWARDABLE", 3, 0).unwrap();
        let quests_up = db.quests_do_personagem(c.id).unwrap();
        assert_eq!(quests_up.len(), 1);
        assert_eq!(quests_up[0].status, "REWARDABLE");
        assert_eq!(quests_up[0].quest_vars, 3);
    }

    #[test]
    fn mail_salvar_ler_extrair_e_deletar() {
        let db = in_memory();
        let c = db.load_or_create_character("alice").unwrap();

        let letter_id = db
            .salvar_carta(
                c.id,
                "Shugo",
                "Bem-vindo",
                "Segue seu presente",
                1,
                10000001,
                1,
                5000,
            )
            .unwrap();

        let cartas = db.cartas_do_personagem(c.id).unwrap();
        assert_eq!(cartas.len(), 1);
        assert_eq!(cartas[0].id, letter_id);
        assert_eq!(cartas[0].sender_name, "Shugo");
        assert_eq!(cartas[0].attached_kinah, 5000);
        assert_eq!(cartas[0].attached_item_id, 10000001);
        assert!(!cartas[0].is_read);

        // Marca lida
        assert!(db.marcar_carta_lida(letter_id).unwrap());
        let cartas = db.cartas_do_personagem(c.id).unwrap();
        assert!(cartas[0].is_read);

        // Nao pode deletar com anexo
        assert!(!db.deletar_carta(letter_id).unwrap());

        // Extrai anexo
        assert!(db.extrair_anexos_carta(letter_id).unwrap());

        // Agora pode deletar
        assert!(db.deletar_carta(letter_id).unwrap());
        let cartas = db.cartas_do_personagem(c.id).unwrap();
        assert!(cartas.is_empty());
    }

    #[test]
    fn guild_criar_adicionar_e_carregar() {
        let db = in_memory();
        let leader = db.load_or_create_character("alice").unwrap();
        let member = db.load_or_create_character("bob").unwrap();

        let gid = db.criar_guild("Olympus", 0, leader.id).unwrap();
        db.adicionar_membro_guild(gid, member.id, 5).unwrap();

        let g_opt = db.guild_do_jogador(leader.id).unwrap();
        assert!(g_opt.is_some());
        let g = g_opt.unwrap();
        assert_eq!(g.id, gid);
        assert_eq!(g.name, "Olympus");
        assert_eq!(g.members.len(), 2);

        // Remove membro
        assert!(db.remover_membro_guild(gid, member.id).unwrap());
        let g2 = db.guild_do_jogador(leader.id).unwrap().unwrap();
        assert_eq!(g2.members.len(), 1);
    }

    #[test]
    fn buddy_adicionar_remover_e_listar() {
        let db = in_memory();
        let alice = db.load_or_create_character("alice").unwrap();
        let bob = db.load_or_create_character("bob").unwrap();

        db.adicionar_amigo(alice.id, bob.id).unwrap();
        let amigos = db.amigos_do_personagem(alice.id).unwrap();
        assert_eq!(amigos.len(), 1);
        assert_eq!(amigos[0].player_id, bob.id);

        assert!(db.remover_amigo(alice.id, bob.id).unwrap());
        let amigos2 = db.amigos_do_personagem(alice.id).unwrap();
        assert!(amigos2.is_empty());
    }

    #[test]
    fn broker_salvar_listar_comprar_e_historico() {
        let db = in_memory();
        let seller = db.load_or_create_character("vendedor").unwrap();
        let buyer = db.load_or_create_character("comprador").unwrap();

        let lid = db.salvar_anuncio_broker(seller.id, &seller.name, 182000001, 10, 5000, 1700000000, 2, 0).unwrap();
        let (total, list) = db.listar_anuncios_broker(0, 20).unwrap();
        assert_eq!(total, 1);
        assert_eq!(list[0].listing_id, lid);

        let buy = db.comprar_anuncio_broker(lid).unwrap().unwrap();
        assert_eq!(buy.0, seller.id);
        assert_eq!(buy.2, 182000001);

        let (total_after, _) = db.listar_anuncios_broker(0, 20).unwrap();
        assert_eq!(total_after, 0);

        db.salvar_historico_broker(buyer.id, 182000001, 10, 50000, 1699999999, 1).unwrap();
        let logs = db.historico_vendas_item(182000001, 2).unwrap();
        assert_eq!(logs.len(), 1);
        assert_eq!(logs[0].price, 50000);

        let avg = db.preco_medio_item(182000001).unwrap();
        assert_eq!(avg, 50000);
    }

    #[test]
    fn skills_salvar_e_carregar_e_migrate() {
        let db = in_memory();
        db.migrate().unwrap();
        let hero = db.load_or_create_character("heroi").unwrap();
        let skills = vec![(1001, 1), (1002, 2), (2001, 5)];
        db.salvar_skills(hero.id, &skills).unwrap();
        let loaded = db.carregar_skills(hero.id).unwrap();
        assert_eq!(loaded.len(), 3);
        assert_eq!(loaded[0], (1001, 1));
        assert_eq!(loaded[2], (2001, 5));
    }
}
