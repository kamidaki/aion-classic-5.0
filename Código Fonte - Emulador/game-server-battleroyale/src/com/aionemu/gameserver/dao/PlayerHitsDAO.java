package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;

public class PlayerHitsDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerHitsDAO.class);

	public static final String SELECT_QUERY =
		"SELECT cumulative_reward, better_amount_hits, daily_hits, weekly_hits, monthly_hits, year_hits, total_hits " +
		"FROM player_hits WHERE account_id = ? AND player_id = ?";

	public static final String INSERT_OR_UPDATE_QUERY =
		"INSERT INTO player_hits (account_id, player_id, cumulative_reward, better_amount_hits, daily_hits, weekly_hits, monthly_hits, year_hits, total_hits) " +
		"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) " +
		"ON DUPLICATE KEY UPDATE " +
		"cumulative_reward = cumulative_reward + ?, " +
		"daily_hits = daily_hits + ?, " +
		"weekly_hits = weekly_hits + ?, " +
		"monthly_hits = monthly_hits + ?, " +
		"year_hits = year_hits + ?, " +
		"total_hits = total_hits + ?, " +
		"better_amount_hits = GREATEST(better_amount_hits, ?)";

	private static final String SELECT_AFTER_UPSERT =
		"SELECT cumulative_reward, better_amount_hits FROM player_hits WHERE account_id = ? AND player_id = ? FOR UPDATE";

	private static final String DECREMENT_QUERY =
		"UPDATE player_hits SET cumulative_reward = GREATEST(0, cumulative_reward - ?) WHERE account_id = ? AND player_id = ?";

	static {
		initTable();
	}

	public static void initTable() {
		String sql = "CREATE TABLE IF NOT EXISTS `player_hits` (" +
			"`account_id` int(11) NOT NULL," +
			"`player_id` int(11) NOT NULL," +
			"`cumulative_reward` int(11) NOT NULL DEFAULT '0'," +
			"`better_amount_hits` int(11) NOT NULL DEFAULT '0'," +
			"`daily_hits` int(11) NOT NULL DEFAULT '0'," +
			"`weekly_hits` int(11) NOT NULL DEFAULT '0'," +
			"`monthly_hits` int(11) NOT NULL DEFAULT '0'," +
			"`year_hits` int(11) NOT NULL DEFAULT '0'," +
			"`total_hits` int(11) NOT NULL DEFAULT '0'," +
			"PRIMARY KEY (`account_id`, `player_id`)" +
			") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
		try (Connection con = DatabaseFactory.getConnection();
			 Statement stmt = con.createStatement()) {
			stmt.executeUpdate(sql);
		} catch (SQLException e) {
			log.error("Erro ao inicializar tabela player_hits", e);
		}
	}

	public static int[] getPlayerHits(int accountId, int playerId) {
		int[] hitsData = new int[7];
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(SELECT_QUERY)) {
			stmt.setInt(1, accountId);
			stmt.setInt(2, playerId);
			try (ResultSet rset = stmt.executeQuery()) {
				if (rset.next()) {
					hitsData[0] = rset.getInt("cumulative_reward");
					hitsData[1] = rset.getInt("better_amount_hits");
					hitsData[2] = rset.getInt("daily_hits");
					hitsData[3] = rset.getInt("weekly_hits");
					hitsData[4] = rset.getInt("monthly_hits");
					hitsData[5] = rset.getInt("year_hits");
					hitsData[6] = rset.getInt("total_hits");
				}
			}
		} catch (SQLException e) {
			log.error("Erro ao buscar hits para player={}", playerId, e);
		}
		return hitsData;
	}

	public static void addHits(int accountId, int playerId, int newHits, int maxComboThisFight) {
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(INSERT_OR_UPDATE_QUERY)) {
			stmt.setInt(1, accountId);
			stmt.setInt(2, playerId);
			stmt.setInt(3, newHits);
			stmt.setInt(4, maxComboThisFight);
			stmt.setInt(5, newHits);
			stmt.setInt(6, newHits);
			stmt.setInt(7, newHits);
			stmt.setInt(8, newHits);
			stmt.setInt(9, newHits);
			stmt.setInt(10, newHits); // cumulative_reward
			stmt.setInt(11, newHits); // daily
			stmt.setInt(12, newHits); // weekly
			stmt.setInt(13, newHits); // monthly
			stmt.setInt(14, newHits); // year
			stmt.setInt(15, newHits); // total
			stmt.setInt(16, maxComboThisFight); // better_amount_hits GREATEST
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Erro ao adicionar hits para player={}", playerId, e);
		}
	}

	public static HitRewardResult addHitsAndClaimRewards(int accountId, int playerId, int newHits, int maxComboThisFight) {
		try (Connection con = DatabaseFactory.getConnection()) {
			con.setAutoCommit(false);
			try {
				try (PreparedStatement stmt = con.prepareStatement(INSERT_OR_UPDATE_QUERY)) {
					stmt.setInt(1, accountId);
					stmt.setInt(2, playerId);
					stmt.setInt(3, newHits);
					stmt.setInt(4, maxComboThisFight);
					stmt.setInt(5, newHits);
					stmt.setInt(6, newHits);
					stmt.setInt(7, newHits);
					stmt.setInt(8, newHits);
					stmt.setInt(9, newHits);
					stmt.setInt(10, newHits);
					stmt.setInt(11, newHits);
					stmt.setInt(12, newHits);
					stmt.setInt(13, newHits);
					stmt.setInt(14, newHits);
					stmt.setInt(15, newHits);
					stmt.setInt(16, maxComboThisFight);
					stmt.executeUpdate();
				}

				int cumulativeReward;
				int betterAmountHits;
				try (PreparedStatement stmt = con.prepareStatement(SELECT_AFTER_UPSERT)) {
					stmt.setInt(1, accountId);
					stmt.setInt(2, playerId);
					try (ResultSet rs = stmt.executeQuery()) {
						if (!rs.next()) {
							throw new SQLException("player_hits row missing after UPSERT for player " + playerId);
						}
						cumulativeReward = rs.getInt("cumulative_reward");
						betterAmountHits = rs.getInt("better_amount_hits");
					}
				}

				int pointsEarned = cumulativeReward / 1000;
				if (pointsEarned > 0) {
					try (PreparedStatement stmt = con.prepareStatement(DECREMENT_QUERY)) {
						stmt.setInt(1, pointsEarned * 1000);
						stmt.setInt(2, accountId);
						stmt.setInt(3, playerId);
						stmt.executeUpdate();
					}
				}
				con.commit();
				return new HitRewardResult(pointsEarned, betterAmountHits);
			} catch (SQLException e) {
				try {
					con.rollback();
				} catch (SQLException rollbackError) {
					e.addSuppressed(rollbackError);
				}
				throw e;
			}
		} catch (SQLException e) {
			log.error("Erro em addHitsAndClaimRewards para player={}", playerId, e);
			return new HitRewardResult(0, 0);
		}
	}

	public record HitRewardResult(int pointsEarned, int betterAmountHits) {}

	public static void decrementCumulativeHits(int accountId, int playerId, int amountToDeduct) {
		try (Connection con = DatabaseFactory.getConnection();
			 PreparedStatement stmt = con.prepareStatement(DECREMENT_QUERY)) {
			stmt.setInt(1, amountToDeduct);
			stmt.setInt(2, accountId);
			stmt.setInt(3, playerId);
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Erro ao decrementar cumulative hits para player={}", playerId, e);
		}
	}
}
