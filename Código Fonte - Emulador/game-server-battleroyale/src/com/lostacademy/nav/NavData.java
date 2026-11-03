package com.lostacademy.nav;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.Map;
import java.util.StringJoiner;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.aionemu.gameserver.geoEngine.models.GeoMap;
import com.aionemu.gameserver.geoEngine.scene.NavGeometry;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.WorldMapType;

/**
 * Sistema de gerenciamento de NavMeshes com cache LRU e liberação de memória.
 *
 * @author KAMIDAKI
 */
public class NavData {

	private static final Logger LOG = LoggerFactory.getLogger(NavData.class);

	// Configurações do cache
	private static final int MAX_CACHED_MAPS = 15;
	private static final long INACTIVE_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutos
	private static final long CLEANUP_INTERVAL_MS = 3 * 60 * 1000; // 3 minutos

	// Cache thread-safe baseado em ConcurrentHashMap (sem ReadWriteLock para prevenir contenção e loops cíclicos)
	private final ConcurrentHashMap<Integer, CachedGeoMap> navMaps;
	public final AtomicLong totalCacheSizeMB = new AtomicLong(0);

	public final AtomicLong cacheHits = new AtomicLong(0);
	public final AtomicLong cacheMisses = new AtomicLong(0);
	public final AtomicLong totalLoadTimeMs = new AtomicLong(0);
	public final AtomicLong loadedCount = new AtomicLong(0);

	// Rastreamento de atividade
	private final ConcurrentHashMap<Integer, MapActivity> mapActivity = new ConcurrentHashMap<>();

	// Thread pool
	private final ThreadPoolManager threadPoolManager = ThreadPoolManager.getInstance();

	private NavData() {
		this.navMaps = new ConcurrentHashMap<>();
		startCleanupScheduler();
	}

	public void onPlayerEnterMap(int worldId) {
		if (!GeoDataConfig.GEO_NAV_ENABLE)
			return;


		MapActivity activity = getOrCreateActivity(worldId);
		activity.incrementPlayerCount();

		if (!navMaps.containsKey(worldId)) {
			loadNavMapAsync(worldId);
		}
	}

	public void onPlayerLeaveMap(int worldId) {

		MapActivity activity = mapActivity.get(worldId);
		if (activity != null) {
			activity.decrementPlayerCount();
		}
	}

	public GeoMap getNavMap(int worldId) {
		if (!GeoDataConfig.GEO_NAV_ENABLE)
			return null;


		MapActivity activity = mapActivity.get(worldId);
		if (activity == null || activity.getPlayerCount() <= 0) {
			// Sem jogadores no mapa: apenas retorna se já estiver no cache, NUNCA carrega do disco
			CachedGeoMap cached = navMaps.get(worldId);
			return cached != null ? cached.geoMap : null;
		}

		activity.updateLastAccess();
		return loadNavMapIfAbsent(worldId);
	}

	private GeoMap loadNavMapIfAbsent(int worldId) {
		CachedGeoMap cached = navMaps.get(worldId);
		if (cached != null) {
			cached.updateAccess();
			cacheHits.incrementAndGet();
			return cached.geoMap;
		}

		synchronized (navMaps) {
			cached = navMaps.get(worldId);
			if (cached != null) {
				cached.updateAccess();
				cacheHits.incrementAndGet();
				return cached.geoMap;
			}

			cacheMisses.incrementAndGet();
			long startTime = System.currentTimeMillis();

			GeoMap geoMap = loadNavFromDisk(worldId);
			if (geoMap == null) {
				return null;
			}
			long loadTime = System.currentTimeMillis() - startTime;
			totalLoadTimeMs.addAndGet(loadTime);
			loadedCount.incrementAndGet();

			CachedGeoMap cachedGeoMap = new CachedGeoMap(geoMap, worldId);
			navMaps.put(worldId, cachedGeoMap);
			totalCacheSizeMB.addAndGet(cachedGeoMap.getEstimatedSizeMB());
			LOG.info("Nav Data: mapa {} carregado. Mapas em Cache: {}",
				formatWorldName(worldId), describeCachedMaps());

			evictEldestIfNeeded();

			return geoMap;
		}
	}

	private void loadNavMapAsync(int worldId) {
		CompletableFuture.runAsync(() -> {
			try {
				loadNavMapIfAbsent(worldId);
			} catch (Exception e) {
				LOG.error("NAVMESH: Erro ao carregar mapa {} assincronamente.", formatWorldName(worldId), e);
			}
		}, threadPoolManager);
	}

	private GeoMap loadNavFromDisk(int worldId) {
		String navDirStr = GeoDataConfig.GEO_NAV_DIR != null ? GeoDataConfig.GEO_NAV_DIR : "data/nav/";
		Path navFile = Path.of(navDirStr).resolve(worldId + ".nav");

		if (!Files.exists(navFile)) {
			LOG.warn("NAVMESH: Arquivo não encontrado: {}", navFile);
			return null;
		}

		try {
			long startTime = System.currentTimeMillis();
			GeoMap map = loadNavFile(navFile, worldId);
			long loadTime = System.currentTimeMillis() - startTime;

			long fileSizeMB = Files.size(navFile) / (1024 * 1024);
			LOG.debug("NAVMESH: Mapa {} carregado em {}ms ({}MB)",
				formatWorldName(worldId), loadTime, fileSizeMB);

			return map;
		} catch (IOException e) {
			LOG.error("NAVMESH: Erro ao carregar mapa {}.", formatWorldName(worldId), e);
			return null;
		}
	}

	private GeoMap loadNavFile(Path file, int worldId) throws IOException {
		try (RandomAccessFile raf = new RandomAccessFile(file.toFile(), "r");
			 FileChannel channel = raf.getChannel()) {

			long fileSize = channel.size();

			ByteBuffer buffer = ByteBuffer.allocateDirect((int) fileSize);
			buffer.order(ByteOrder.LITTLE_ENDIAN);

			channel.read(buffer);
			buffer.flip();

			GeoMap result = processNavBuffer(buffer, worldId);

			try {
				java.lang.reflect.Method cleanerMethod = buffer.getClass().getMethod("cleaner");
				cleanerMethod.setAccessible(true);
				Object cleaner = cleanerMethod.invoke(buffer);
				if (cleaner != null) {
					java.lang.reflect.Method cleanMethod = cleaner.getClass().getMethod("clean");
					cleanMethod.invoke(cleaner);
				}
			} catch (Exception e) {
				LOG.debug("NAVMESH: Liberação direta de buffer delegada ao GC");
			}

			return result;
		}
	}

	private GeoMap processNavBuffer(ByteBuffer buffer, int worldId) {
		GeoMap map = new GeoMap(worldId);

		int floatCount = buffer.getInt();
		float[] sharedVertices = new float[floatCount];
		for (int i = 0; i < floatCount; i++) {
			sharedVertices[i] = buffer.getFloat();
		}

		int triangleCount = buffer.getInt();
		NavGeometry[] triangles = new NavGeometry[triangleCount];

		int[] edge1Connections = new int[triangleCount];
		int[] edge2Connections = new int[triangleCount];
		int[] edge3Connections = new int[triangleCount];

		for (int i = 0; i < triangleCount; i++) {
			int index0 = buffer.getInt();
			int index1 = buffer.getInt();
			int index2 = buffer.getInt();

			triangles[i] = new NavGeometry(sharedVertices, index0, index1, index2);

			edge1Connections[i] = buffer.getInt();
			edge2Connections[i] = buffer.getInt();
			edge3Connections[i] = buffer.getInt();
		}

		for (int i = 0; i < triangleCount; i++) {
			if (edge1Connections[i] != -1) {
				triangles[i].setEdge1(triangles[edge1Connections[i]]);
			}
			if (edge2Connections[i] != -1) {
				triangles[i].setEdge2(triangles[edge2Connections[i]]);
			}
			if (edge3Connections[i] != -1) {
				triangles[i].setEdge3(triangles[edge3Connections[i]]);
			}

			triangles[i].updateModelBound();
			map.attachChild(triangles[i]);
		}

		map.updateModelBound();
		return map;
	}

	private void startCleanupScheduler() {
		threadPoolManager.scheduleAtFixedRate(() -> {
			try {
				cleanupInactiveMaps();
			} catch (Exception e) {
				LOG.error("NAVMESH: Erro durante limpeza.", e);
			}
		}, CLEANUP_INTERVAL_MS, CLEANUP_INTERVAL_MS);
	}

	private void cleanupInactiveMaps() {
		long now = System.currentTimeMillis();

		for (Map.Entry<Integer, CachedGeoMap> entry : navMaps.entrySet()) {
			int worldId = entry.getKey();
			CachedGeoMap cached = entry.getValue();

			MapActivity activity = mapActivity.get(worldId);

			if (activity != null && activity.getPlayerCount() > 0) {
				continue; // mapa ainda tem jogadores, não remover
			}

			boolean isInactive = activity == null ||
				(activity.getPlayerCount() == 0 &&
					now - activity.getLastAccessTime() > INACTIVE_TIMEOUT_MS);

			if (isInactive) {
				if (navMaps.remove(worldId, cached)) {
					long freedMB = cached.getEstimatedSizeMB();
					totalCacheSizeMB.addAndGet(-freedMB);
					cached.dispose();
					mapActivity.remove(worldId);

					LOG.info("Nav Data: mapa {} removido da memoria (inativo). Mapas atuais em Cache: {}",
						formatWorldName(worldId), describeCachedMaps());
					System.gc();
				}
			}
		}
	}

	private void evictEldestIfNeeded() {
		if (navMaps.size() <= MAX_CACHED_MAPS) {
			return;
		}

		Integer oldestWorldId = null;
		long oldestTime = Long.MAX_VALUE;
		CachedGeoMap oldestCached = null;

		for (Map.Entry<Integer, CachedGeoMap> entry : navMaps.entrySet()) {
			int worldId = entry.getKey();
			MapActivity activity = mapActivity.get(worldId);
			if (activity != null && activity.getPlayerCount() > 0) {
				continue;
			}
			CachedGeoMap c = entry.getValue();
			if (c.lastAccessTime < oldestTime) {
				oldestTime = c.lastAccessTime;
				oldestWorldId = worldId;
				oldestCached = c;
			}
		}

		if (oldestWorldId != null && oldestCached != null) {
			if (navMaps.remove(oldestWorldId, oldestCached)) {
				long freedMB = oldestCached.getEstimatedSizeMB();
				totalCacheSizeMB.addAndGet(-freedMB);
				oldestCached.dispose();
				mapActivity.remove(oldestWorldId);
				LOG.info("Nav Data: LRU removeu mapa {} da memoria. Mapas em Cache: {}",
					formatWorldName(oldestWorldId), describeCachedMaps());
				System.gc();
			}
		}
	}

	private String describeCachedMaps() {
		if (navMaps.isEmpty())
			return "vazio";

		StringJoiner joiner = new StringJoiner(", ");
		for (Integer worldId : navMaps.keySet()) {
			joiner.add(formatWorldName(worldId));
		}
		return joiner.toString();
	}

	private String formatWorldName(int worldId) {
		WorldMapType world = WorldMapType.getWorld(worldId);
		if (world == null)
			return String.valueOf(worldId);

		String[] parts = world.name().toLowerCase(Locale.ROOT).split("_");
		StringBuilder builder = new StringBuilder();
		for (String part : parts) {
			if (part.isEmpty())
				continue;
			if (!builder.isEmpty())
				builder.append(' ');
			builder.append(Character.toUpperCase(part.charAt(0))).append(part.substring(1));
		}
		return builder.toString();
	}

	private MapActivity getOrCreateActivity(int worldId) {
		return mapActivity.computeIfAbsent(worldId, id -> new MapActivity());
	}

	public CacheStats getStats() {
		int totalMaps = navMaps.size();
		int activeMaps = 0;

		for (MapActivity activity : mapActivity.values()) {
			if (activity.getPlayerCount() > 0)
				activeMaps++;
		}

		return new CacheStats(totalMaps, MAX_CACHED_MAPS, activeMaps);
	}

	private static class CachedGeoMap {
		GeoMap geoMap;
		final int worldId;
		final long creationTime;
		private final long estimatedSizeMB;
		volatile long lastAccessTime;
		private volatile boolean disposed = false;

		CachedGeoMap(GeoMap geoMap, int worldId) {
			this.geoMap = geoMap;
			this.worldId = worldId;
			this.creationTime = System.currentTimeMillis();
			this.lastAccessTime = creationTime;
			this.estimatedSizeMB = estimateSizeMB(geoMap);
		}

		void updateAccess() {
			this.lastAccessTime = System.currentTimeMillis();
		}

		void dispose() {
			if (disposed)
				return;
			disposed = true;
			if (geoMap != null) {
				geoMap.cleanUp();
				geoMap = null;
			}
		}

		long getEstimatedSizeMB() {
			if (disposed) {
				return 0;
			}
			return estimatedSizeMB;
		}

		private static long estimateSizeMB(GeoMap geoMap) {
			if (geoMap == null || geoMap.getChildren() == null) {
				return 1;
			}
			int triangleCount = geoMap.getChildren().size();
			return Math.max(1, (triangleCount * 200L) / (1024 * 1024));
		}
	}

	private static class MapActivity {
		private final AtomicInteger playerCount = new AtomicInteger(0);
		private volatile long lastAccessTime = System.currentTimeMillis();

		void incrementPlayerCount() {
			playerCount.incrementAndGet();
			lastAccessTime = System.currentTimeMillis();
		}

		void decrementPlayerCount() {
			playerCount.updateAndGet(current -> Math.max(0, current - 1));
			lastAccessTime = System.currentTimeMillis();
		}

		int getPlayerCount() {
			return playerCount.get();
		}

		void updateLastAccess() {
			lastAccessTime = System.currentTimeMillis();
		}

		long getLastAccessTime() {
			return lastAccessTime;
		}
	}


	public static class CacheStats {
		public final int cachedMaps;
		public final int maxMaps;
		public final int activeMaps;
		public final int criticalMaps;

		public CacheStats(int cached, int max, int active, int critical) {
			this.cachedMaps = cached;
			this.maxMaps = max;
			this.activeMaps = active;
			this.criticalMaps = critical;
		}

		public CacheStats(int cached, int max, int active) {
			this(cached, max, active, 0);
		}

		@Override
		public String toString() {
			return String.format("NavCache: %d/%d | Ativos: %d | Críticos: %d",
				cachedMaps, maxMaps, activeMaps, criticalMaps);
		}
	}

	public static NavData getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private static final class SingletonHolder {
		static final NavData INSTANCE = new NavData();
	}
}