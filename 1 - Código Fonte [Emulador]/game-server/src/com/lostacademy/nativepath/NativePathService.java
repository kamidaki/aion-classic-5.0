package com.lostacademy.nativepath;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.Creature;

/**
 * Ponto de entrada e fachada pública de consultas de navegação CryEngine (native-path).
 *
 * @author KAMIDAKI
 */
public final class NativePathService {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathService.class);

	private final NativePathData data = NativePathData.getInstance();

	public static final AtomicLong totalQueries = new AtomicLong(0);
	public static final AtomicLong totalQueryTimeNs = new AtomicLong(0);
	public static final AtomicInteger queriesInFlight = new AtomicInteger(0);
	public static final AtomicLong lastQueryTimeNs = new AtomicLong(0);

	private static final AtomicLong queriesInLastSecond = new AtomicLong(0);
	private static volatile double queriesPerSecond = 0.0;
	private static volatile long lastQpsResetTime = System.currentTimeMillis();

	public static synchronized double getQueriesPerSecond() {
		long now = System.currentTimeMillis();
		long delta = now - lastQpsResetTime;
		if (delta >= 1000) {
			queriesPerSecond = (double) queriesInLastSecond.getAndSet(0) / (delta / 1000.0);
			lastQpsResetTime = now;
		}
		return queriesPerSecond;
	}

	private static void recordQuery(long startTimeNs) {
		queriesInFlight.decrementAndGet();
		long duration = System.nanoTime() - startTimeNs;
		totalQueryTimeNs.addAndGet(duration);
		lastQueryTimeNs.set(duration);
	}

	private NativePathService() {
	}

	public void initialize() {
		if (!NativePathConfig.NATIVE_PATH_ENABLE) {
			LOG.info("NATIVE_PATH: Subsistema desativado por configuração.");
			return;
		}
		LOG.info("NATIVE_PATH: Subsistema CryEngine habilitado. Malhas de 185 mapas prontas para carregamento sob demanda.");
	}

	public boolean hasMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return false;
		return data.hasMap(worldId);
	}

	public boolean canPullTarget(Creature creature, Creature target) {
		long start = System.nanoTime();
		queriesInFlight.incrementAndGet();
		totalQueries.incrementAndGet();
		queriesInLastSecond.incrementAndGet();

		try {
			if (!NativePathConfig.NATIVE_PATH_ENABLE)
				return true;
			if (creature == null || target == null)
				return true;

			int worldId = creature.getWorldId();
			if (target.isFlying() || creature.isFlying())
				return true;

			NativePathMap map = data.getNativeMap(worldId);
			if (map == null) {
				return true; // Sem mapa nativo: delega ao fallback
			}

			float x1 = creature.getX(), y1 = creature.getY(), z1 = creature.getZ();
			float x2 = target.getX(), y2 = target.getY(), z2 = target.getZ();

			return map.hasLineOfSight(x1, y1, z1, x2, y2, z2, 2.5f);
		} finally {
			recordQuery(start);
		}
	}

	public float[][] navigateToTarget(Creature pathOwner, Creature target) {
		long start = System.nanoTime();
		queriesInFlight.incrementAndGet();
		totalQueries.incrementAndGet();
		queriesInLastSecond.incrementAndGet();

		try {
			if (!NativePathConfig.NATIVE_PATH_ENABLE)
				return null;
			if (pathOwner == null || target == null)
				return null;
			if (pathOwner.getLifeStats().isDead())
				return null;
			if (pathOwner.getWorldId() != target.getWorldId())
				return null;

			int worldId = pathOwner.getWorldId();

			NativePathMap map = data.getNativeMap(worldId);
			if (map == null)
				return null;

			float x1 = pathOwner.getX(), y1 = pathOwner.getY(), z1 = pathOwner.getZ();
			float x2 = target.getX(), y2 = target.getY(), z2 = target.getZ();

			float[][] path = NativePathAStar.findPath(map, x1, y1, z1, x2, y2, z2);
			if (NativePathConfig.NATIVE_PATH_DEBUG) {
				if (path != null) {
					LOG.info("NATIVE_PATH [TARGET]: [{}] ({}, {}, {}) -> ({}, {}, {}) | {} waypoints",
						pathOwner.getName(), x1, y1, z1, x2, y2, z2, path.length);
				} else {
					LOG.debug("NATIVE_PATH [TARGET]: [{}] No path from ({}, {}, {}) to ({}, {}, {})",
						pathOwner.getName(), x1, y1, z1, x2, y2, z2);
				}
			}
			return path;
		} finally {
			recordQuery(start);
		}
	}

	public float[][] navigateToLocation(Creature pathOwner, float x, float y, float z) {
		long start = System.nanoTime();
		queriesInFlight.incrementAndGet();
		totalQueries.incrementAndGet();
		queriesInLastSecond.incrementAndGet();

		try {
			if (!NativePathConfig.NATIVE_PATH_ENABLE)
				return null;
			if (pathOwner == null)
				return null;
			if (pathOwner.getLifeStats().isDead())
				return null;

			int worldId = pathOwner.getWorldId();

			NativePathMap map = data.getNativeMap(worldId);
			if (map == null)
				return null;

			float x1 = pathOwner.getX(), y1 = pathOwner.getY(), z1 = pathOwner.getZ();

			float[][] path = NativePathAStar.findPath(map, x1, y1, z1, x, y, z);
			if (NativePathConfig.NATIVE_PATH_DEBUG) {
				if (path != null) {
					LOG.info("NATIVE_PATH [LOC]: [{}] ({}, {}, {}) -> ({}, {}, {}) | {} waypoints",
						pathOwner.getName(), x1, y1, z1, x, y, z, path.length);
				} else {
					LOG.debug("NATIVE_PATH [LOC]: [{}] No path from ({}, {}, {}) to ({}, {}, {})",
						pathOwner.getName(), x1, y1, z1, x, y, z);
				}
			}
			return path;
		} finally {
			recordQuery(start);
		}
	}

	public float getSurfaceZ(int worldId, float x, float y, float z) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return Float.NaN;

		NativePathMap map = data.getNativeMap(worldId);
		if (map == null)
			return Float.NaN;

		return map.getSurfaceZ(x, y, z);
	}

	public boolean isWalkable(int worldId, float x, float y, float z) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return false;

		NativePathMap map = data.getNativeMap(worldId);
		if (map == null)
			return false;

		return map.isWalkable(x, y, z, 2.5f);
	}

	public static NativePathService getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private static final class SingletonHolder {
		static final NativePathService INSTANCE = new NativePathService();
	}
}
