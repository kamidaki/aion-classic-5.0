use rusqlite::{params, Connection, Result};

pub struct MailDao;

impl MailDao {
    pub fn salvar_carta(
        conn: &Connection,
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
        conn.execute(
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
        Ok(conn.last_insert_rowid() as u32)
    }

    pub fn cartas_do_personagem(conn: &Connection, recipient_id: u32) -> Result<Vec<crate::mail::Letter>> {
        let mut stmt = conn.prepare(
            "SELECT id, sender_name, recipient_id, title, body, item_template_id, item_quantity, kinah_amount, letter_type, is_read, timestamp
             FROM character_mail WHERE recipient_id = ?1 ORDER BY id ASC",
        )?;
        let rows = stmt.query_map(params![recipient_id as i64], |row| {
            let ltype_num: u8 = row.get::<_, i64>(8)? as u8;
            let ltype = match ltype_num {
                1 => crate::mail::LetterType::Express,
                2 => crate::mail::LetterType::System,
                3 => crate::mail::LetterType::Blackcloud,
                _ => crate::mail::LetterType::Regular,
            };
            Ok(crate::mail::Letter {
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

    pub fn marcar_carta_lida(conn: &Connection, letter_id: u32) -> Result<bool> {
        let n = conn.execute(
            "UPDATE character_mail SET is_read = 1 WHERE id = ?1",
            params![letter_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn deletar_carta(conn: &Connection, letter_id: u32) -> Result<bool> {
        let n = conn.execute(
            "DELETE FROM character_mail WHERE id = ?1 AND kinah_amount = 0 AND item_template_id = 0",
            params![letter_id as i64],
        )?;
        Ok(n > 0)
    }

    pub fn extrair_anexos_carta(conn: &Connection, letter_id: u32) -> Result<bool> {
        let n = conn.execute(
            "UPDATE character_mail SET kinah_amount = 0, item_template_id = 0, item_quantity = 0 WHERE id = ?1",
            params![letter_id as i64],
        )?;
        Ok(n > 0)
    }
}
