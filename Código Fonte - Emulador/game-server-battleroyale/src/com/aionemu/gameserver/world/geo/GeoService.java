package com.aionemu.gameserver.world.geo;

import java.util.HashMap;
import java.util.Map;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.ai.poll.AIQuestion;
import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.geoEngine.GeoWorldLoader;
import com.aionemu.gameserver.geoEngine.collision.CollisionIntention;
import com.aionemu.gameserver.geoEngine.collision.CollisionResults;
import com.aionemu.gameserver.geoEngine.collision.IgnoreProperties;
import com.aionemu.gameserver.geoEngine.math.Vector3f;
import com.aionemu.gameserver.geoEngine.models.GeoMap;
import com.aionemu.gameserver.model.GameEngine;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.house.HouseDoorState;
import com.aionemu.gameserver.model.templates.npc.NpcTemplate;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.world.WorldMapType;
import com.aionemu.gameserver.world.WorldPosition;

/**
 * @author Lost Academy Team & Durak
 */
public class GeoService implements GameEngine {

	private final Map<Integer, GeoMap> geoMaps = new HashMap<>();

	@Override
	public void init() {
		DataManager.WORLD_MAPS_DATA.forEach(map -> geoMaps.put(map.getMapId(), new GeoMap(map.getMapId())));
		if (GeoDataConfig.GEO_ENABLE) {
			GeoWorldLoader.load(geoMaps.values());
		} else {
			LoggerFactory.getLogger(GeoService.class).warn("Geo data is disabled");
		}
	}

	/**
	 * @return The surface Z coordinate at the objects position, nearest to the given zMax value at the given position or {@link Float#NaN} if not found
	 *         / less than zMin.
	 */
	public float getZ(VisibleObject object, float zMax, float zMin) {
		return getZ(object.getWorldId(), object.getX(), object.getY(), zMax, zMin, object.getInstanceId());
	}

	/**
	 * @return The surface Z coordinate nearest to the given Z value at the given position or {@link Float#NaN} if not found.
	 */
	public float getZ(int worldId, float x, float y, float z, int instanceId) {
		return getZ(worldId, x, y, z + 2, z - 2, instanceId);
	}

	/**
	 * @return The surface Z coordinate nearest to the given zMax value at the given position or {@link Float#NaN} if not found / less than zMin.
	 */
	public float getZ(int worldId, float x, float y, float zMax, float zMin, int instanceId) {
		GeoMap map = geoMaps.get(worldId);
		return map == null ? Float.NaN : map.getZ(x, y, zMax, zMin, instanceId);
	}

	public float getZ(int worldId, float x, float y) {
		GeoMap map = geoMaps.get(worldId);
		if (map == null)
			return 0;
		return map.getZ(x, y);
	}

	/**
	 * @return z of the terrain heightmap only (no meshes) at x/y, NaN without terrain. Used by the path.dat grid for cells that inherit the
	 *         terrain height.
	 */
	public float getTerrainHeight(int worldId, float x, float y) {
		GeoMap map = geoMaps.get(worldId);
		return map == null ? Float.NaN : map.getTerrainHeight(x, y);
	}

	/**
	 * Resolves valid ground height near currentZ using expanding vertical search windows.
	 * Avoids shooting from sky (4000) which hits ceilings/roofs, while tolerating spawn elevation errors.
	 */
	public float getValidGroundZ(int worldId, float x, float y, float currentZ, int instanceId) {
		GeoMap map = geoMaps.get(worldId);
		if (map == null)
			return Float.NaN;

		// 1. Janela imediata (+2m / -3m)
		float z = map.getZ(x, y, currentZ + 2.0f, currentZ - 3.0f, instanceId);
		if (!Float.isNaN(z))
			return z;

		// 2. Janela intermediaria (+6m / -10m)
		z = map.getZ(x, y, currentZ + 6.0f, currentZ - 10.0f, instanceId);
		if (!Float.isNaN(z))
			return z;

		// 3. Janela ampla (+15m / -25m) para relevos acidentados e rampas
		z = map.getZ(x, y, currentZ + 15.0f, currentZ - 25.0f, instanceId);
		if (!Float.isNaN(z))
			return z;

		// 4. Fallback apenas se currentZ for zero ou proximo de zero
		if (currentZ <= 0.1f) {
			return map.getZ(x, y, 4000, 0, instanceId);
		}
		return Float.NaN;
	}

	public CollisionResults getCollisions(VisibleObject object, float x, float y, float z, byte intentions, IgnoreProperties ignoreProperties) {
		GeoMap map = geoMaps.get(object.getWorldId());
		return map == null ? null : map.getCollisions(object.getX(), object.getY(), object.getZ() + getSeeCheckOffset(object), x, y, z,
			object.getInstanceId(), intentions, ignoreProperties);
	}

	/**
	 * @return True if object has unobstructed view on its target.
	 */
	public boolean canSee(VisibleObject object, VisibleObject target) {
		if (!GeoDataConfig.CANSEE_ENABLE)
			return true;

		GeoMap map = geoMaps.get(object.getWorldId());
		if (map == null)
			return true;

		float objectSeeCheckZ = object.getZ() + getSeeCheckOffset(object);
		float targetSeeCheckZ = target.getZ() + getSeeCheckOffset(target);
		float x = object.getX();
		float y = object.getY();
		float targetX = target.getX();
		float targetY = target.getY();
		if (object instanceof Npc npc && npc.getAi().ask(AIQuestion.CONSIDER_BOUNDS_IN_CAN_SEE_CHECK_WHEN_ATTACKING)) {
			double rad = Math.toRadians(PositionUtil.calculateAngleFrom(object, target));
			x += (float) (Math.cos(rad) * object.getObjectTemplate().getBoundRadius().getMaxOfFrontAndSide());
			y += (float) (Math.sin(rad) * object.getObjectTemplate().getBoundRadius().getMaxOfFrontAndSide());
		}
		if (target instanceof Npc npc && npc.getAi().ask(AIQuestion.CONSIDER_BOUNDS_IN_CAN_SEE_CHECK_WHEN_ATTACKED)) {
			double rad = Math.toRadians(PositionUtil.calculateAngleFrom(target, object));
			targetX += (float) (Math.cos(rad) * target.getObjectTemplate().getBoundRadius().getMaxOfFrontAndSide());
			targetY += (float) (Math.sin(rad) * target.getObjectTemplate().getBoundRadius().getMaxOfFrontAndSide());
		}
		Race race = null;
		int staticId = -1;
		if (target.getSpawn() != null) {
			staticId = target.getSpawn().getStaticId();
		}
		if (object instanceof Creature creature) {
			race = creature.getRace();
		}
		IgnoreProperties ignoreProperties = IgnoreProperties.of(race, staticId);
		return map.canSee(x, y, objectSeeCheckZ, targetX, targetY, targetSeeCheckZ, object.getInstanceId(), ignoreProperties);
	}

	public boolean canSee(VisibleObject object, float targetX, float targetY, float targetZ, IgnoreProperties ignoreProperties) {
		GeoMap map = geoMaps.get(object.getWorldId());
		if (map == null)
			return true;
		float zOffset = getSeeCheckOffset(object);
		return map.canSee(object.getX(), object.getY(), object.getZ() + zOffset, targetX, targetY, targetZ + zOffset,
			object.getInstanceId(), ignoreProperties);
	}

	public boolean canPass(VisibleObject object, VisibleObject target) {
		float limit = (float) (PositionUtil.getDistance(object, target) - target.getObjectTemplate().getBoundRadius().getCollision());
		if (limit <= 0)
			return true;

		float upperTarget = target.getObjectTemplate().getBoundRadius().getUpper() / 2;
		if (upperTarget > 2.2f)
			upperTarget = 2.2f;

		float objectUp = object.getObjectTemplate().getBoundRadius().getUpper() / 2;
		if (object instanceof Player)
			objectUp = 1.5f;
		else if (target instanceof Player)
			upperTarget = 1.5f;

		return canPass(object.getWorldId(), object.getX(), object.getY(),
				object.getZ() + objectUp, target.getX(), target.getY(),
				target.getZ() + upperTarget, limit, object.getInstanceId());
	}

	public boolean canPass(int worldId, float x, float y, float z, float x1, float y1, float z1, float limit, int instanceId) {
		GeoMap map = geoMaps.get(worldId);
		if (map == null)
			return true;
		return map.canPass(x, y, z, x1, y1, z1, limit, instanceId);
	}

	public boolean hasPhysicalGeometries(int worldId, float x, float y) {
		GeoMap map = geoMaps.get(worldId);
		return map != null && map.hasPhysicalGeometries(x, y);
	}

	public boolean canPassPhysical(int worldId, float x, float y, float z, float x1, float y1, float z1, float limit, int instanceId) {
		GeoMap map = geoMaps.get(worldId);
		if (map == null)
			return true;
		return map.canPassPhysical(x, y, z, x1, y1, z1, limit, instanceId);
	}

	private float getSeeCheckOffset(VisibleObject object) {
		float height = object.getObjectTemplate().getBoundRadius().getUpper();
		if (object instanceof Player p && p.isTransformed() && p.getTransformModel().cantMove()) {
			NpcTemplate t = DataManager.NPC_DATA.getNpcTemplate(p.getTransformModel().getModelId());
			if (t != null)
				return t.getBoundRadius().getUpper();
		}
		return height > 2.5f ? height / 2 : 1.25f;
	}

	public Vector3f getClosestCollision(Creature object, float x, float y, float z) {
		return getClosestCollision(object, x, y, z, true, CollisionIntention.DEFAULT_COLLISIONS.getId(), IgnoreProperties.ANY_RACE);
	}

	public Vector3f getClosestCollision(Creature object, float x, float y, float z, boolean atNearGroundZ, byte intentions, IgnoreProperties ignoreProperties) {
		return geoMaps.get(object.getWorldId()).getClosestCollision(object.getX(), object.getY(), object.getZ(), x, y, z, atNearGroundZ,
			object.getInstanceId(), intentions, ignoreProperties);
	}

	/**
	 * Terrain agnostic check. It will move along the terrain and only return collisions which are actual obstacles, like trees, walls or steep hills.
	 * Inclines <= 45° will not be considered as collisions.
	 * On steep slopes and cliffs it'll return the position nearest to where you can still walk.
	 */
	public Vector3f findMovementCollision(Creature creature, float directionAngle, float maxDistance) {
		double rad = Math.toRadians(directionAngle);
		float x1 = (float) (Math.cos(rad) * maxDistance);
		float y1 = (float) (Math.sin(rad) * maxDistance);
		Vector3f startPos;
		GeoMap map = geoMaps.get(creature.getWorldId());
		if (creature instanceof Player player) {
			startPos = calculateCurrentGeoPosition(player);
			if (creature.isFlying())
				return map.getClosestCollision(startPos.getX(), startPos.getY(), startPos.getZ(), startPos.getX() + x1, startPos.getY() + y1,
					startPos.getZ(), false, creature.getInstanceId(), CollisionIntention.DEFAULT_COLLISIONS.getId(), IgnoreProperties.ANY_RACE);
		} else
			startPos = new Vector3f(creature.getX(), creature.getY(), creature.getZ());
		return map.findMovementCollision(startPos, startPos.getX() + x1, startPos.getY() + y1, creature.getInstanceId());
	}

	private Vector3f calculateCurrentGeoPosition(Player player) {
		WorldPosition approximatePos = player.getPosition();
		WorldPosition lastPos = player.getMoveController().getLastPositionFromClient();
		if (lastPos == null)
			return new Vector3f(approximatePos.getX(), approximatePos.getY(), approximatePos.getZ());
		GeoMap geoMap = geoMaps.get(approximatePos.getMapId());
		if (geoMap == null)
			return new Vector3f(approximatePos.getX(), approximatePos.getY(), approximatePos.getZ());
		// client sends CM_MOVE in intervals when moving straight, so we search for possible collisions between lastPos and the server side position
		return geoMap.getClosestCollision(lastPos.getX(), lastPos.getY(), lastPos.getZ(), approximatePos.getX(),
			approximatePos.getY(), approximatePos.getZ(), true, approximatePos.getInstanceId(), CollisionIntention.DEFAULT_COLLISIONS.getId(),
			IgnoreProperties.ANY_RACE);
	}

	public void spawnPlaceableObject(int worldId, int instanceId, int staticId) {
		GeoMap geoMap = geoMaps.get(worldId);
		if (geoMap != null)
			geoMap.spawnPlaceableObject(instanceId, staticId);
	}

	public void despawnPlaceableObject(int worldId, int instanceId, int staticId) {
		GeoMap geoMap = geoMaps.get(worldId);
		if (geoMap != null)
			geoMap.despawnPlaceableObject(instanceId, staticId);
	}

	public void updateTown(Race race, int townId, int level) {
		int worldId = race == Race.ELYOS ? WorldMapType.ORIEL.getId() : WorldMapType.PERNON.getId();
		GeoMap geoMap = geoMaps.get(worldId);
		if (geoMap != null)
			geoMap.updateTownToLevel(townId, level);
	}

	public void setHouseDoorState(int worldId, int instanceId, int houseAddress, HouseDoorState state) {
		GeoMap geoMap = geoMaps.get(worldId);
		if (geoMap != null)
			geoMap.setHouseDoorState(instanceId, houseAddress, state);
	}

	public void setDoorState(int worldId, int instanceId, int doorId, boolean open) {
		GeoMap geoMap = geoMaps.get(worldId);
		if (geoMap != null)
			geoMap.setDoorState(instanceId, doorId, open);
	}

	public boolean worldHasTerrainMaterials(int worldId) {
		GeoMap geoMap = geoMaps.get(worldId);
		return GeoDataConfig.GEO_MATERIALS_ENABLE && geoMap != null && geoMap.hasTerrainMaterials();
	}

	public int getTerrainMaterialAt(int worldId, float x, float y, float z, int instanceId) {
		GeoMap geoMap = geoMaps.get(worldId);
		return (GeoDataConfig.GEO_MATERIALS_ENABLE && geoMap != null) ? geoMap.getTerrainMaterialAt(x, y, z, instanceId) : 0;
	}

	public static GeoService getInstance() {
		return SingletonHolder.instance;
	}

	private static final class SingletonHolder {

		protected static final GeoService instance = new GeoService();
	}
}
