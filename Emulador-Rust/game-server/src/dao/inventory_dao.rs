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
    /// Kit inicial oficial de 21 equipamentos e consumíveis da 4.5 Classic por classe
    pub fn kit_for_class(class_id: u32) -> Vec<(u32, u32)> {
        match class_id {
            0 | 1 => vec![ // Warrior / Gladiator (Battlemaster)
                (182400001, 0),
                (182500000, 0),
                (101301127, 1),
                (110301466, 1),
                (113301417, 1),
                (112301344, 1),
                (111301396, 1),
                (114301456, 1),
                (125003453, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            2 => vec![ // Templar (Knight)
                (182400001, 0),
                (182500000, 0),
                (100001519, 1),
                (115001470, 1),
                (110601374, 1),
                (113601332, 1),
                (112601323, 1),
                (111601344, 1),
                (114601333, 1),
                (125003443, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            3 | 4 => vec![ // Scout / Assassin
                (182400001, 0),
                (182500000, 0),
                (100201355, 1),
                (100001520, 1),
                (110301463, 1),
                (113301414, 1),
                (112301341, 1),
                (111301393, 1),
                (114301453, 1),
                (125003447, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            5 => vec![ // Ranger
                (182400001, 0),
                (182500000, 0),
                (101701219, 1),
                (101701219, 1),
                (110301464, 1),
                (113301415, 1),
                (112301342, 1),
                (111301394, 1),
                (114301454, 1),
                (125003448, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            6 | 7 => vec![ // Mage / Sorcerer (Wizard)
                (182400001, 0),
                (182500000, 0),
                (100501181, 1),
                (110101547, 1),
                (113101433, 1),
                (112101374, 1),
                (111101415, 1),
                (114101463, 1),
                (125003449, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            8 => vec![ // Spiritmaster (Elementallist)
                (182400001, 0),
                (182500000, 0),
                (100601234, 1),
                (110101548, 1),
                (113101434, 1),
                (112101375, 1),
                (111101416, 1),
                (114101464, 1),
                (125003450, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            9 | 10 => vec![ // Priest / Cleric
                (182400001, 0),
                (182500000, 0),
                (100101171, 1),
                (115001470, 1),
                (110551028, 1),
                (113501388, 1),
                (112501318, 1),
                (111501369, 1),
                (114501393, 1),
                (125003446, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            11 => vec![ // Chanter
                (182400001, 0),
                (182500000, 0),
                (101501210, 1),
                (110551027, 1),
                (113501387, 1),
                (112501317, 1),
                (111501368, 1),
                (114501392, 1),
                (125003445, 1),
                (121001324, 1),
                (120015074, 1),
                (122001596, 1),
                (123001243, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
            ],
            _ => vec![ // Monk / Brawler / Revenant / Outros
                (182400001, 0),
                (182500000, 0),
                (102400013, 1),
                (110301338, 1),
                (111301283, 1),
                (113301306, 1),
                (114301341, 1),
                (164000221, 10),
                (164000224, 10),
                (164000227, 10),
                (164000259, 10),
                (160003577, 10),
                (160003578, 10),
                (169300007, 30),
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
