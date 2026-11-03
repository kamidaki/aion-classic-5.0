package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.world.World;
import com.lostacademy.Dps_Meter.DpsService;

public class ParticipationPointsDAO {

	private static final Logger log = LoggerFactory.getLogger(ParticipationPointsDAO.class);

	private static final ConcurrentHashMap<Integer, Long> pointsCache = new ConcurrentHashMap<>();

	public static final String SELECT_QUERY =
		"SELECT points FROM player_participation_points WHERE account_id = ?";

	public static final String INSERT_OR_UPDATE_QUERY =
		"INSERT INTO player_participation_points (account_id, points, last_update) VALUES (?, GREATEST(0, ?), ?) " +
		"ON DUPLICATE KEY UPDATE points = GREATEST(0, CAST(points AS SIGNED) + ?), last_update = ?";

	public static final String CLEAR_QUERY =
		"UPDATE player_participation_points SET points = 0 WHERE account_id = ?";

	private static final String TRY_DEBIT_QUERY =
		"UPDATE player_participation_points SET points = points - ?, last_update = ? WHERE account_id = ? AND points >= ?";

	static {
		initTable();
	}

	public static void initTable() {
		String sql = "CREATE TABLE IF NOT EXISTS `player_participation_points` (" +
			"`account_id` int(11) NOT NULL," +
			"`points` bigint(20) NOT NULL DEFAULT '0'," +
			"`last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP," +
			"PRIMARY KEY (`account_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
		try (Connection con = DatabaseFactory.getConnection();
			 Statement stmt = con.createStatement()) {
			stmt.executeUpdate(sql);
		} catch (SQLException e) {
			log.error("Erro ao inicializar tabela player_participation_points", e);
		}
	}

	private static Player findOnlinePlayerByAccount(int accountId) {
		for (Player p : World.getInstance().getAllPlayers()) {
			if (p.getAccount() != null && p.getAccount().getId() == accountId) {
				return p;
			}
		}
		return null;
	}

	private static void notifyAndLog(Player player, long delta, String source) {
		if (player == null) return;
		DpsService.getInstance().sendParticipationNotification(player, delta, getPoints(player.getAccount().getId()));
	}

	public static long getPoints(int accountId) {
		Long cached = pointsCache.get(accountId);
		if (cached != null) {
			return cached;
		}
		long points = 0;
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(SELECT_QUERY)) {
			stmt.setInt(1, accountId);
			try (ResultSet rset = stmt.executeQuery()) {
				if (rset.next()) {
					points = rset.getLong("points");
				}
			}
			pointsCache.put(accountId, points);
		} catch (SQLException e) {
			log.error("Erro ao buscar pontos de participacao para account_id={}", accountId, e);
		}
		return points;
	}

	public static void addPoints(int accountId, long pointsToAdd) {
		tryAddPoints(accountId, pointsToAdd);
	}

	public static boolean tryAddPoints(int accountId, long pointsToAdd) {
		if (accountId <= 0 || pointsToAdd == 0)
			return false;
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(INSERT_OR_UPDATE_QUERY)) {
			Timestamp now = new Timestamp(System.currentTimeMillis());
			stmt.setInt(1, accountId);
			stmt.setLong(2, pointsToAdd);
			stmt.setTimestamp(3, now);
			stmt.setLong(4, pointsToAdd);
			stmt.setTimestamp(5, now);
			stmt.executeUpdate();
			pointsCache.compute(accountId, (k, v) -> v == null ? null : Math.max(0L, v + pointsToAdd));
			notifyAndLog(findOnlinePlayerByAccount(accountId), pointsToAdd, "participation_points");
			return true;
		} catch (SQLException e) {
			log.error("Erro ao adicionar pontos de participacao para account_id={}", accountId, e);
			return false;
		}
	}

	public static boolean addPointsBatch(Map<Integer, Long> pointsByAccount) {
		if (pointsByAccount == null || pointsByAccount.isEmpty()) {
			return true;
		}
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(INSERT_OR_UPDATE_QUERY)) {
			Timestamp now = new Timestamp(System.currentTimeMillis());
			int batched = 0;
			for (Map.Entry<Integer, Long> entry : pointsByAccount.entrySet()) {
				int accountId = entry.getKey() == null ? 0 : entry.getKey();
				long delta = entry.getValue() == null ? 0 : entry.getValue();
				if (accountId <= 0 || delta == 0) {
					continue;
				}
				stmt.setInt(1, accountId);
				stmt.setLong(2, delta);
				stmt.setTimestamp(3, now);
				stmt.setLong(4, delta);
				stmt.setTimestamp(5, now);
				stmt.addBatch();
				batched++;
			}
			if (batched == 0) {
				return true;
			}
			stmt.executeBatch();
			for (Map.Entry<Integer, Long> entry : pointsByAccount.entrySet()) {
				if (entry.getKey() != null && entry.getKey() > 0 && entry.getValue() != null && entry.getValue() != 0) {
					int accId = entry.getKey();
					long d = entry.getValue();
					pointsCache.compute(accId, (k, v) -> v == null ? null : Math.max(0L, v + d));
					notifyAndLog(findOnlinePlayerByAccount(accId), d, "participation_points_batch");
				}
			}
			return true;
		} catch (SQLException e) {
			log.error("Erro ao adicionar lote de pontos de participacao para {} contas", pointsByAccount.size(), e);
			return false;
		}
	}

	public static boolean tryDebitPoints(int accountId, long pointsToDebit) {
		if (accountId <= 0 || pointsToDebit <= 0)
			return false;
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(TRY_DEBIT_QUERY)) {
			stmt.setLong(1, pointsToDebit);
			stmt.setTimestamp(2, new Timestamp(System.currentTimeMillis()));
			stmt.setInt(3, accountId);
			stmt.setLong(4, pointsToDebit);
			boolean debited = stmt.executeUpdate() == 1;
			if (debited) {
				pointsCache.compute(accountId, (k, v) -> v == null ? null : Math.max(0L, v - pointsToDebit));
				notifyAndLog(findOnlinePlayerByAccount(accountId), -pointsToDebit, "participation_points");
			}
			return debited;
		} catch (SQLException e) {
			log.error("Erro ao debitar pontos de participacao para account_id={}", accountId, e);
			return false;
		}
	}

	public static void clearPoints(int accountId) {
		long before = getPoints(accountId);
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(CLEAR_QUERY)) {
			stmt.setInt(1, accountId);
			stmt.executeUpdate();
			pointsCache.put(accountId, 0L);
			notifyAndLog(findOnlinePlayerByAccount(accountId), -before, "participation_clear");
		} catch (SQLException e) {
			log.error("Erro ao limpar pontos de participacao para account_id={}", accountId, e);
		}
	}
}
