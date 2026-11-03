package com.aionemu.gameserver.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.gameserver.model.gameobjects.player.Player;

/** Persistent per-character bitset for the 32 reward flags carried by S 0x0148. */
public final class CombatTalentRewardDAO {

	private static final Logger log = LoggerFactory.getLogger(CombatTalentRewardDAO.class);
	private static final String LOAD = "SELECT claimed_mask FROM player_combat_talent_rewards WHERE player_id=?";
	private static final String ENSURE = "INSERT IGNORE INTO player_combat_talent_rewards (player_id, claimed_mask) VALUES (?,0)";
	private static final String CLAIM = "UPDATE player_combat_talent_rewards SET claimed_mask=claimed_mask|? WHERE player_id=? AND (claimed_mask&?)=0";
	private static final String UNCLAIM = "UPDATE player_combat_talent_rewards SET claimed_mask=claimed_mask&~? WHERE player_id=?";

	private static volatile boolean tableChecked = false;

	private static void ensureTable(Connection con) {
		if (!tableChecked) {
			try (java.sql.Statement s = con.createStatement()) {
				s.executeUpdate("CREATE TABLE IF NOT EXISTS `player_combat_talent_rewards` (" +
					"  `player_id` INT NOT NULL," +
					"  `claimed_mask` INT UNSIGNED NOT NULL DEFAULT 0," +
					"  PRIMARY KEY (`player_id`)," +
					"  CONSTRAINT `player_combat_talent_rewards_player_fk` FOREIGN KEY (`player_id`)" +
					"    REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE" +
					") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;");
				tableChecked = true;
			} catch (Exception e) {
				log.warn("Could not ensure player_combat_talent_rewards table: " + e.getMessage());
			}
		}
	}

	private CombatTalentRewardDAO() {
	}

	public static int loadClaimedMask(Player player) {
		try (Connection con = DatabaseFactory.getConnection()) {
			ensureTable(con);
			try (PreparedStatement stmt = con.prepareStatement(LOAD)) {
				stmt.setInt(1, player.getObjectId());
				try (ResultSet result = stmt.executeQuery()) {
					return result.next() ? result.getInt(1) : 0;
				}
			}
		} catch (Exception e) {
			log.error("Could not load Combat Talent rewards for " + player, e);
			return 0;
		}
	}

	public static boolean claim(Player player, int rewardId) {
		int bit = 1 << (rewardId - 1);
		try (Connection con = DatabaseFactory.getConnection()) {
			con.setAutoCommit(false);
			try (PreparedStatement ensure = con.prepareStatement(ENSURE); PreparedStatement claim = con.prepareStatement(CLAIM)) {
				ensure.setInt(1, player.getObjectId());
				ensure.executeUpdate();
				claim.setInt(1, bit);
				claim.setInt(2, player.getObjectId());
				claim.setInt(3, bit);
				boolean claimed = claim.executeUpdate() == 1;
				con.commit();
				return claimed;
			} catch (Exception e) {
				con.rollback();
				throw e;
			} finally {
				con.setAutoCommit(true);
			}
		} catch (Exception e) {
			log.error("Could not claim Combat Talent reward " + rewardId + " for " + player, e);
			return false;
		}
	}

	public static void unclaim(Player player, int rewardId) {
		int bit = 1 << (rewardId - 1);
		try (Connection con = DatabaseFactory.getConnection(); PreparedStatement stmt = con.prepareStatement(UNCLAIM)) {
			stmt.setInt(1, bit);
			stmt.setInt(2, player.getObjectId());
			stmt.executeUpdate();
		} catch (Exception e) {
			log.error("Could not roll back Combat Talent reward " + rewardId + " for " + player, e);
		}
	}
}
