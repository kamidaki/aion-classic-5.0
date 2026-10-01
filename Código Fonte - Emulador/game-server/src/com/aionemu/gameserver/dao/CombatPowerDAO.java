package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;

/**
 * Persistência e consulta do Combat Power (Combat Talent) de todos os jogadores (online e offline).
 */
public final class CombatPowerDAO {

	private static final Logger log = LoggerFactory.getLogger(CombatPowerDAO.class);
	private static volatile boolean tableChecked = false;

	public record PlayerCombatPowerEntry(
		int playerId,
		String name,
		Race race,
		PlayerClass playerClass,
		int combatPower,
		int oldRank
	) {}

	private static void ensureTable(Connection con) {
		if (!tableChecked) {
			try (var s = con.createStatement()) {
				s.executeUpdate("CREATE TABLE IF NOT EXISTS `player_combat_power` (" +
					"  `player_id` INT NOT NULL," +
					"  `combat_power` INT NOT NULL DEFAULT 0," +
					"  `last_update` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP," +
					"  PRIMARY KEY (`player_id`)," +
					"  CONSTRAINT `player_combat_power_player_fk` FOREIGN KEY (`player_id`)" +
					"    REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
					") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;");
				tableChecked = true;
			} catch (Exception e) {
				log.warn("Could not ensure player_combat_power table: " + e.getMessage());
			}
		}
	}

	private CombatPowerDAO() {
	}

	public static void storeCombatPower(int playerId, int combatPower) {
		if (playerId <= 0)
			return;
		String query = "INSERT INTO player_combat_power (player_id, combat_power) VALUES (?, ?) " +
			"ON DUPLICATE KEY UPDATE combat_power = VALUES(combat_power)";
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTable(con);
			try (PreparedStatement stmt = con.prepareStatement(query)) {
				stmt.setInt(1, playerId);
				stmt.setInt(2, combatPower);
				stmt.executeUpdate();
			}
		} catch (SQLException e) {
			log.error("Could not store combat power for player " + playerId, e);
		}
	}

	public static List<PlayerCombatPowerEntry> loadAllCandidates() {
		List<PlayerCombatPowerEntry> list = new ArrayList<>();
		String query = "SELECT p.id, p.name, p.race, p.player_class, " +
			"COALESCE(cp.combat_power, 0) AS combat_power, " +
			"COALESCE(a.old_rank_pos, 0) AS old_rank " +
			"FROM players p " +
			"LEFT JOIN player_combat_power cp ON p.id = cp.player_id " +
			"LEFT JOIN abyss_rank a ON p.id = a.player_id " +
			"WHERE p.exp > 0";
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTable(con);
			try (PreparedStatement stmt = con.prepareStatement(query);
				 ResultSet rs = stmt.executeQuery()) {
				while (rs.next()) {
					int id = rs.getInt("id");
					String name = rs.getString("name");
					Race race = Race.valueOf(rs.getString("race"));
					PlayerClass pClass = PlayerClass.valueOf(rs.getString("player_class"));
					int cp = rs.getInt("combat_power");
					int oldRank = rs.getInt("old_rank");
					list.add(new PlayerCombatPowerEntry(id, name, race, pClass, cp, oldRank));
				}
			}
		} catch (SQLException e) {
			log.error("Could not load all candidates for combat power ranking", e);
		}
		return list;
	}
}
