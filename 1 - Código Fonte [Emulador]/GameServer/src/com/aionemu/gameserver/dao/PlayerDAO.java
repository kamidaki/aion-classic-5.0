package com.aionemu.gameserver.dao;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.PlayerCommonData;
import com.aionemu.gameserver.model.team.legion.LegionJoinRequestState;

import java.sql.Timestamp;
import java.util.Collection;
import java.util.List;
import java.util.Map;

public abstract class PlayerDAO implements IDFactoryAwareDAO
{
	public abstract boolean isNameUsed(String name);
	public abstract Map<Integer, String> getPlayerNames(Collection<Integer> playerObjectIds);
	public abstract void storePlayer(Player player);
	public abstract boolean saveNewPlayer(PlayerCommonData pcd, int accountId, String accountName);
	public abstract PlayerCommonData loadPlayerCommonData(int playerObjId);
	public abstract void deletePlayer(int playerId);
	public abstract void updateDeletionTime(int objectId, Timestamp deletionDate);
	public abstract void storeCreationTime(int objectId, Timestamp creationDate);
	public abstract void setCreationDeletionTime(PlayerAccountData acData);
	public abstract List<Integer> getPlayerOidsOnAccount(int accountId);
	public abstract void storeLastOnlineTime(final int objectId, final Timestamp lastOnline);
	public abstract void onlinePlayer(final Player player, final boolean online);
	public abstract void setPlayersOffline(final boolean online);
	public abstract PlayerCommonData loadPlayerCommonDataByName(String name);
	public abstract int getAccountIdByName(final String name);
	public abstract String getPlayerNameByObjId(final int playerObjId);
	public abstract int getPlayerIdByName(final String playerName);
	public abstract void storePlayerName(PlayerCommonData recipientCommonData);
	public abstract int getCharacterCountOnAccount(final int accountId);
	public abstract int getCharacterCountForRace(Race race);
	public abstract int getOnlinePlayerCount();
	public abstract List<Integer> getPlayersToDelete(int paramInt1, int paramInt2);
	public abstract void setPlayerLastTransferTime(final int playerId, final long time);
	@Override
	public final String getClassName() {
		return PlayerDAO.class.getName();
	}
	public abstract Timestamp getCharacterCreationDateId(final int obj);
	public abstract void updateLegionJoinRequestState(int playerId, LegionJoinRequestState state);
	public abstract void clearJoinRequest(final int playerId);
	public abstract void getJoinRequestState(Player player);
}