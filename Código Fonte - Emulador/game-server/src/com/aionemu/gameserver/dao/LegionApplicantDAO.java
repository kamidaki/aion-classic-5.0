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
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.team.legion.LegionApplicant;

/**
 * Candidaturas a Legion ({@code legion_applicant}, uma por personagem, como o S 0x151 mostra) e a busca de Legion por raça.
 */
public final class LegionApplicantDAO {

	private static final Logger log = LoggerFactory.getLogger(LegionApplicantDAO.class);

	public static final String CREATE_TABLE = "CREATE TABLE IF NOT EXISTS `legion_applicant` (" +
		"  `player_id` INT NOT NULL," +
		"  `legion_id` INT NOT NULL," +
		"  `name` VARCHAR(50) NOT NULL," +
		"  `player_class` TINYINT NOT NULL," +
		"  `gender` TINYINT NOT NULL," +
		"  `level` TINYINT NOT NULL," +
		"  `intro` VARCHAR(64) NOT NULL DEFAULT ''," +
		"  `apply_time` INT NOT NULL," +
		"  `refused` TINYINT NOT NULL DEFAULT 0," +
		"  PRIMARY KEY (`player_id`)," +
		"  KEY `legion_id` (`legion_id`)," +
		"  CONSTRAINT `legion_applicant_player_fk` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE," +
		"  CONSTRAINT `legion_applicant_legion_fk` FOREIGN KEY (`legion_id`) REFERENCES `legions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	private static final String COLUMNS = "player_id, legion_id, name, player_class, gender, level, intro, apply_time, refused";
	private static final String LOAD_BY_PLAYER = "SELECT " + COLUMNS + " FROM legion_applicant WHERE player_id=?";
	private static final String LOAD_BY_LEGION = "SELECT " + COLUMNS + " FROM legion_applicant WHERE legion_id=? AND refused=0 ORDER BY apply_time";
	private static final String STORE = "REPLACE INTO legion_applicant (" + COLUMNS + ") VALUES (?,?,?,?,?,?,?,?,?)";
	private static final String REFUSE = "UPDATE legion_applicant SET refused=1 WHERE player_id=? AND legion_id=?";
	private static final String DELETE = "DELETE FROM legion_applicant WHERE player_id=?";
	private static final String SEARCH = "SELECT l.id FROM legions l JOIN legion_members m ON m.legion_id=l.id AND m.`rank`='BRIGADE_GENERAL'"
		+ " JOIN players p ON p.id=m.player_id WHERE p.race=? AND l.disband_time=0 AND (? IS NULL OR l.name LIKE ?)"
		+ " ORDER BY l.contribution_points DESC, l.id LIMIT ?";

	private LegionApplicantDAO() {
	}

	public static LegionApplicant loadByPlayer(int playerId) {
		List<LegionApplicant> applicants = load(LOAD_BY_PLAYER, playerId);
		return applicants.isEmpty() ? null : applicants.getFirst();
	}

	public static List<LegionApplicant> loadByLegion(int legionId) {
		return load(LOAD_BY_LEGION, legionId);
	}

	private static List<LegionApplicant> load(String query, int id) {
		List<LegionApplicant> applicants = new ArrayList<>();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(query)) {
			stmt.setInt(1, id);
			try (ResultSet rs = stmt.executeQuery()) {
				while (rs.next())
					applicants.add(new LegionApplicant(rs.getInt(1), rs.getInt(2), rs.getString(3), rs.getInt(4), rs.getInt(5), rs.getInt(6),
						rs.getString(7), rs.getInt(8), rs.getBoolean(9)));
			}
		} catch (SQLException e) {
			log.error("Could not load legion applicants (" + id + ")", e);
		}
		return applicants;
	}

	public static boolean store(LegionApplicant applicant) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(STORE)) {
			stmt.setInt(1, applicant.playerId());
			stmt.setInt(2, applicant.legionId());
			stmt.setString(3, applicant.name());
			stmt.setInt(4, applicant.playerClass());
			stmt.setInt(5, applicant.gender());
			stmt.setInt(6, applicant.level());
			stmt.setString(7, applicant.intro());
			stmt.setInt(8, applicant.applyTime());
			stmt.setBoolean(9, applicant.refused());
			stmt.executeUpdate();
			return true;
		} catch (SQLException e) {
			log.error("Could not store legion applicant " + applicant.playerId(), e);
			return false;
		}
	}

	public static void refuse(int playerId, int legionId) {
		update(REFUSE, playerId, legionId);
	}

	public static void delete(int playerId) {
		update(DELETE, playerId, null);
	}

	private static void update(String query, int playerId, Integer legionId) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(query)) {
			stmt.setInt(1, playerId);
			if (legionId != null)
				stmt.setInt(2, legionId);
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Could not update legion applicant " + playerId, e);
		}
	}

	/**
	 * @param name
	 *          parte do nome, ou null para todas
	 * @return ids das Legions da raça, pela contribuição
	 */
	public static List<Integer> search(Race race, String name, int limit) {
		List<Integer> ids = new ArrayList<>();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(SEARCH)) {
			stmt.setString(1, race.name());
			stmt.setString(2, name);
			stmt.setString(3, name == null ? null : "%" + name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%");
			stmt.setInt(4, limit);
			try (ResultSet rs = stmt.executeQuery()) {
				while (rs.next())
					ids.add(rs.getInt(1));
			}
		} catch (SQLException e) {
			log.error("Could not search legions", e);
		}
		return ids;
	}
}
