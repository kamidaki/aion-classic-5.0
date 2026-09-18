package com.aionemu.gameserver.dao;

import java.sql.SQLException;
import java.util.Map;
import java.util.TreeMap;
import com.aionemu.commons.database.DatabaseFactory;

/** Per-character guaranteed-craft progress. SQL errors must prevent a paid ceiling craft. */
public final class SielAnvilDAO {
	private SielAnvilDAO() { }
	public static Map<Integer, Integer> load(int playerId) throws SQLException {
		Map<Integer, Integer> points = new TreeMap<>();
		try (var con = DatabaseFactory.getConnection(); var stmt = con.prepareStatement(
			"SELECT recipe_id, points FROM player_siel_anvil WHERE player_id=?")) {
			stmt.setInt(1, playerId);
			try (var rs = stmt.executeQuery()) {
				while (rs.next()) points.put(rs.getInt(1), rs.getInt(2));
			}
		}
		return points;
	}
	public static void save(int playerId, int recipeId, int points) throws SQLException {
		try (var con = DatabaseFactory.getConnection(); var stmt = con.prepareStatement(
			"INSERT INTO player_siel_anvil (player_id,recipe_id,points) VALUES (?,?,?) ON DUPLICATE KEY UPDATE points=VALUES(points)")) {
			stmt.setInt(1, playerId); stmt.setInt(2, recipeId); stmt.setInt(3, points);
			stmt.executeUpdate();
		}
	}
}
