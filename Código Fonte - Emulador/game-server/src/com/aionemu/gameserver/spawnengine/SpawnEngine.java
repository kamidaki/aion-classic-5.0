package com.aionemu.gameserver.spawnengine;

import java.util.List;
import java.util.function.Consumer;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Gatherable;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.siege.SiegeModType;
import com.aionemu.gameserver.model.siege.SiegeRace;
import com.aionemu.gameserver.model.templates.event.EventTemplate;
import com.aionemu.gameserver.model.templates.spawns.SpawnGroup;
import com.aionemu.gameserver.model.templates.spawns.SpawnTemplate;
import com.aionemu.gameserver.model.templates.spawns.riftspawns.RiftSpawnTemplate;
import com.aionemu.gameserver.model.templates.spawns.siegespawns.SiegeSpawnTemplate;
import com.aionemu.gameserver.model.templates.spawns.vortexspawns.VortexSpawnTemplate;
import com.aionemu.gameserver.services.rift.RiftManager;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldMap;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * @author Lost Academy Team & Durak
 */
public class SpawnEngine {

	private static final Logger log = LoggerFactory.getLogger(SpawnEngine.class);

	public static VisibleObject spawnObject(SpawnTemplate spawn, int instanceIndex) {
		VisibleObject visObj = getSpawnedObject(spawn, instanceIndex);
		if (visObj != null) {
			if (visObj.getSpawn() != null && visObj.getSpawn().isTemporarySpawn())
				TemporarySpawnEngine.registerSpawned(visObj);
			if (visObj.isSpawned()) // WalkerFormator.processClusteredNpc delays spawn of pooled walkers
				visObj.getPosition().getWorldMapInstance().getInstanceHandler().onSpawn(visObj);
		}
		return visObj;
	}

	private static VisibleObject getSpawnedObject(SpawnTemplate spawn, int instanceIndex) {
		int npcId = spawn.getNpcId();

		if (npcId > 400000 && npcId < 499999) {
			return VisibleObjectSpawner.spawnGatherable(spawn, instanceIndex);
		} else if (spawn instanceof RiftSpawnTemplate) {
			return VisibleObjectSpawner.spawnRiftNpc((RiftSpawnTemplate) spawn, instanceIndex);
		} else if (spawn instanceof SiegeSpawnTemplate) {
			return VisibleObjectSpawner.spawnSiegeNpc((SiegeSpawnTemplate) spawn, instanceIndex);
		} else if (spawn instanceof VortexSpawnTemplate) {
			return VisibleObjectSpawner.spawnInvasionNpc((VortexSpawnTemplate) spawn, instanceIndex);
		} else {
			return VisibleObjectSpawner.spawnNpc(spawn, instanceIndex);
		}
	}

	/**
	 * Create non-permanent spawn template with no respawn
	 */
	public static SpawnTemplate newSingleTimeSpawn(int worldId, int npcId, float x, float y, float z, byte heading) {
		return newSpawn(worldId, npcId, x, y, z, heading, 0, 0, null, null);
	}

	public static SpawnTemplate newSingleTimeSpawn(int worldId, int npcId, float x, float y, float z, byte heading, VisibleObject creator, String aiName) {
		int creatorId = creator == null ? 0 : creator.getObjectId();
		EventTemplate eventTemplate = creator == null || creator.getSpawn() == null ? null : creator.getSpawn().getEventTemplate();
		return newSpawn(worldId, npcId, x, y, z, heading, 0, creatorId, aiName, eventTemplate);
	}

	public static SpawnTemplate newSingleTimeSpawn(int worldId, int npcId, float x, float y, float z, byte heading, int creatorId) {
		return newSpawn(worldId, npcId, x, y, z, heading, 0, creatorId, null, null);
	}

	public static SpawnTemplate newSpawn(int worldId, int npcId, float x, float y, float z, byte heading, int respawnTime) {
		return newSpawn(worldId, npcId, x, y, z, heading, respawnTime, 0, null, null);
	}

	private static SpawnTemplate newSpawn(int worldId, int npcId, float x, float y, float z, byte heading, int respawnTime, int creatorId,
			String aiName, EventTemplate eventTemplate) {
		return new SpawnTemplate(new SpawnGroup(worldId, npcId, respawnTime, eventTemplate), x, y, z, heading, 0, null, 0, creatorId, aiName);
	}

	/**
	 * Should be used when you need to add a siegespawn through code and not from static_data spawns (e.g. CustomBalaurAssault)
	 */
	public static SiegeSpawnTemplate newSiegeSpawn(int worldId, int npcId, int siegeId, SiegeRace race, SiegeModType mod, float x, float y, float z,
		byte heading) {
		return new SiegeSpawnTemplate(siegeId, race, mod, new SpawnGroup(worldId, npcId, 0, null), x, y, z, heading, 0, null, 0);
	}

	/**
	 * Resolves the authoritative ground/walkable Z coordinate for a ground NPC spawn at (x, y) near referenceZ.
	 * Uses active NavMesh triangle plane interpolation first, then GeoEngine collision raycasting within a safe vertical window
	 * so NPCs do not spawn embedded underground or floating above terrain/floors.
	 */
	public static float resolveSpawnGroundZ(int worldId, float x, float y, float referenceZ, int instanceIndex) {
		float navZ = com.lostacademy.nav.NavService.getInstance().getNavSurfaceZ(worldId, x, y, referenceZ);
		if (!Float.isNaN(navZ)) {
			float diff = navZ - referenceZ;
			// Correct embedded spawns (up to 6m underground) or floating spawns (up to 5m above surface)
			if (diff >= -5.0f && diff <= 6.0f) {
				return navZ;
			}
		}
		if (com.aionemu.gameserver.configs.main.GeoDataConfig.GEO_ENABLE) {
			float geoZ = com.aionemu.gameserver.world.geo.GeoService.getInstance().getValidGroundZ(worldId, x, y, referenceZ, instanceIndex);
			if (!Float.isNaN(geoZ)) {
				float diff = geoZ - referenceZ;
				if (diff >= -5.0f && diff <= 6.0f) {
					return geoZ;
				}
			}
		}
		return referenceZ;
	}

	private static boolean shouldValidateGroundSpawnZ(VisibleObject visibleObject, SpawnTemplate spawn) {
		if (!(visibleObject instanceof Npc npc)) {
			return false;
		}
		if (visibleObject instanceof com.aionemu.gameserver.model.gameobjects.StaticDoor) {
			return false;
		}
		if (npc.isFlying()) {
			return false;
		}
		if (spawn != null && spawn.isAerialSpawn()) {
			return false;
		}
		return true;
	}

	static void bringIntoWorld(VisibleObject visibleObject, SpawnTemplate spawn, int instanceIndex) {
		float spawnZ = spawn.getZ();
		if (shouldValidateGroundSpawnZ(visibleObject, spawn)) {
			float resolvedZ = resolveSpawnGroundZ(spawn.getWorldId(), spawn.getX(), spawn.getY(), spawnZ, instanceIndex);
			if (!Float.isNaN(resolvedZ) && Math.abs(resolvedZ - spawnZ) >= 0.05f) {
				spawnZ = resolvedZ;
				spawn.setZ(resolvedZ);
			}
		}
		bringIntoWorld(visibleObject, spawn.getWorldId(), instanceIndex, spawn.getX(), spawn.getY(), spawnZ, spawn.getHeading());
	}

	public static void bringIntoWorld(VisibleObject visibleObject, int worldId, int instanceIndex, float x, float y, float z, byte h) {
		float effectiveZ = z;
		if (shouldValidateGroundSpawnZ(visibleObject, visibleObject.getSpawn())) {
			float resolvedZ = resolveSpawnGroundZ(worldId, x, y, z, instanceIndex);
			if (!Float.isNaN(resolvedZ) && Math.abs(resolvedZ - z) >= 0.05f) {
				effectiveZ = resolvedZ;
				if (visibleObject.getSpawn() != null) {
					visibleObject.getSpawn().setZ(resolvedZ);
				}
			}
		}
		World world = World.getInstance();
		world.storeObject(visibleObject);
		world.setPosition(visibleObject, worldId, instanceIndex, x, y, effectiveZ, h);
		world.spawn(visibleObject);
	}

	public static void bringIntoWorld(VisibleObject visibleObject) {
		if (visibleObject.getPosition() == null)
			throw new IllegalArgumentException("Position is null");
		World world = World.getInstance();
		world.storeObject(visibleObject);
		world.spawn(visibleObject);
	}

	/**
	 * Spawn all NPCs from templates
	 */
	public static void spawnAll() {
		DataManager.WORLD_MAPS_DATA.forEachParalllel(worldMapTemplate -> {
			WorldMap worldMap = World.getInstance().getWorldMap(worldMapTemplate.getMapId());
			if (!worldMap.isInstanceType())
				worldMap.forEach(instance -> spawnInstance(instance, (byte) 0, instance.getOwnerId()));
		});
		printWorldSpawnStats();
	}

	public static void spawnInstance(WorldMapInstance instance, byte difficultId, int ownerId) {
		spawnInstance(instance, difficultId, ownerId, null);
	}

	public static void spawnEventSpawns(WorldMapInstance instance, byte difficultId, int ownerId, EventTemplate eventTemplate) {
		spawnInstance(instance, difficultId, ownerId, eventTemplate);
	}

	private static void spawnInstance(WorldMapInstance instance, byte difficultId, int ownerId, EventTemplate eventTemplate) {
		List<SpawnGroup> worldSpawns = DataManager.SPAWNS_DATA.getSpawnsByWorldId(instance.getMapId());
		if (eventTemplate == null)
			StaticDoorSpawnManager.spawnTemplate(instance);

		int spawnedCounter = 0;
		if (worldSpawns != null) {
			for (SpawnGroup spawn : worldSpawns) {
				if (eventTemplate != null && eventTemplate != spawn.getEventTemplate())
					continue;
				if (spawn.getDifficultId() != 0 && spawn.getDifficultId() != difficultId)
					continue;

				if (spawn.isTemporarySpawn()) {
					TemporarySpawnEngine.addSpawnGroup(spawn, instance.getInstanceId());
					if (!spawn.getTemporarySpawn().isInSpawnTime())
						continue;
				}

				if (spawn.getHandlerType() != null) {
					switch (spawn.getHandlerType()) {
						case RIFT -> RiftManager.addRiftSpawnTemplate(spawn);
						case STATIC -> StaticObjectSpawnManager.spawnTemplate(spawn, instance.getInstanceId());
					}
				} else if (spawn.hasPool() && checkPool(spawn)) {
					spawn.resetPoolSpots(instance.getInstanceId());
					for (int i = 0; i < spawn.getPool(); i++) {
						SpawnTemplate template = spawn.reserveRandomFreePoolSpot(instance.getInstanceId());
						if (template == null)
							break;
						if (spawnObject(template, instance.getInstanceId()) != null)
							spawnedCounter++;
					}
				} else {
					for (SpawnTemplate template : spawn.getSpawnTemplates()) {
						if (template.getTemporarySpawn() != null && !template.getTemporarySpawn().isInSpawnTime())
							continue;
						if (spawnObject(template, instance.getInstanceId()) != null)
							spawnedCounter++;
					}
				}
			}
			if (eventTemplate == null)
				WalkerFormator.organizeAndSpawn(instance.getMapId(), instance.getInstanceId());
		}
		if (spawnedCounter > 0) {
			if (eventTemplate == null)
				log.info("Spawned " + spawnedCounter + " objects in " + instance);
			else
				log.info('[' + eventTemplate.getName() + "] Spawned " + spawnedCounter + " event objects in " + instance);
		}
		// Sem casas no mundo: o Classic 5.0 não tem housing. O Game.dll não tem nenhum pacote S de casa (só os de warehouse) e o
		// client_housing_land.xml só traz 4 terrenos de teste; os endereços do HOUSE_DATA são da 4.8. Com eles a casa (e o mordomo) entrava
		// no knownlist em Heiron e o SM_HOUSE_RENDER/SM_DELETE_HOUSE/SM_HOUSE_SCRIPTS estourava "There is no opcode" (20/10).
	}

	public static boolean checkPool(SpawnGroup spawn) {
		if (spawn.getPool() >= spawn.getSpawnTemplates().size()) {
			log.warn("Spawn pool size must be smaller than spots to take effect, npcId: " + spawn.getNpcId() + ", worldId: " + spawn.getWorldId());
			return false;
		}
		return true;
	}

	public static void printWorldSpawnStats() {
		StatsCollector function = new StatsCollector();
		World.getInstance().forEachObject(function);
		log.info("Loaded " + function.getNpcCount() + " npc spawns");
		log.info("Loaded " + function.getGatherableCount() + " gatherable spawns");
	}

	static class StatsCollector implements Consumer<VisibleObject> {

		int npcCount;
		int gatherableCount;

		@Override
		public void accept(VisibleObject object) {
			if (object instanceof Npc) {
				npcCount++;
			} else if (object instanceof Gatherable) {
				gatherableCount++;
			}
		}

		public int getNpcCount() {
			return npcCount;
		}

		public int getGatherableCount() {
			return gatherableCount;
		}

	}

}
