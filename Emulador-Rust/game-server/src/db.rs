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
            ",
        )?;

        // Compatibilidade com colunas legadas se existirem
        let _ = self.conn.execute("ALTER TABLE characters ADD COLUMN aparencia BLOB", []);
        let _ = self.conn.execute("ALTER TABLE characters ADD COLUMN kit_inicial INTEGER NOT NULL DEFAULT 0", []);
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

    /// Valida a sessao pelo par que o cliente apresenta no `C_HQ_LOGIN` (0xF0) e devolve o nome
    /// da conta.
    ///
    /// Esses dois `u32` sao os unicos dados de autenticacao que chegam ao game server: o cliente
    /// os recebe do login server no pacote `0x04` da porta 13001 e os repete intactos. Confirmado
    /// nas duas capturas do servidor oficial -- a chave do `0x04` reaparece byte a byte no `0xF0`.
    ///
    /// Uma linha expirada nao vale: `expires_at` zero significa "sem prazo" (sessoes antigas,
    /// gravadas antes da coluna existir).
    pub fn resolver_sessao(&self, account_id: u32, session_key: u32) -> Result<Option<String>> {
        let agora = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs() as i64)
            .unwrap_or(0);

        self.conn
            .query_row(
                "SELECT COALESCE(NULLIF(account_name, ''), username) FROM sessions
                 WHERE account_id = ?1 AND session_key = ?2
                   AND (expires_at = 0 OR expires_at >= ?3)
                 ORDER BY created_at DESC LIMIT 1",
                params![account_id as i64, session_key as i64, agora],
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
            "SELECT id, account_id, name, level, exp, x, y, z, hp, mp, aparencia
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
                hp: row.get::<_, i64>(8)? as i32,
                mp: row.get::<_, i64>(9)? as u32,
                aparencia: row.get(10)?,
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
            "INSERT INTO characters(account_id, name, level, exp, x, y, z, hp, mp, aparencia)
             VALUES (?1, ?2, 1, 0, ?3, ?4, ?5, 100, 100, ?6)",
            params![account_id, nome, ponto.x, ponto.y, ponto.z, aparencia],
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
                "SELECT id, account_id, name, level, exp, x, y, z, hp, mp, aparencia
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
                        hp: row.get::<_, i64>(8)? as i32,
                        mp: row.get::<_, i64>(9)? as u32,
                        aparencia: row.get(10)?,
                    })
                },
            )
            .ok();

        if let Some(c) = existing {
            return Ok(c);
        }

        self.conn.execute(
            "INSERT INTO characters(account_id, name, level, exp, x, y, z, hp, mp)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                account_id,
                "Azphelumbra",
                14_i64,
                226_334_i64,
                mundo::X,
                mundo::Y,
                mundo::Z,
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
        level: u16,
        exp: u64,
        hp: i32,
        mp: u32,
    ) -> Result<()> {
        self.conn.execute(
            "UPDATE characters
             SET x=?1, y=?2, z=?3, level=?4, exp=?5, hp=?6, mp=?7,
                 updated_at=strftime('%s','now')
             WHERE id=?8",
            params![
                x,
                y,
                z,
                level as i64,
                exp as i64,
                hp as i64,
                mp as i64,
                id as i64
            ],
        )?;
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

    /// Grava uma linha em `sessions` como o login server faz ao mandar o pacote 0x04.
    fn grava_sessao(db: &Db, token: &str, conta: &str, account_id: u32, key: u32, expires_at: i64) {
        db.conn
            .execute(
                "INSERT INTO sessions (token, account_name, account_id, session_key, created_at, expires_at)
                 VALUES (?1, ?2, ?3, ?4, 0, ?5)",
                params![token, conta, account_id as i64, key as i64, expires_at],
            )
            .unwrap();
    }

    fn daqui_a(segundos: i64) -> i64 {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64
            + segundos
    }

    #[test]
    fn resolver_sessao_casa_o_par_do_hq_login() {
        let db = in_memory();
        // Os numeros sao os da captura de 21/08: conta 40820537, chave 0x161E.
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, daqui_a(600));

        assert_eq!(
            db.resolver_sessao(40_820_537, 0x161E).unwrap().as_deref(),
            Some("kamidaki")
        );
    }

    #[test]
    fn resolver_sessao_recusa_chave_errada() {
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, daqui_a(600));

        // Chave da outra captura, na mesma conta: nao pode valer.
        assert_eq!(db.resolver_sessao(40_820_537, 0x3939).unwrap(), None);
        // Conta errada com a chave certa tambem nao.
        assert_eq!(db.resolver_sessao(1, 0x161E).unwrap(), None);
    }

    #[test]
    fn resolver_sessao_recusa_sessao_expirada() {
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, daqui_a(-1));

        assert_eq!(db.resolver_sessao(40_820_537, 0x161E).unwrap(), None);
    }

    #[test]
    fn resolver_sessao_aceita_prazo_zero() {
        // Linhas gravadas antes de a coluna existir vem com expires_at = 0: sem prazo, nao
        // expiradas.
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, 0);

        assert_eq!(
            db.resolver_sessao(40_820_537, 0x161E).unwrap().as_deref(),
            Some("kamidaki")
        );
    }

    #[test]
    fn resolver_sessao_pega_a_mais_recente_da_conta() {
        // Relogar gera uma chave nova; a antiga nao pode continuar valendo por acidente.
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, daqui_a(600));
        grava_sessao(&db, "tok2", "kamidaki", 40_820_537, 0x3939, daqui_a(600));

        assert_eq!(
            db.resolver_sessao(40_820_537, 0x3939).unwrap().as_deref(),
            Some("kamidaki")
        );
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

        db.save_character(a.id, 100.0, 200.0, 300.0, 20, 999_999, 500, 250)
            .unwrap();

        let c = db.load_or_create_character("alice").unwrap();
        assert_eq!(c.id, a.id);
        assert_eq!(c.level, 20);
        assert_eq!(c.exp, 999_999);
        assert_eq!(c.x, 100.0);
        assert_eq!(c.y, 200.0);
        assert_eq!(c.z, 300.0);
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
}
