package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.sql.Types;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeCurrency;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing;
import com.aionemu.gameserver.model.globaltrade.GlobalTradeListing.State;

/**
 * Anúncios da Global Auction House (tabela global_trade_listings, criada pelo DatabaseSchemaService). O item anunciado fica no inventory
 * com item_location 125; a linha do anúncio guarda o item_unique_id dele.
 */
public final class GlobalTradeDAO {

	private static final Logger log = LoggerFactory.getLogger(GlobalTradeDAO.class);
	private static final String LOAD = "SELECT * FROM global_trade_listings WHERE state IN ('LISTED','SOLD') OR (state='COLLECTED' AND collected_time >= ?)";
	private static final String INSERT = "INSERT INTO global_trade_listings (seller_id, item_unique_id, item_id, item_count, price, currency, category,"
		+ " register_fee, register_time, expire_time, state) VALUES (?,?,?,?,?,?,?,?,?,?,'LISTED')";
	private static final String UPDATE = "UPDATE global_trade_listings SET state=?, buyer_id=?, sold_time=?, sale_fee=?, collected_time=?, item_count=?, price=? WHERE id=?";

	private GlobalTradeDAO() {
	}

	/**
	 * @return anúncios à venda, vendidos sem receita recebida e recebidos a partir de {@code collectedSince} (histórico de vendas)
	 */
	public static List<GlobalTradeListing> load(long collectedSince) {
		List<GlobalTradeListing> listings = new ArrayList<>();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD)) {
			stmt.setTimestamp(1, new Timestamp(collectedSince));
			try (ResultSet rs = stmt.executeQuery()) {
				while (rs.next()) {
					GlobalTradeCurrency currency = GlobalTradeCurrency.of(rs.getInt("currency"));
					if (currency == null) {
						log.warn("Global trade listing {} with unknown currency {}", rs.getLong("id"), rs.getInt("currency"));
						continue;
					}
					listings.add(new GlobalTradeListing(rs.getLong("id"), rs.getInt("seller_id"), rs.getInt("item_unique_id"), rs.getInt("item_id"),
						rs.getLong("item_count"), rs.getLong("price"), currency, rs.getInt("category"), rs.getLong("register_fee"),
						millis(rs.getTimestamp("register_time")), millis(rs.getTimestamp("expire_time")), State.valueOf(rs.getString("state")),
						rs.getInt("buyer_id"), millis(rs.getTimestamp("sold_time")), rs.getLong("sale_fee"), millis(rs.getTimestamp("collected_time"))));
				}
			}
		} catch (Exception e) {
			log.error("Could not load global trade listings", e);
		}
		return listings;
	}

	/**
	 * @return id do anúncio novo, ou 0 se não foi gravado
	 */
	public static long insert(int sellerId, int itemUniqueId, int itemId, long count, long price, GlobalTradeCurrency currency, int category,
		long registerFee, long registerTime, long expireTime) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(INSERT, Statement.RETURN_GENERATED_KEYS)) {
			stmt.setInt(1, sellerId);
			stmt.setInt(2, itemUniqueId);
			stmt.setInt(3, itemId);
			stmt.setLong(4, count);
			stmt.setLong(5, price);
			stmt.setInt(6, currency.getId());
			stmt.setInt(7, category);
			stmt.setLong(8, registerFee);
			stmt.setTimestamp(9, new Timestamp(registerTime));
			stmt.setTimestamp(10, new Timestamp(expireTime));
			stmt.executeUpdate();
			try (ResultSet keys = stmt.getGeneratedKeys()) {
				return keys.next() ? keys.getLong(1) : 0;
			}
		} catch (Exception e) {
			log.error("Could not store global trade listing of player " + sellerId + " (item " + itemId + " x" + count + ")", e);
			return 0;
		}
	}

	public static boolean update(GlobalTradeListing listing) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(UPDATE)) {
			stmt.setString(1, listing.getState().name());
			if (listing.getBuyerId() != 0)
				stmt.setInt(2, listing.getBuyerId());
			else
				stmt.setNull(2, Types.INTEGER);
			setTime(stmt, 3, listing.getSoldTime());
			stmt.setLong(4, listing.getSaleFee());
			setTime(stmt, 5, listing.getCollectedTime());
			stmt.setLong(6, listing.getCount());
			stmt.setLong(7, listing.getPrice());
			stmt.setLong(8, listing.getId());
			return stmt.executeUpdate() == 1;
		} catch (Exception e) {
			log.error("Could not update " + listing, e);
			return false;
		}
	}

	private static void setTime(PreparedStatement stmt, int index, long millis) throws SQLException {
		if (millis > 0)
			stmt.setTimestamp(index, new Timestamp(millis));
		else
			stmt.setNull(index, Types.TIMESTAMP);
	}

	private static long millis(Timestamp timestamp) {
		return timestamp == null ? 0 : timestamp.getTime();
	}
}
