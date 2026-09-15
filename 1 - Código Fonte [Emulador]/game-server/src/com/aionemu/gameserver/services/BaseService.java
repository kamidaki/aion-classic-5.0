package com.aionemu.gameserver.services;

import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.base.*;
import com.aionemu.gameserver.model.templates.base.BaseTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * @author Lost Academy Team & Durak
 */
public class BaseService {

	private final static Logger log = LoggerFactory.getLogger(BaseService.class);
	private final static BaseService INSTANCE = new BaseService();
	private final Map<Integer, Base<?>> activeBases = new ConcurrentHashMap<>();
	private final Map<Integer, BaseLocation> allBaseLocations = new HashMap<>();

	/**
	 * Initializes all base locations
	 */
	private BaseService() {
		log.info("Initializing bases...");

		for (BaseTemplate template : DataManager.BASE_DATA.getAllBaseTemplates()) {
			if (template.getType() == null) {
				log.warn("Skipping base location {} with null type", template.getId());
				continue;
			}
			BaseLocation loc = switch (template.getType()) {
				case CASUAL -> new BaseLocation(template);
				case SIEGE -> new SiegeBaseLocation(template);
				case STAINED -> new StainedBaseLocation(template);
			};
			allBaseLocations.put(template.getId(), loc);
		}
	}

	/**
	 * Executes start of all casual and stained bases.
	 */
	public void initBases() {
		allBaseLocations.values().forEach(loc -> {
			switch (loc.getType()) {
				case CASUAL, STAINED -> start(loc.getId());
			}
		});
	}

	/**
	 * Generates a new BaseObject for given id
	 */
	public void start(int id) {
		final Base<?> base;

		if (isActive(id)) {
			log.error("Called BaseService#start with active id {}", id);
			return;
		}

		base = newBase(id);
		activeBases.put(id, base);
		base.start();
	}

	/**
	 * Stops a base.
	 */
	public void stop(int id) {
		Base<?> base = activeBases.remove(id);
		if (base != null)
			base.stop();
	}

	public Collection<Base<?>> getActiveBases() {
		return activeBases.values();
	}

	/**
	 * @return A type-specific base object for given id, if a base location is given for the specific id.
	 */
	private Base<?> newBase(int id) {
		BaseLocation loc = allBaseLocations.get(id);
		return switch (loc.getType()) {
			case CASUAL -> new CasualBase(loc);
			case STAINED -> new StainedBase((StainedBaseLocation) loc);
			case SIEGE -> new SiegeBase((SiegeBaseLocation) loc);
		};
	}

	public void capture(int id, BaseOccupier newOccupier) {
		if (!isActive(id))
			return;

		stop(id);

		BaseLocation loc = allBaseLocations.get(id);

		if (newOccupier != null)
			loc.setOccupier(newOccupier);

		start(id);

		// Broadcast conquest message to the world map
		if (newOccupier != null && newOccupier != BaseOccupier.BALAUR) {
			Base<?> newBase = activeBases.get(id);
			if (newBase != null) {
				int worldId = loc.getWorldId();
				WorldMapInstance mapInstance = World.getInstance().getWorldMap(worldId).getMainWorldMapInstance();
				if (mapInstance != null) {
					String raceName = newOccupier == BaseOccupier.ELYOS ? "Elyos" : "Asmodians";
					String baseName = "Base " + id;
					PacketSendUtility.broadcastToMap(mapInstance,
						SM_SYSTEM_MESSAGE.STR_CAMP_GUILD_WIN_FORT(raceName, "", baseName));
				}
			}
		}

		if (loc instanceof StainedBaseLocation coloredLoc)
			handleStainedFeatures(coloredLoc.getColor(), newOccupier);
	}

	private void handleStainedFeatures(BaseColorType colorType, BaseOccupier newOccupier) {
		List<StainedBase> spec = activeBases.values().stream().filter(base -> base instanceof StainedBase sb && sb.getColor() == colorType)
			.map(base -> (StainedBase) base).toList();

		long equalBases = spec.stream().filter(base -> base.getOccupier() == newOccupier).count();
		if (newOccupier == BaseOccupier.BALAUR || equalBases < 3) {
			spec.forEach(StainedBase::deactivateEnhancedSpawns);
		} else {
			spec.forEach(StainedBase::scheduleEnhancedSpawns);
		}
	}

	public Collection<BaseLocation> getBaseLocations() {
		return allBaseLocations.values();
	}

	public Base<?> getActiveBase(int id) {
		return activeBases.get(id);
	}

	public BaseLocation getBaseLocation(int id) {
		return allBaseLocations.get(id);
	}

	public boolean isActive(int id) {
		return activeBases.containsKey(id);
	}

	public static BaseService getInstance() {
		return INSTANCE;
	}
}
