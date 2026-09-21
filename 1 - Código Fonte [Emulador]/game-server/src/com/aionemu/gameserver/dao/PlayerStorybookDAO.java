package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.player.PlayerStorybook;

/**
 * Book of Legends por personagem: o que foi registrado em cada livro (player_storybook_items) e os livros completos (player_storybook_finished).
 */
public final class PlayerStorybookDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerStorybookDAO.class);
	private static final String LOAD_ITEMS = "SELECT storybook_id, item_id, item_count FROM player_storybook_items WHERE player_id=? ORDER BY register_order";
	private static final String LOAD_FINISHED = "SELECT storybook_id FROM player_storybook_finished WHERE player_id=? ORDER BY finish_time";
	private static final String STORE_ITEM = "INSERT INTO player_storybook_items (player_id, storybook_id, item_id, item_count) VALUES (?,?,?,?)"
		+ " ON DUPLICATE KEY UPDATE item_count=VALUES(item_count)";
	private static final String STORE_FINISHED = "INSERT IGNORE INTO player_storybook_finished (player_id, storybook_id) VALUES (?,?)";
	public static final String CREATE_ITEMS_TABLE = "CREATE TABLE IF NOT EXISTS `player_storybook_items` (" +
		"  `player_id` INT NOT NULL," +
		"  `storybook_id` INT NOT NULL," +
		"  `item_id` INT NOT NULL," +
		"  `item_count` INT UNSIGNED NOT NULL," +
		"  `register_order` BIGINT NOT NULL AUTO_INCREMENT," +
		"  PRIMARY KEY (`player_id`, `storybook_id`, `item_id`)," +
		"  KEY `register_order` (`register_order`)," +
		"  CONSTRAINT `player_storybook_items_player_fk` FOREIGN KEY (`player_id`)" +
		"    REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
	public static final String CREATE_FINISHED_TABLE = "CREATE TABLE IF NOT EXISTS `player_storybook_finished` (" +
		"  `player_id` INT NOT NULL," +
		"  `storybook_id` INT NOT NULL," +
		"  `finish_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP," +
		"  PRIMARY KEY (`player_id`, `storybook_id`)," +
		"  CONSTRAINT `player_storybook_finished_player_fk` FOREIGN KEY (`player_id`)" +
		"    REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

	private static volatile boolean tableChecked = false;

	private PlayerStorybookDAO() {
	}

	private static void ensureTables(Connection con) {
		if (!tableChecked) {
			try (Statement s = con.createStatement()) {
				s.executeUpdate(CREATE_ITEMS_TABLE);
				s.executeUpdate(CREATE_FINISHED_TABLE);
				tableChecked = true;
			} catch (Exception e) {
				log.warn("Could not ensure player_storybook tables: " + e.getMessage());
			}
		}
	}

	/**
	 * @throws SQLException
	 *           se o banco falhar: quem chama não pode seguir com o livro vazio, senão o registro seguinte sobrescreve o progresso
	 */
	public static PlayerStorybook load(int playerId) throws SQLException {
		PlayerStorybook storybook = new PlayerStorybook();
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTables(con);
			try (PreparedStatement stmt = con.prepareStatement(LOAD_ITEMS)) {
				stmt.setInt(1, playerId);
				try (ResultSet rs = stmt.executeQuery()) {
					while (rs.next())
						storybook.setRegistered(rs.getInt(1), rs.getInt(2), rs.getLong(3));
				}
			}
			try (PreparedStatement stmt = con.prepareStatement(LOAD_FINISHED)) {
				stmt.setInt(1, playerId);
				try (ResultSet rs = stmt.executeQuery()) {
					while (rs.next())
						storybook.setFinished(rs.getInt(1));
				}
			}
		}
		return storybook;
	}

	/**
	 * Grava as quantidades novas de um livro e, se for o caso, o livro completo, numa transação só.
	 *
	 * @param items
	 *          item -> quantidade total registrada
	 */
	public static boolean store(int playerId, int storybookId, Map<Integer, Long> items, boolean finished) {
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTables(con);
			con.setAutoCommit(false);
			try (PreparedStatement item = con.prepareStatement(STORE_ITEM); PreparedStatement finish = con.prepareStatement(STORE_FINISHED)) {
				for (Map.Entry<Integer, Long> entry : items.entrySet()) {
					item.setInt(1, playerId);
					item.setInt(2, storybookId);
					item.setInt(3, entry.getKey());
					item.setLong(4, entry.getValue());
					item.addBatch();
				}
				item.executeBatch();
				if (finished) {
					finish.setInt(1, playerId);
					finish.setInt(2, storybookId);
					finish.executeUpdate();
				}
				con.commit();
				return true;
			} catch (Exception e) {
				con.rollback();
				throw e;
			} finally {
				con.setAutoCommit(true);
			}
		} catch (Exception e) {
			log.error("Could not store Book of Legends {} for player {}", storybookId, playerId, e);
			return false;
		}
	}
}
