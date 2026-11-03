package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.player.PlayerMoros;

/**
 * Moreth, Chronicle of Time por personagem: nível, pontos no nível e a hora (epoch ms) em que cada registro gasto volta, separadas por vírgula.
 */
public final class PlayerMorosDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerMorosDAO.class);
	private static final String LOAD = "SELECT level, points, restore_times FROM player_moros WHERE player_id=?";
	private static final String STORE = "INSERT INTO player_moros (player_id, level, points, restore_times) VALUES (?,?,?,?)"
		+ " ON DUPLICATE KEY UPDATE level=VALUES(level), points=VALUES(points), restore_times=VALUES(restore_times)";
	public static final String CREATE_TABLE = "CREATE TABLE IF NOT EXISTS `player_moros` (" +
		"  `player_id` INT NOT NULL," +
		"  `level` SMALLINT UNSIGNED NOT NULL DEFAULT 1," +
		"  `points` INT UNSIGNED NOT NULL DEFAULT 0," +
		"  `restore_times` VARCHAR(512) NOT NULL DEFAULT ''," +
		"  PRIMARY KEY (`player_id`)," +
		"  CONSTRAINT `player_moros_player_fk` FOREIGN KEY (`player_id`)" +
		"    REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	private static volatile boolean tableChecked = false;

	private PlayerMorosDAO() {
	}

	private static void ensureTable(Connection con) {
		if (!tableChecked) {
			try (Statement s = con.createStatement()) {
				s.executeUpdate(CREATE_TABLE);
				tableChecked = true;
			} catch (Exception e) {
				log.warn("Could not ensure player_moros table: " + e.getMessage());
			}
		}
	}

	/**
	 * @return o estado gravado, ou o inicial (nível 1, 0 pontos, todos os registros) se o personagem nunca gravou
	 * @throws SQLException
	 *           se o banco falhar: quem chama não pode seguir com o estado inicial, senão a próxima gravação apaga o progresso
	 */
	public static PlayerMoros load(int playerId) throws SQLException {
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTable(con);
			try (PreparedStatement stmt = con.prepareStatement(LOAD)) {
				stmt.setInt(1, playerId);
				try (ResultSet rs = stmt.executeQuery()) {
					if (!rs.next())
						return new PlayerMoros(1, 0, List.of());
					List<Long> restoreTimes = new ArrayList<>();
					for (String time : rs.getString(3).split(","))
						if (!time.isBlank())
							restoreTimes.add(Long.parseLong(time.trim()));
					return new PlayerMoros(rs.getInt(1), rs.getLong(2), restoreTimes);
				}
			}
		}
	}

	public static boolean store(int playerId, PlayerMoros moros) {
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTable(con);
			try (PreparedStatement stmt = con.prepareStatement(STORE)) {
				stmt.setInt(1, playerId);
				stmt.setInt(2, moros.getLevel());
				stmt.setLong(3, moros.getPoints());
				stmt.setString(4, moros.getRestoreTimes().stream().map(String::valueOf).collect(Collectors.joining(",")));
				stmt.executeUpdate();
				return true;
			}
		} catch (Exception e) {
			log.error("Could not store Moreth for player " + playerId, e);
			return false;
		}
	}
}
