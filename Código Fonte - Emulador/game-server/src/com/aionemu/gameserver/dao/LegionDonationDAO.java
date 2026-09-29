package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Types;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.team.legion.LegionCraftBoard;
import com.aionemu.gameserver.model.team.legion.LegionDonationBoard;
import com.aionemu.gameserver.model.team.legion.LegionDonationProgress;

/**
 * Produção de moedas da Legion: a lista do dia e os pontos de cada Legion ({@code legion_donation}), o progresso de cada personagem
 * ({@code player_legion_donation}) e as doações para as receitas de produção ({@code legion_craft}).
 */
public final class LegionDonationDAO {

	private static final Logger log = LoggerFactory.getLogger(LegionDonationDAO.class);

	public static final String CREATE_LEGION_TABLE = "CREATE TABLE IF NOT EXISTS `legion_donation` (" +
		"  `legion_id` INT NOT NULL," +
		"  `day` DATE NOT NULL," +
		"  `selection` VARCHAR(255) NOT NULL DEFAULT ''," +
		"  `points` INT NOT NULL DEFAULT 0," +
		"  PRIMARY KEY (`legion_id`)," +
		"  CONSTRAINT `legion_donation_legion_fk` FOREIGN KEY (`legion_id`) REFERENCES `legions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	public static final String CREATE_PLAYER_TABLE = "CREATE TABLE IF NOT EXISTS `player_legion_donation` (" +
		"  `player_id` INT NOT NULL," +
		"  `day` DATE NULL," +
		"  `count_today` INT NOT NULL DEFAULT 0," +
		"  `points_today` INT NOT NULL DEFAULT 0," +
		"  `points_total` INT NOT NULL DEFAULT 0," +
		"  `streak` INT NOT NULL DEFAULT 0," +
		"  `last_production_day` DATE NULL," +
		"  `coins` INT NOT NULL DEFAULT 0," +
		"  PRIMARY KEY (`player_id`)," +
		"  CONSTRAINT `player_legion_donation_player_fk` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	public static final String CREATE_CRAFT_TABLE = "CREATE TABLE IF NOT EXISTS `legion_craft` (" +
		"  `legion_id` INT NOT NULL," +
		"  `recipe_id` INT NOT NULL," +
		"  `donated` VARCHAR(512) NOT NULL DEFAULT ''," +
		"  `craft_start` INT NOT NULL DEFAULT 0," +
		"  `crafting` TINYINT NOT NULL DEFAULT 0," +
		"  PRIMARY KEY (`legion_id`, `recipe_id`)," +
		"  CONSTRAINT `legion_craft_legion_fk` FOREIGN KEY (`legion_id`) REFERENCES `legions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	private static final String LOAD_CRAFT = "SELECT recipe_id, donated, craft_start, crafting FROM legion_craft WHERE legion_id=?";
	private static final String STORE_CRAFT = "INSERT INTO legion_craft (legion_id, recipe_id, donated, craft_start, crafting) VALUES (?,?,?,?,?)"
		+ " ON DUPLICATE KEY UPDATE donated=VALUES(donated), craft_start=VALUES(craft_start), crafting=VALUES(crafting)";
	private static final String LOAD_BOARD = "SELECT day, selection, points FROM legion_donation WHERE legion_id=?";
	private static final String STORE_BOARD = "INSERT INTO legion_donation (legion_id, day, selection, points) VALUES (?,?,?,?)"
		+ " ON DUPLICATE KEY UPDATE day=VALUES(day), selection=VALUES(selection), points=VALUES(points)";
	private static final String PROGRESS_COLUMNS = "day, count_today, points_today, points_total, streak, last_production_day, coins";
	private static final String LOAD_PROGRESS = "SELECT " + PROGRESS_COLUMNS + " FROM player_legion_donation WHERE player_id=?";
	private static final String LOAD_LEGION_PROGRESS = "SELECT d.player_id, " + PROGRESS_COLUMNS.replaceAll("(\\w+)", "d.$1")
		+ " FROM player_legion_donation d JOIN legion_members m ON m.player_id = d.player_id WHERE m.legion_id=?";
	private static final String STORE_PROGRESS = "INSERT INTO player_legion_donation (player_id, " + PROGRESS_COLUMNS + ") VALUES (?,?,?,?,?,?,?,?)"
		+ " ON DUPLICATE KEY UPDATE day=VALUES(day), count_today=VALUES(count_today), points_today=VALUES(points_today),"
		+ " points_total=VALUES(points_total), streak=VALUES(streak), last_production_day=VALUES(last_production_day), coins=VALUES(coins)";

	private LegionDonationDAO() {
	}

	/**
	 * @return a lista gravada, ou null se a Legion nunca teve uma
	 */
	public static LegionDonationBoard loadBoard(int legionId) throws SQLException {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_BOARD)) {
			stmt.setInt(1, legionId);
			try (ResultSet rs = stmt.executeQuery()) {
				if (!rs.next())
					return null;
				return new LegionDonationBoard(rs.getDate(1).toLocalDate(), LegionDonationBoard.parseSelection(rs.getString(2)), rs.getInt(3));
			}
		}
	}

	public static void storeBoard(int legionId, LegionDonationBoard board) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(STORE_BOARD)) {
			stmt.setInt(1, legionId);
			stmt.setDate(2, Date.valueOf(board.getDay()));
			stmt.setString(3, board.getSelectionText());
			stmt.setInt(4, board.getPoints());
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Could not store legion donation board of legion " + legionId, e);
		}
	}

	/**
	 * @return o progresso gravado, ou um vazio se o personagem nunca produziu
	 */
	public static LegionDonationProgress loadProgress(int playerId) throws SQLException {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_PROGRESS)) {
			stmt.setInt(1, playerId);
			try (ResultSet rs = stmt.executeQuery()) {
				return rs.next() ? readProgress(rs, 1) : LegionDonationProgress.empty();
			}
		}
	}

	/**
	 * @return o progresso gravado de cada membro da Legion que já produziu
	 */
	public static Map<Integer, LegionDonationProgress> loadLegionProgress(int legionId) throws SQLException {
		Map<Integer, LegionDonationProgress> progress = new HashMap<>();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_LEGION_PROGRESS)) {
			stmt.setInt(1, legionId);
			try (ResultSet rs = stmt.executeQuery()) {
				while (rs.next())
					progress.put(rs.getInt(1), readProgress(rs, 2));
			}
		}
		return progress;
	}

	public static void storeProgress(int playerId, LegionDonationProgress progress) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(STORE_PROGRESS)) {
			stmt.setInt(1, playerId);
			setDate(stmt, 2, progress.getDay());
			stmt.setInt(3, progress.getStoredCountToday());
			stmt.setInt(4, progress.getStoredPointsToday());
			stmt.setInt(5, progress.getPointsTotal());
			stmt.setInt(6, progress.getStoredStreak());
			setDate(stmt, 7, progress.getLastProductionDay());
			stmt.setInt(8, progress.getCoins());
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Could not store legion donation progress of player " + playerId, e);
		}
	}

	public static LegionCraftBoard loadCraft(int legionId) throws SQLException {
		LegionCraftBoard board = new LegionCraftBoard();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_CRAFT)) {
			stmt.setInt(1, legionId);
			try (ResultSet rs = stmt.executeQuery()) {
				while (rs.next()) {
					board.setDonated(rs.getInt(1), LegionCraftBoard.parseDonated(rs.getString(2)));
					board.setCraft(rs.getInt(1), rs.getInt(3), rs.getBoolean(4));
				}
			}
		}
		return board;
	}

	public static void storeCraft(int legionId, int recipeId, LegionCraftBoard board) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(STORE_CRAFT)) {
			stmt.setInt(1, legionId);
			stmt.setInt(2, recipeId);
			stmt.setString(3, board.getDonatedText(recipeId));
			stmt.setInt(4, board.getCraftStart(recipeId));
			stmt.setBoolean(5, board.isCrafting(recipeId));
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Could not store legion craft " + recipeId + " of legion " + legionId, e);
		}
	}

	private static LegionDonationProgress readProgress(ResultSet rs, int first) throws SQLException {
		return new LegionDonationProgress(toLocalDate(rs.getDate(first)), rs.getInt(first + 1), rs.getInt(first + 2), rs.getInt(first + 3),
			rs.getInt(first + 4), toLocalDate(rs.getDate(first + 5)), rs.getInt(first + 6));
	}

	private static LocalDate toLocalDate(Date date) {
		return date == null ? null : date.toLocalDate();
	}

	private static void setDate(PreparedStatement stmt, int index, LocalDate date) throws SQLException {
		if (date == null)
			stmt.setNull(index, Types.DATE);
		else
			stmt.setDate(index, Date.valueOf(date));
	}
}
