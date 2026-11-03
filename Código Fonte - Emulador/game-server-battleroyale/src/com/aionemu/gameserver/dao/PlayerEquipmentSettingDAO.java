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
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.equipmentset.EquipmentSetting;

public class PlayerEquipmentSettingDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerEquipmentSettingDAO.class);

	private static final String SELECT_QUERY = "SELECT * FROM player_equipment_setting WHERE player_id = ?";
	private static final String REPLACE_QUERY = "REPLACE INTO player_equipment_setting (`player_id`, `macross_id`, `item_unique_id_1`, `item_unique_id_2`, `item_unique_id_3`, `item_unique_id_4`, `item_unique_id_5`, `item_unique_id_6`, `item_unique_id_7`, `item_unique_id_8`, `item_unique_id_9`, `item_unique_id_10`, `item_unique_id_11`, `item_unique_id_12`, `item_unique_id_13`, `item_unique_id_14`, `item_unique_id_15`, `item_unique_id_16`, `item_unique_id_17`, `item_unique_id_18`, `item_unique_id_19`, `item_unique_id_20`) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
	private static final String DELETE_QUERY = "DELETE FROM player_equipment_setting WHERE player_id = ? AND macross_id = ?";

	public static void loadEquipmentSetting(Player player) {
		try (Connection conn = DatabaseFactory.getConnection();
				 PreparedStatement stmt = conn.prepareStatement(SELECT_QUERY)) {
			stmt.setInt(1, player.getObjectId());
			try (ResultSet rset = stmt.executeQuery()) {
				while (rset.next()) {
					int macrossId = rset.getInt("macross_id");
					List<Integer> objIds = new ArrayList<>(20);
					for (int i = 1; i <= 20; i++) {
						objIds.add(rset.getInt("item_unique_id_" + i));
					}
					player.putPlayerEquipSettingList(new EquipmentSetting(player.getObjectId(), macrossId, objIds));
				}
			}
		} catch (SQLException e) {
			log.error("Error in PlayerEquipmentSettingDAO.loadEquipmentSetting for player " + player.getName(), e);
		}
	}

	public static void updateEquipmentSetting(EquipmentSetting macross) {
		try (Connection conn = DatabaseFactory.getConnection();
				 PreparedStatement stmt = conn.prepareStatement(REPLACE_QUERY)) {
			stmt.setInt(1, macross.getPlayerId());
			stmt.setInt(2, macross.getMacrossId());
			List<Integer> objIds = macross.getObjIds();
			for (int i = 0; i < 20; i++) {
				int val = (i < objIds.size()) ? objIds.get(i) : 0;
				stmt.setInt(3 + i, val);
			}
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Error in PlayerEquipmentSettingDAO.updateEquipmentSetting", e);
		}
	}

	public static void deleteEquipmentSetting(EquipmentSetting macross) {
		try (Connection conn = DatabaseFactory.getConnection();
				 PreparedStatement stmt = conn.prepareStatement(DELETE_QUERY)) {
			stmt.setInt(1, macross.getPlayerId());
			stmt.setInt(2, macross.getMacrossId());
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("Error in PlayerEquipmentSettingDAO.deleteEquipmentSetting", e);
		}
	}
}
