package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.LinkedHashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;

/**
 * Lista de cabelo do Wardrobe 5.0 (player_hairstyle): um penteado registrado por item, com a marca de favorito. O total de slots fica em
 * players.hairstyle_size ({@link PlayerWardrobeDAO#storeHairstyleSize}).
 */
public class PlayerHairstyleDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerHairstyleDAO.class);

	/** O DatabaseSchemaService cria no boot se faltar. */
	public static final String CREATE_TABLE = "CREATE TABLE IF NOT EXISTS `player_hairstyle` (" +
		"  `object_id` int NOT NULL," +
		"  `player_id` int NOT NULL," +
		"  `item_id` int NOT NULL," +
		"  `like` tinyint(1) NOT NULL DEFAULT '0'," +
		"  PRIMARY KEY (`object_id`)," +
		"  KEY `player_id` (`player_id`)," +
		"  CONSTRAINT `player_hairstyle_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
	private static final String INSERT_QUERY = "INSERT INTO player_hairstyle (object_id, player_id, item_id, `like`) VALUES (?, ?, ?, ?)";
	private static final String LOAD_QUERY = "SELECT * FROM `player_hairstyle` WHERE `player_id`=? ORDER BY `object_id`";
	private static final String UPDATE_QUERY = "UPDATE player_hairstyle SET `like`=? WHERE `object_id`=?";
	private static final String DELETE_QUERY = "DELETE FROM player_hairstyle WHERE object_id = ?";

	/**
	 * @return objeto -> penteado, na ordem dos objetos
	 * @throws SQLException
	 *           se a leitura falhar; quem chama deixa a lista fora da sessão em vez de mostrar vazia e deixar registrar por cima
	 */
	public static Map<Integer, WardrobeEntry> load(int playerId) throws SQLException {
		Map<Integer, WardrobeEntry> entries = new LinkedHashMap<>();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_QUERY)) {
			stmt.setInt(1, playerId);
			try (ResultSet rset = stmt.executeQuery()) {
				while (rset.next()) {
					WardrobeEntry entry = new WardrobeEntry(rset.getInt("object_id"), rset.getInt("item_id"), null, rset.getBoolean("like"));
					entries.put(entry.getObjectId(), entry);
				}
			}
		}
		return entries;
	}

	public static boolean add(int playerId, WardrobeEntry entry) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(INSERT_QUERY)) {
			stmt.setInt(1, entry.getObjectId());
			stmt.setInt(2, playerId);
			stmt.setInt(3, entry.getItemId());
			stmt.setBoolean(4, entry.isLiked());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not insert hairstyle {} of player {}", entry.getObjectId(), playerId, e);
			return false;
		}
	}

	public static boolean update(WardrobeEntry entry) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(UPDATE_QUERY)) {
			stmt.setBoolean(1, entry.isLiked());
			stmt.setInt(2, entry.getObjectId());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not update hairstyle {}", entry.getObjectId(), e);
			return false;
		}
	}

	public static boolean delete(WardrobeEntry entry) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(DELETE_QUERY)) {
			stmt.setInt(1, entry.getObjectId());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not delete hairstyle {}", entry.getObjectId(), e);
			return false;
		}
	}

	public static int[] getUsedIDs() {
		try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement stmt = con.prepareStatement("SELECT object_id FROM player_hairstyle", ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY)) {
			try (ResultSet rs = stmt.executeQuery()) {
				rs.last();
				int count = rs.getRow();
				rs.beforeFirst();
				int[] ids = new int[count];
				for (int i = 0; rs.next(); i++)
					ids[i] = rs.getInt("object_id");
				return ids;
			}
		} catch (SQLException e) {
			log.error("Can't get list of IDs from player_hairstyle table", e);
			return new int[0];
		}
	}
}
