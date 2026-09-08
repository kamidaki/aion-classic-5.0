package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;

public class PlayerWardrobeDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerWardrobeDAO.class);

	public static final String INSERT_QUERY = "INSERT INTO player_wardrobe (object_id, player_id, item_id, color, `like`) VALUES (?, ?, ?, ?, ?)";
	public static final String LOAD_QUERY = "SELECT * FROM `player_wardrobe` WHERE `player_id`=?";
	public static final String UPDATE_QUERY = "UPDATE player_wardrobe SET `color`=?, `like`=? WHERE `object_id`=?";
	public static final String DELETE_QUERY = "DELETE FROM player_wardrobe WHERE object_id = ?";

	public static void loadWardrobe(Player player) {
		try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement stmt = con.prepareStatement(LOAD_QUERY)) {
			stmt.setInt(1, player.getObjectId());
			try (ResultSet rset = stmt.executeQuery()) {
				while (rset.next()) {
					WardrobeEntry entry = new WardrobeEntry(
						rset.getInt("object_id"),
						rset.getInt("item_id"),
						rset.getInt("color"),
						rset.getBoolean("like")
					);
					player.getPlayerWardrobe().put(entry.getObjectId(), entry);
				}
			}
		} catch (SQLException e) {
			log.error("Could not load Wardrobe data for Player " + player.getName() + " from DB: " + e.getMessage(), e);
		}
	}

	public static boolean addItem(Player player, WardrobeEntry wardrobeEntry) {
		try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement stmt = con.prepareStatement(INSERT_QUERY)) {
			stmt.setInt(1, wardrobeEntry.getObjectId());
			stmt.setInt(2, player.getObjectId());
			stmt.setInt(3, wardrobeEntry.getItemId());
			stmt.setInt(4, wardrobeEntry.getColor());
			stmt.setBoolean(5, wardrobeEntry.isLiked());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("Could not insert Wardrobe data for Player " + player.getName() + " from DB: " + e.getMessage(), e);
			return false;
		}
	}

	public static boolean updateItem(Player player, WardrobeEntry wardrobeEntry) {
		try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement stmt = con.prepareStatement(UPDATE_QUERY)) {
			stmt.setInt(1, wardrobeEntry.getColor());
			stmt.setBoolean(2, wardrobeEntry.isLiked());
			stmt.setInt(3, wardrobeEntry.getObjectId());
			stmt.execute();
			return true;
		} catch (Exception e) {
			log.error("Could not update Wardrobe data for Player " + player.getName() + " from DB: " + e.getMessage(), e);
			return false;
		}
	}

	public static void deleteItem(Player player, WardrobeEntry wardrobeEntry) {
		try (Connection con = DatabaseFactory.getConnection();
				 PreparedStatement stmt = con.prepareStatement(DELETE_QUERY)) {
			stmt.setInt(1, wardrobeEntry.getObjectId());
			stmt.execute();
		} catch (SQLException e) {
			log.error("Could not delete Wardrobe item for Player " + player.getName() + ": " + e.getMessage(), e);
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
