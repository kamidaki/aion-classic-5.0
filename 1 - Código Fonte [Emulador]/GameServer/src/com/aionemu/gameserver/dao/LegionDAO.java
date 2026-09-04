package com.aionemu.gameserver.dao;

import com.aionemu.gameserver.model.team.legion.*;
import javolution.util.FastList;

import java.sql.Timestamp;
import java.util.Collection;
import java.util.TreeMap;

public abstract class LegionDAO implements IDFactoryAwareDAO
{
	public abstract boolean isNameUsed(String name);
	public abstract boolean saveNewLegion(Legion legion);
	public abstract void storeLegion(Legion legion);
	public abstract Legion loadLegion(String legionName);
	public abstract Legion loadLegion(int legionId);
	public abstract void deleteLegion(int legionId);
	public abstract TreeMap<Timestamp, String> loadAnnouncementList(int legionId);
	public abstract boolean saveNewAnnouncement(int legionId, Timestamp currentTime, String message);
	
	@Override
	public final String getClassName() {
		return LegionDAO.class.getName();
	}
	
	public abstract void storeLegionEmblem(int legionId, LegionEmblem legionEmblem);
	public abstract void removeAnnouncement(int legionId, Timestamp key);
	public abstract LegionEmblem loadLegionEmblem(int legionId);
	public abstract LegionWarehouse loadLegionStorage(Legion legion);
	public abstract void loadLegionHistory(Legion legion);
	public abstract boolean saveNewLegionHistory(int legionId, LegionHistory legionHistory);

	public abstract void storeLegionJoinRequest(LegionJoinRequest legionJoinRequest);
	public abstract FastList<LegionJoinRequest> loadLegionJoinRequests(int legionId);
	public abstract void deleteLegionJoinRequest(int legionId, int playerId);
	public abstract void deleteLegionJoinRequest(LegionJoinRequest legionJoinRequest);
}