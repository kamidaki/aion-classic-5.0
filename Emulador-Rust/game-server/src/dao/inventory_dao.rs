use rusqlite::{params, Connection, OptionalExtension, Result};

pub const OBJ_ID_BASE: u32 = 0xC000_0000;
pub const KINAH_ITEM_ID: u32 = 182_400_001;

/// Uma linha da bolsa, como ela sai do banco.
#[derive(Debug, Clone)]
pub struct ItemPersistido {
    pub obj_id: u32,
    pub item_id: u32,
    pub quantidade: u64,
    pub posicao: u16,
}

pub struct InventoryDao;

impl InventoryDao {
    /// Salva a lista de itens iniciais de um novo personagem (vindos 100% dinamicamente do XML)
    pub fn salvar_itens_iniciais(
        conn: &Connection,
        character_id: u32,
        itens: &[(u32, u32)],
    ) -> Result<()> {
        for (pos, &(item_id, qtd)) in itens.iter().enumerate() {
            conn.execute(
                "INSERT INTO character_items (character_id, item_id, quantidade, posicao)
                 VALUES (?1, ?2, ?3, ?4)",
                params![character_id as i64, item_id as i64, qtd as i64, pos as i64],
            )?;
        }
        Ok(())
    }

    /// Entrega o kit inicial a um personagem que ainda não o recebeu
    pub fn garante_kit_inicial(
        conn: &Connection,
        character_id: u32,
        itens: &[(u32, u32)],
    ) -> Result<bool> {
        let ja: Option<i64> = conn
            .query_row(
                "SELECT kit_inicial FROM characters WHERE id = ?1",
                params![character_id as i64],
                |row| row.get(0),
            )
            .optional()?;
        if ja != Some(0) {
            return Ok(false);
        }

        let max_pos: i64 = conn
            .query_row(
                "SELECT COALESCE(MAX(posicao), -1) FROM character_items WHERE character_id = ?1",
                params![character_id as i64],
                |row| row.get(0),
            )
            .unwrap_or(-1);

        let mut pos = (max_pos + 1) as u16;
        for &(item_id, qtd) in itens {
            conn.execute(
                "INSERT INTO character_items (character_id, item_id, quantidade, posicao)
                 VALUES (?1, ?2, ?3, ?4)",
                params![character_id as i64, item_id as i64, qtd as i64, pos as i64],
            )?;
            pos += 1;
        }

        conn.execute(
            "UPDATE characters SET kit_inicial = 1 WHERE id = ?1",
            params![character_id as i64],
        )?;

        Ok(true)
    }

    pub fn itens_do_personagem(conn: &Connection, character_id: u32) -> Result<Vec<ItemPersistido>> {
        let mut stmt = conn.prepare(
            "SELECT id, item_id, quantidade, posicao
             FROM character_items
             WHERE character_id = ?1
             ORDER BY posicao ASC",
        )?;

        let rows = stmt.query_map(params![character_id as i64], |row| {
            let row_id: i64 = row.get(0)?;
            let item_id: i64 = row.get(1)?;
            let quantidade: i64 = row.get(2)?;
            let posicao: i64 = row.get(3)?;
            Ok(ItemPersistido {
                obj_id: OBJ_ID_BASE.wrapping_add(row_id as u32),
                item_id: item_id as u32,
                quantidade: quantidade as u64,
                posicao: posicao as u16,
            })
        })?;

        let mut itens = Vec::new();
        for r in rows {
            itens.push(r?);
        }
        Ok(itens)
    }

    pub fn adicionar_item(
        conn: &Connection,
        character_id: u32,
        item_id: u32,
        quantidade: u64,
        posicao: u16,
    ) -> Result<u32> {
        conn.execute(
            "INSERT INTO character_items (character_id, item_id, quantidade, posicao)
             VALUES (?1, ?2, ?3, ?4)",
            params![character_id as i64, item_id as i64, quantidade as i64, posicao as i64],
        )?;
        Ok(conn.last_insert_rowid() as u32)
    }

    pub fn remover_item(conn: &Connection, character_id: u32, item_id: u32, quantidade: u64) -> Result<bool> {
        let row: Option<(i64, i64)> = conn
            .query_row(
                "SELECT id, quantidade FROM character_items WHERE character_id = ?1 AND item_id = ?2 LIMIT 1",
                params![character_id as i64, item_id as i64],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .optional()?;

        if let Some((id, qty)) = row {
            if qty <= quantidade as i64 {
                conn.execute("DELETE FROM character_items WHERE id = ?1", params![id])?;
            } else {
                conn.execute(
                    "UPDATE character_items SET quantidade = quantidade - ?1 WHERE id = ?2",
                    params![quantidade as i64, id],
                )?;
            }
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn obter_kinah(conn: &Connection, character_id: u32) -> Result<u64> {
        let kinah: Option<i64> = conn
            .query_row(
                "SELECT quantidade FROM character_items WHERE character_id = ?1 AND item_id = ?2",
                params![character_id as i64, KINAH_ITEM_ID as i64],
                |r| r.get(0),
            )
            .optional()?;
        Ok(kinah.unwrap_or(0) as u64)
    }

    pub fn alterar_kinah(conn: &Connection, character_id: u32, diff: i64) -> Result<bool> {
        let cur = Self::obter_kinah(conn, character_id)? as i64;
        let novo = (cur + diff).max(0) as u64;

        let ja_existe: Option<i64> = conn
            .query_row(
                "SELECT id FROM character_items WHERE character_id = ?1 AND item_id = ?2",
                params![character_id as i64, KINAH_ITEM_ID as i64],
                |r| r.get(0),
            )
            .optional()?;

        if let Some(id) = ja_existe {
            conn.execute(
                "UPDATE character_items SET quantidade = ?1 WHERE id = ?2",
                params![novo as i64, id],
            )?;
        } else {
            conn.execute(
                "INSERT INTO character_items (character_id, item_id, quantidade, posicao)
                 VALUES (?1, ?2, ?3, 0)",
                params![character_id as i64, KINAH_ITEM_ID as i64, novo as i64],
            )?;
        }
        Ok(true)
    }

    pub fn transferir_item_entre_personagens(
        conn: &mut Connection,
        source_char_id: u32,
        target_char_id: u32,
        item_id: u32,
        count: u32,
    ) -> Result<bool> {
        let tx = conn.transaction()?;
        let removed = Self::remover_item(&tx, source_char_id, item_id, count as u64)?;
        if removed {
            Self::adicionar_item(&tx, target_char_id, item_id, count as u64, 0)?;
            tx.commit()?;
            Ok(true)
        } else {
            Ok(false)
        }
    }
}
