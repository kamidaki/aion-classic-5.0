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
 * Entradas do Wardrobe (player_wardrobe) e o total de slots (players.wardrobe_size). A cor fica em {@link WardrobeEntry#getStoredColor()}.
 */
public class PlayerWardrobeDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerWardrobeDAO.class);

	/** Mesma definição do aion_gs.sql; o DatabaseSchemaService cria no boot se faltar. */
	public static final String CREATE_TABLE = "CREATE TABLE IF NOT EXISTS `player_wardrobe` (" +
		"  `object_id` int NOT NULL," +
		"  `player_id` int NOT NULL," +
		"  `item_id` int NOT NULL," +
		"  `color` int NOT NULL DEFAULT '0'," +
		"  `like` tinyint(1) NOT NULL DEFAULT '0'," +
		"  PRIMARY KEY (`object_id`)," +
		"  KEY `player_id` (`player_id`)," +
		"  CONSTRAINT `player_wardrobe_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
		") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";
	public static final String INSERT_QUERY = "INSERT INTO player_wardrobe (object_id, player_id, item_id, color, `like`) VALUES (?, ?, ?, ?, ?)";
	public static final String LOAD_QUERY = "SELECT * FROM `player_wardrobe` WHERE `player_id`=? ORDER BY `object_id`";
	public static final String UPDATE_QUERY = "UPDATE player_wardrobe SET `color`=?, `like`=? WHERE `object_id`=?";
	public static final String DELETE_QUERY = "DELETE FROM player_wardrobe WHERE object_id = ?";
	public static final String UPDATE_SIZE_QUERY = "UPDATE players SET wardrobe_size=? WHERE id=?";

	/**
	 * @return objeto -> entrada, na ordem dos objetos
	 * @throws SQLException
	 *           se a leitura falhar; quem chama deixa o guarda-roupa fora da sessão em vez de mostrar vazio e deixar registrar por cima
	 */
	public static Map<Integer, WardrobeEntry> load(int playerId) throws SQLException {
		Map<Integer, WardrobeEntry> entries = new LinkedHashMap<>();
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(LOAD_QUERY)) {
			stmt.setInt(1, playerId);
			try (ResultSet rset = stmt.executeQuery()) {
				while (rset.next()) {
					WardrobeEntry entry = new WardrobeEntry(rset.getInt("object_id"), rset.getInt("item_id"),
						WardrobeEntry.fromStoredColor(rset.getInt("color")), rset.getBoolean("like"));
					entries.put(entry.getObjectId(), entry);
				}
			}
		}
		return entries;
	}

	public static boolean addItem(int playerId, WardrobeEntry entry) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(INSERT_QUERY)) {
			stmt.setInt(1, entry.getObjectId());
			stmt.setInt(2, playerId);
			stmt.setInt(3, entry.getItemId());
			stmt.setInt(4, entry.getStoredColor());
			stmt.setBoolean(5, entry.isLiked());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not insert wardrobe entry {} of player {}", entry.getObjectId(), playerId, e);
			return false;
		}
	}

	public static boolean updateItem(int playerId, WardrobeEntry entry) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(UPDATE_QUERY)) {
			stmt.setInt(1, entry.getStoredColor());
			stmt.setBoolean(2, entry.isLiked());
			stmt.setInt(3, entry.getObjectId());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not update wardrobe entry {} of player {}", entry.getObjectId(), playerId, e);
			return false;
		}
	}

	public static boolean deleteItem(int playerId, WardrobeEntry entry) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(DELETE_QUERY)) {
			stmt.setInt(1, entry.getObjectId());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not delete wardrobe entry {} of player {}", entry.getObjectId(), playerId, e);
			return false;
		}
	}

	/**
	 * Grava o total de slots na hora da expansão, junto com o item gasto; o PlayerDAO só grava de novo ao salvar o personagem.
	 */
	public static boolean storeSize(int playerId, int size) {
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(UPDATE_SIZE_QUERY)) {
			stmt.setInt(1, size);
			stmt.setInt(2, playerId);
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not store wardrobe size {} of player {}", size, playerId, e);
			return false;
		}
	}

	public static int[] getUsedIDs() {
		try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement stmt = con.prepareStatement("SELECT object_id FROM player_wardrobe", ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY)) {
			try (ResultSet rs = stmt.executeQuery()) {
				rs.last();
				int count = rs.getRow();
				rs.beforeFirst();
				int[] ids = new int[count];
				for (int i = 0; rs.next(); i++) {
					ids[i] = rs.getInt("object_id");
				}
				return ids;
			}
		} catch (SQLException e) {
			log.error("Can't get list of IDs from player_wardrobe table", e);
			return new int[0];
		}
	}
}
