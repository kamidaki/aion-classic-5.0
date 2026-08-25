use rusqlite::{params, Connection, Result};

pub struct BrokerDao;

impl BrokerDao {
    pub fn salvar_anuncio_broker(
        conn: &Connection,
        seller_id: u32,
        seller_name: &str,
        item_template_id: u32,
        quantity: u32,
        price_per_unit: u64,
        expiry_ts: u64,
        quality: u8,
        enhance_level: u8,
    ) -> Result<u32> {
        conn.execute(
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
        Ok(conn.last_insert_rowid() as u32)
    }

    pub fn listar_anuncios_broker(
        conn: &Connection,
        page: u32,
        page_size: u8,
    ) -> Result<(u32, Vec<crate::message::server::GlobalTradeListingEntry>)> {
        let total: i64 = conn.query_row(
            "SELECT COUNT(*) FROM broker_listings WHERE is_sold = 0",
            [],
            |r| r.get(0),
        )?;

        let offset = (page as i64) * (page_size as i64);
        let mut stmt = conn.prepare(
            "SELECT id, item_template_id, quantity, price_per_unit, seller_name, expiry_ts, quality, enhance_level
             FROM broker_listings
             WHERE is_sold = 0
             ORDER BY id DESC
             LIMIT ?1 OFFSET ?2",
        )?;
        let rows = stmt.query_map(params![page_size as i64, offset], |row| {
            Ok(crate::message::server::GlobalTradeListingEntry {
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

    pub fn comprar_anuncio_broker(conn: &Connection, listing_id: u32) -> Result<Option<(u32, String, u32, u32, u64)>> {
        let mut stmt = conn.prepare(
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
            conn.execute("UPDATE broker_listings SET is_sold = 1 WHERE id = ?1", params![listing_id as i64])?;
            Ok(Some(res))
        } else {
            Ok(None)
        }
    }

    pub fn salvar_historico_broker(
        conn: &Connection,
        player_id: u32,
        item_template_id: u32,
        quantity: u32,
        price: u64,
        timestamp: u64,
        trade_type: u8,
    ) -> Result<()> {
        conn.execute(
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
        conn: &Connection,
        item_template_id: u32,
        quality: u8,
    ) -> Result<Vec<crate::message::server::GlobalTradeSaleslogEntry>> {
        let mut stmt = conn.prepare(
            "SELECT item_template_id, quantity, price, timestamp
             FROM broker_history
             WHERE item_template_id = ?1
             ORDER BY timestamp DESC
             LIMIT 50",
        )?;
        let rows = stmt.query_map(params![item_template_id as i64], |row| {
            Ok(crate::message::server::GlobalTradeSaleslogEntry {
                item_template_id: row.get::<_, i64>(0)? as u32,
                quantity: row.get::<_, i64>(1)? as u32,
                price: row.get::<_, i64>(2)? as u64,
                timestamp: row.get::<_, i64>(3)? as u64,
                quality,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn preco_medio_item(conn: &Connection, item_template_id: u32) -> Result<u64> {
        let avg: Option<f64> = conn.query_row(
            "SELECT AVG(price) FROM broker_history WHERE item_template_id = ?1",
            params![item_template_id as i64],
            |r| r.get(0),
        )?;
        Ok(avg.unwrap_or(0.0) as u64)
    }
}
