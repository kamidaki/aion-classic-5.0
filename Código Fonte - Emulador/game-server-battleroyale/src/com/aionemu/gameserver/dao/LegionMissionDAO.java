package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.team.legion.LegionMissionProgress;

/**
 * Missões da Legion ({@code legion_mission}, uma linha por dono e missão) e crescimento da Legion ({@code legion_growth}).
 */
public final class LegionMissionDAO {

	private static final Logger log = LoggerFactory.getLogger(LegionMissionDAO.class);

	public static final String CREATE_MISSION_TABLE = "CREATE TABLE IF NOT EXISTS `legion_mission` (" +
		"  `owner_type` TINYINT NOT NULL," +
		"  `owner_id` INT NOT NULL," +
		"  `mission_id` INT NOT NULL," +
		"  `instance_id` BIGINT NOT NULL," +
		"  `last_instance_id` BIGINT NOT NULL," +
		"  `period_start` BIGINT NOT NULL," +
		"  `last_update` BIGINT NOT NULL," +
		"  `rewarded_stages` INT NOT NULL DEFAULT 0," +
		"  `actions` VARCHAR(1024) NOT NULL DEFAULT ''," +
		"  PRIMARY KEY (`owner_type`, `owner_id`, `mission_id`)" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	public static final String CREATE_GROWTH_TABLE = "CREATE TABLE IF NOT EXISTS `legion_growth` (" +
		"  `legion_id` INT NOT NULL," +
		"  `level` INT NOT NULL DEFAULT 1," +
		"  `exp` INT NOT NULL DEFAULT 0," +
		"  `essence` INT NOT NULL DEFAULT 0," +
		"  `essence_piece` INT NOT NULL DEFAULT 0," +
		"  PRIMARY KEY (`legion_id`)," +
		"  CONSTRAINT `legion_growth_legion_fk` FOREIGN KEY (`legion_id`) REFERENCES `legions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	private static final String LOAD = "SELECT instance_id, period_start, last_update, rewarded_stages, actions FROM legion_mission"
		+ " WHERE owner_type=? AND owner_id=? AND mission_id=?";
	private static final String STORE = "INSERT INTO legion_mission (owner_type, owner_id, mission_id, instance_id, last_instance_id, period_start,"
		+ " last_update, rewarded_stages, actions) VALUES (?,?,?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE instance_id=VALUES(instance_id),"
		+ " last_instance_id=VALUES(last_instance_id), period_start=VALUES(period_start), last_update=VALUES(last_update),"
		+ " rewarded_stages=VALUES(rewarded_stages), actions=VALUES(actions)";
	private static final String MAX_INSTANCE = "SELECT COALESCE(MAX(last_instance_id), 0) FROM legion_mission";
	private static final String LOAD_GROWTH = "SELECT level, exp, essence, essence_piece FROM legion_growth WHERE legion_id=?";
	private static final String STORE_GROWTH = "INSERT INTO legion_growth (legion_id, level, exp, essence, essence_piece) VALUES (?,?,?,?,?)"
		+ " ON DUPLICATE KEY UPDATE level=VALUES(level), exp=VALUES(exp), essence=VALUES(essence), essence_piece=VALUES(essence_piece)";

	private LegionMissionDAO() {
	}

	/**
	 * @return a missão gravada, ou null
	 */
	public static LegionMissionProgress load(LegionMissionProgress.Owner owner, int ownerId, int missionId) throws SQLException {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD)) {
			stmt.setInt(1, owner.ordinal());
			stmt.setInt(2, ownerId);
			stmt.setInt(3, missionId);
			try (ResultSet rs = stmt.executeQuery()) {
				if (!rs.next())
					return null;
				return new LegionMissionProgress(missionId, rs.getLong(1), rs.getLong(2), rs.getLong(3), rs.getInt(4),
					LegionMissionProgress.parseActions(rs.getString(5)));
			}
		}
	}

	public static void store(LegionMissionProgress.Owner owner, int ownerId, LegionMissionProgress progress) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(STORE)) {
			stmt.setInt(1, owner.ordinal());
			stmt.setInt(2, ownerId);
			stmt.setInt(3, progress.getMissionId());
			stmt.setLong(4, progress.getInstanceId());
			stmt.setLong(5, progress.getLastInstanceId());
			stmt.setLong(6, progress.getPeriodStart());
			stmt.setLong(7, progress.getLastUpdate());
			stmt.setInt(8, progress.getRewardedStages());
			stmt.setString(9, progress.getActionsText());
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Could not store legion mission " + progress.getMissionId() + " of " + owner + " " + ownerId, e);
		}
	}

	public static long loadMaxInstanceId() throws SQLException {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(MAX_INSTANCE);
			ResultSet rs = stmt.executeQuery()) {
			return rs.next() ? rs.getLong(1) : 0;
		}
	}

	public static void loadGrowth(Legion legion) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_GROWTH)) {
			stmt.setInt(1, legion.getLegionId());
			try (ResultSet rs = stmt.executeQuery()) {
				if (rs.next())
					legion.setGrowth(rs.getInt(1), rs.getInt(2), rs.getInt(3), rs.getInt(4));
			}
		} catch (SQLException e) {
			log.error("Could not load growth of " + legion, e);
		}
	}

	public static void storeGrowth(Legion legion) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(STORE_GROWTH)) {
			stmt.setInt(1, legion.getLegionId());
			stmt.setInt(2, legion.getGrowthLevel());
			stmt.setInt(3, legion.getGrowthExp());
			stmt.setInt(4, legion.getEssence());
			stmt.setInt(5, legion.getEssencePiece());
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Could not store growth of " + legion, e);
		}
	}
}
