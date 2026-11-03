package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.BlackCloudGoods;

/**
 * Fila de mercadorias do Black Cloud Mail por conta. A linha não é apagada no resgate: {@code received_time} e {@code received_player_id}
 * ficam como histórico da entrega, e só as linhas sem {@code received_time} aparecem para o cliente.
 */
public final class BlackCloudGoodsDAO {

	private static final Logger log = LoggerFactory.getLogger(BlackCloudGoodsDAO.class);
	private static final String COLUMNS = "id, account_id, name, item_id, item_count, register_time";
	private static final String LOAD_PENDING = "SELECT " + COLUMNS
		+ " FROM account_blackcloud_goods WHERE account_id=? AND received_time IS NULL ORDER BY id DESC"; // mais nova primeiro, como na captura
	private static final String LOAD_ONE = "SELECT " + COLUMNS
		+ " FROM account_blackcloud_goods WHERE id=? AND account_id=? AND received_time IS NULL";
	private static final String COUNT_PENDING = "SELECT COUNT(*) FROM account_blackcloud_goods WHERE account_id=? AND received_time IS NULL";
	private static final String MARK_RECEIVED = "UPDATE account_blackcloud_goods SET received_player_id=?, received_time=CURRENT_TIMESTAMP"
		+ " WHERE id=? AND account_id=? AND received_time IS NULL";
	private static final String INSERT = "INSERT INTO account_blackcloud_goods (account_id, name, item_id, item_count) VALUES (?,?,?,?)";

	private BlackCloudGoodsDAO() {
	}

	public static List<BlackCloudGoods> loadPending(int accountId) {
		List<BlackCloudGoods> goods = new ArrayList<>();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_PENDING)) {
			stmt.setInt(1, accountId);
			try (ResultSet rs = stmt.executeQuery()) {
				while (rs.next())
					goods.add(read(rs));
			}
		} catch (Exception e) {
			log.error("Could not load Black Cloud goods of account " + accountId, e);
		}
		return goods;
	}

	public static BlackCloudGoods loadPending(int accountId, long goodsId) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_ONE)) {
			stmt.setLong(1, goodsId);
			stmt.setInt(2, accountId);
			try (ResultSet rs = stmt.executeQuery()) {
				return rs.next() ? read(rs) : null;
			}
		} catch (Exception e) {
			log.error("Could not load Black Cloud goods " + goodsId + " of account " + accountId, e);
			return null;
		}
	}

	public static int countPending(int accountId) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(COUNT_PENDING)) {
			stmt.setInt(1, accountId);
			try (ResultSet rs = stmt.executeQuery()) {
				return rs.next() ? rs.getInt(1) : 0;
			}
		} catch (Exception e) {
			log.error("Could not count Black Cloud goods of account " + accountId, e);
			return 0;
		}
	}

	/**
	 * @return true só para quem marcou a linha; um segundo resgate da mesma mercadoria encontra {@code received_time} preenchido e não altera nada
	 */
	public static boolean markReceived(BlackCloudGoods goods, int playerId) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(MARK_RECEIVED)) {
			stmt.setInt(1, playerId);
			stmt.setLong(2, goods.id());
			stmt.setInt(3, goods.accountId());
			return stmt.executeUpdate() == 1;
		} catch (Exception e) {
			log.error("Could not mark Black Cloud goods " + goods + " as received by player " + playerId, e);
			return false;
		}
	}

	/**
	 * @return id da nova mercadoria, ou 0 se não foi gravada
	 */
	public static long insert(int accountId, String name, int itemId, long itemCount) {
		try (Connection con = DatabaseFactory.getConnection();
			PreparedStatement stmt = con.prepareStatement(INSERT, Statement.RETURN_GENERATED_KEYS)) {
			stmt.setInt(1, accountId);
			stmt.setString(2, name);
			stmt.setInt(3, itemId);
			stmt.setLong(4, itemCount);
			stmt.executeUpdate();
			try (ResultSet keys = stmt.getGeneratedKeys()) {
				return keys.next() ? keys.getLong(1) : 0;
			}
		} catch (Exception e) {
			log.error("Could not store Black Cloud goods (" + itemId + " x" + itemCount + ") for account " + accountId, e);
			return 0;
		}
	}

	private static BlackCloudGoods read(ResultSet rs) throws java.sql.SQLException {
		return new BlackCloudGoods(rs.getLong("id"), rs.getInt("account_id"), rs.getString("name"), rs.getInt("item_id"), rs.getLong("item_count"),
			(int) (rs.getTimestamp("register_time").getTime() / 1000));
	}
}
