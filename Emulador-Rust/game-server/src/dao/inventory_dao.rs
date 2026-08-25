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
    /// Kit inicial de equipamentos por classe
    pub fn kit_for_class(class_id: u32) -> Vec<(u32, u32)> {
        match class_id {
            1 => vec![ // Gladiator
                (100000001, 1), // sword_l1_1a
                (110300001, 1), // lt_torso_n_l1_battlemaster_1a
                (110700001, 1), // lt_pants_n_l1_battlemaster_1a
                (111100001, 1), // lt_feet_n_l1_battlemaster_1a
                (111500001, 1), // lt_hands_n_l1_battlemaster_1a
            ],
            2 => vec![ // Templar
                (100000001, 1), // sword_l1_1a
                (115000001, 1), // shield
                (110300001, 1),
                (110700001, 1),
                (111100001, 1),
                (111500001, 1),
            ],
            3 | 4 => vec![ // Scout / Assassin
                (100200001, 1), // dagger_l1_1a
                (110300001, 1),
                (110700001, 1),
                (111100001, 1),
                (111500001, 1),
            ],
            5 => vec![ // Ranger
                (101300001, 1), // bow_l1_1a
                (110300001, 1),
                (110700001, 1),
                (111100001, 1),
                (111500001, 1),
            ],
            6 | 7 | 8 => vec![ // Mage / Sorcerer / Spiritmaster
                (100500001, 1), // staff_l1_1a
                (110100001, 1), // cl_torso
                (110500001, 1), // cl_pants
                (110900001, 1), // cl_feet
                (111300001, 1), // cl_hands
            ],
            9 | 10 | 11 => vec![ // Priest / Cleric / Chanter
                (100100001, 1), // mace_l1_1a
                (110100001, 1),
                (110500001, 1),
                (110900001, 1),
                (111300001, 1),
            ],
            _ => vec![
                (100000001, 1),
                (110300001, 1),
                (110700001, 1),
                (111100001, 1),
                (111500001, 1),
            ],
        }
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

        for (posicao, (item_id, quantidade)) in itens.iter().enumerate() {
            conn.execute(
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

        conn.execute(
            "UPDATE characters SET kit_inicial = 1 WHERE id = ?1",
            params![character_id as i64],
        )?;
        Ok(true)
    }

    /// Consulta todos os itens da bolsa do personagem
    pub fn itens_do_personagem(conn: &Connection, character_id: u32) -> Result<Vec<ItemPersistido>> {
        let mut stmt = conn.prepare(
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

    /// Adiciona item ou empilha no inventário persistido
    pub fn adicionar_item(
        conn: &Connection,
        character_id: u32,
        item_id: u32,
        quantidade: u64,
        posicao: u16,
    ) -> Result<u32> {
        let existente: Option<(i64, i64)> = conn
            .query_row(
                "SELECT id, quantidade FROM character_items WHERE character_id = ?1 AND item_id = ?2 AND posicao = ?3",
                params![character_id as i64, item_id as i64, posicao as i64],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .optional()?;

        if let Some((row_id, qtd_atual)) = existente {
            let nova_qtd = qtd_atual + quantidade as i64;
            conn.execute(
                "UPDATE character_items SET quantidade = ?1 WHERE id = ?2",
                params![nova_qtd, row_id],
            )?;
            Ok(OBJ_ID_BASE | (row_id as u32 & !OBJ_ID_BASE))
        } else {
            conn.execute(
                "INSERT INTO character_items (character_id, item_id, quantidade, posicao) VALUES (?1, ?2, ?3, ?4)",
                params![character_id as i64, item_id as i64, quantidade as i64, posicao as i64],
            )?;
            let row_id = conn.last_insert_rowid();
            Ok(OBJ_ID_BASE | (row_id as u32 & !OBJ_ID_BASE))
        }
    }

    /// Remove item do inventário do personagem
    pub fn remover_item(conn: &Connection, character_id: u32, item_id: u32, quantidade: u64) -> Result<bool> {
        let mut restante = quantidade as i64;
        let mut stmt = conn.prepare(
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
                conn.execute("DELETE FROM character_items WHERE id = ?1", params![row_id])?;
                restante -= qtd;
            } else {
                conn.execute("UPDATE character_items SET quantidade = ?1 WHERE id = ?2", params![qtd - restante, row_id])?;
                restante = 0;
            }
        }

        Ok(restante == 0)
    }

    /// Consulta saldo de Kinah
    pub fn obter_kinah(conn: &Connection, character_id: u32) -> Result<u64> {
        let total: i64 = conn
            .query_row(
                "SELECT COALESCE(SUM(quantidade), 0) FROM character_items WHERE character_id = ?1 AND item_id = ?2",
                params![character_id as i64, KINAH_ITEM_ID as i64],
                |row| row.get(0),
            )?;
        Ok(total.max(0) as u64)
    }

    /// Altera o saldo de Kinah (positivo = ganho, negativo = gasto)
    pub fn alterar_kinah(conn: &Connection, character_id: u32, delta: i64) -> Result<bool> {
        let saldo_atual = Self::obter_kinah(conn, character_id)? as i64;
        if saldo_atual + delta < 0 {
            return Ok(false);
        }
        if delta > 0 {
            Self::adicionar_item(conn, character_id, KINAH_ITEM_ID, delta as u64, 0)?;
        } else if delta < 0 {
            Self::remover_item(conn, character_id, KINAH_ITEM_ID, (-delta) as u64)?;
        }
        Ok(true)
    }

    /// Transferência atômica segura de itens entre personagens (prevenção contra duplicação)
    pub fn transferir_item_entre_personagens(
        conn: &mut Connection,
        remetente_id: u32,
        destinatario_id: u32,
        item_id: u32,
        quantidade: u32,
    ) -> Result<bool> {
        let tx = conn.transaction()?;

        let qtd_remetente: Option<i64> = tx
            .query_row(
                "SELECT quantidade FROM character_items WHERE character_id = ?1 AND item_id = ?2",
                params![remetente_id as i64, item_id as i64],
                |r| r.get(0),
            )
            .optional()?;

        let Some(qtd_atual) = qtd_remetente else {
            return Ok(false);
        };

        if (qtd_atual as u32) < quantidade {
            return Ok(false);
        }

        if qtd_atual as u32 == quantidade {
            tx.execute(
                "DELETE FROM character_items WHERE character_id = ?1 AND item_id = ?2",
                params![remetente_id as i64, item_id as i64],
            )?;
        } else {
            tx.execute(
                "UPDATE character_items SET quantidade = quantidade - ?1 WHERE character_id = ?2 AND item_id = ?3",
                params![quantidade as i64, remetente_id as i64, item_id as i64],
            )?;
        }

        tx.execute(
            "INSERT INTO character_items (character_id, item_id, quantidade, posicao)
             VALUES (?1, ?2, ?3, 0)",
            params![destinatario_id as i64, item_id as i64, quantidade as i64],
        )?;

        tx.commit()?;
        Ok(true)
    }
}
