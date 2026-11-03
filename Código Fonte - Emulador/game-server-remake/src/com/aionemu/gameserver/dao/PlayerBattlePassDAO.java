package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassQuest;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassReward;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassSeason;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattleQuestState;
import com.aionemu.gameserver.model.templates.battle_pass.BattleQuestType;

public class PlayerBattlePassDAO {

	private static final Logger log = LoggerFactory.getLogger(PlayerBattlePassDAO.class);

	public static final String INSERT_SEASON = "INSERT INTO player_battle_pass (id, player_id, level, exp) VALUES (?, ?, ?, ?)";
	public static final String LOAD_SEASON = "SELECT * FROM player_battle_pass WHERE player_id=?";
	public static final String UPDATE_SEASON = "UPDATE player_battle_pass SET level=?, exp=? WHERE player_id=? AND id=?";

	public static final String INSERT_REWARD = "INSERT INTO player_battle_pass_reward (id, player_id, rewarded, unlockReward, season_id) VALUES (?, ?, ?, ?, ?)";
	public static final String LOAD_REWARD = "SELECT * FROM player_battle_pass_reward WHERE player_id=? AND season_id=?";
	public static final String UPDATE_REWARD = "UPDATE player_battle_pass_reward SET rewarded=?, unlockReward=? WHERE player_id=? AND id=?";

	public static final String INSERT_QUEST = "INSERT INTO player_battle_pass_quest (object_id, id, player_id, state, step, start_date, end_date, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)";
	public static final String LOAD_QUEST = "SELECT * FROM player_battle_pass_quest WHERE player_id=?";
	public static final String UPDATE_QUEST = "UPDATE player_battle_pass_quest SET state=?, step=? WHERE player_id=? AND object_id=?";

	public static final String DELETE_QUEST_BY_TYPE = "DELETE FROM player_battle_pass_quest WHERE type = ?";
	public static final String DELETE_ALL_SEASON = "DELETE FROM player_battle_pass";
	public static final String DELETE_ALL_REWARD = "DELETE FROM player_battle_pass_reward";
	public static final String SELECT_USED_IDS = "SELECT object_id FROM player_battle_pass_quest";

	public static boolean storeSeason(Player player, BattlePassSeason season) {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(INSERT_SEASON)) {
			stmt.setInt(1, season.getId());
			stmt.setInt(2, player.getObjectId());
			stmt.setInt(3, season.getLevel());
			stmt.setLong(4, season.getExp());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("storeSeason failed for player " + player.getName() + ": " + e.getMessage(), e);
			return false;
		}
	}

	public static boolean updateSeason(Player player, BattlePassSeason season) {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(UPDATE_SEASON)) {
			stmt.setInt(1, season.getLevel());
			stmt.setLong(2, season.getExp());
			stmt.setInt(3, player.getObjectId());
			stmt.setInt(4, season.getId());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("updateSeason failed for player " + player.getName() + ": " + e.getMessage(), e);
			return false;
		}
	}

	public static boolean storeReward(Player player, BattlePassReward reward, int seasonId) {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(INSERT_REWARD)) {
			stmt.setInt(1, reward.getId());
			stmt.setInt(2, player.getObjectId());
			stmt.setBoolean(3, reward.isRewarded());
			stmt.setBoolean(4, reward.isUnlockReward());
			stmt.setInt(5, seasonId);
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("storeReward failed for player " + player.getName() + ": " + e.getMessage(), e);
			return false;
		}
	}

	public static boolean updateReward(Player player, BattlePassReward reward) {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(UPDATE_REWARD)) {
			stmt.setBoolean(1, reward.isRewarded());
			stmt.setBoolean(2, reward.isUnlockReward());
			stmt.setInt(3, player.getObjectId());
			stmt.setInt(4, reward.getId());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("updateReward failed for player " + player.getName() + ": " + e.getMessage(), e);
			return false;
		}
	}

	public static boolean storeQuest(Player player, BattlePassQuest quest) {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(INSERT_QUEST)) {
			stmt.setInt(1, quest.getObjectId());
			stmt.setInt(2, quest.getId());
			stmt.setInt(3, player.getObjectId());
			stmt.setInt(4, quest.getState().getValue());
			stmt.setInt(5, quest.getStep());
			stmt.setTimestamp(6, quest.getStartDate());
			stmt.setTimestamp(7, quest.getEndateDate());
			stmt.setInt(8, quest.getType().getValue());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("storeQuest failed for player " + player.getName() + ": " + e.getMessage(), e);
			return false;
		}
	}

	public static boolean updateQuest(Player player, BattlePassQuest quest) {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(UPDATE_QUEST)) {
			stmt.setInt(1, quest.getState().getValue());
			stmt.setInt(2, quest.getStep());
			stmt.setInt(3, player.getObjectId());
			stmt.setInt(4, quest.getObjectId());
			stmt.execute();
			return true;
		} catch (SQLException e) {
			log.error("updateQuest failed for player " + player.getName() + ": " + e.getMessage(), e);
			return false;
		}
	}

	public static Map<Integer, BattlePassSeason> loadPlayerBattlePass(Player player) {
		Map<Integer, BattlePassSeason> seasonMap = new HashMap<>();
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(LOAD_SEASON)) {
			stmt.setInt(1, player.getObjectId());
			try (ResultSet rset = stmt.executeQuery()) {
				while (rset.next()) {
					BattlePassSeason season = new BattlePassSeason(rset.getInt("id"), rset.getInt("level"), rset.getLong("exp"));
					season.setRewards(loadPlayerBattleReward(season.getId(), player));
					seasonMap.put(season.getId(), season);
				}
			}
		} catch (SQLException e) {
			log.error("loadPlayerBattlePass failed for player " + player.getName() + ": " + e.getMessage(), e);
		}
		return seasonMap;
	}

	public static Map<Integer, BattlePassReward> loadPlayerBattleReward(int seasonId, Player player) {
		Map<Integer, BattlePassReward> rewardMap = new HashMap<>();
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(LOAD_REWARD)) {
			stmt.setInt(1, player.getObjectId());
			stmt.setInt(2, seasonId);
			try (ResultSet rset = stmt.executeQuery()) {
				while (rset.next()) {
					BattlePassReward reward = new BattlePassReward(rset.getInt("id"), rset.getBoolean("rewarded"), rset.getBoolean("unlockReward"));
					if (reward.getTemplate() != null) {
						rewardMap.put(reward.getTemplate().getLevel(), reward);
					}
				}
			}
		} catch (SQLException e) {
			log.error("loadPlayerBattleReward failed for player " + player.getName() + ": " + e.getMessage(), e);
		}
		return rewardMap;
	}

	public static Map<Integer, BattlePassQuest> loadPlayerBattleQuest(Player player) {
		Map<Integer, BattlePassQuest> questMap = new HashMap<>();
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(LOAD_QUEST)) {
			stmt.setInt(1, player.getObjectId());
			try (ResultSet rset = stmt.executeQuery()) {
				while (rset.next()) {
					BattlePassQuest quest = new BattlePassQuest(
						rset.getInt("object_id"),
						rset.getInt("id"),
						BattleQuestType.getPlayerClassById(rset.getInt("type")),
						BattleQuestState.getPlayerClassById(rset.getInt("state")),
						rset.getInt("step"),
						rset.getTimestamp("start_date"),
						rset.getTimestamp("end_date")
					);
					questMap.put(quest.getObjectId(), quest);
				}
			}
		} catch (SQLException e) {
			log.error("loadPlayerBattleQuest failed for player " + player.getName() + ": " + e.getMessage(), e);
		}
		return questMap;
	}

	public static void deleteQuest(BattleQuestType type) {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(DELETE_QUEST_BY_TYPE)) {
			stmt.setInt(1, type.getValue());
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("deleteQuest failed for type " + type + ": " + e.getMessage(), e);
		}
	}

	public static void deleteSeason() {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(DELETE_ALL_SEASON)) {
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("deleteSeason failed: " + e.getMessage(), e);
		}
	}

	public static void deleteReward() {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(DELETE_ALL_REWARD)) {
			stmt.executeUpdate();
		} catch (SQLException e) {
			log.error("deleteReward failed: " + e.getMessage(), e);
		}
	}

	public static int[] getUsedIDs() {
		try (Connection con = DatabaseFactory.getConnection();
		     PreparedStatement stmt = con.prepareStatement(SELECT_USED_IDS, ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY)) {
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
			log.error("Can't get list of id's from player_battle_pass_quest table", e);
			return new int[0];
		}
	}
}
