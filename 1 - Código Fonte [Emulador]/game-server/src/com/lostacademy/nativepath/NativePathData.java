package com.lostacademy.nativepath;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * Gerenciador de arquivos e cache LRU do subsistema native-path da CryEngine.
 *
 * @author KAMIDAKI
 */
public final class NativePathData {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathData.class);

	// Índice de worldId -> Path do arquivo .dat
	private final ConcurrentHashMap<Integer, Path> mapFileIndex = new ConcurrentHashMap<>();

	// Cache de mapas carregados em memória
	private final ConcurrentHashMap<Integer, CachedNativeMap> cachedMaps = new ConcurrentHashMap<>();

	// Rastreamento de atividade / jogadores por mapa
	private final ConcurrentHashMap<Integer, MapActivity> mapActivity = new ConcurrentHashMap<>();

	public final AtomicLong cacheHits = new AtomicLong(0);
	public final AtomicLong cacheMisses = new AtomicLong(0);
	public final AtomicLong totalLoadTimeMs = new AtomicLong(0);
	public final AtomicLong loadedCount = new AtomicLong(0);

	private final ThreadPoolManager threadPoolManager = ThreadPoolManager.getInstance();

	private NativePathData() {
		indexNativePathDirectories();
		startCleanupScheduler();
	}

	/**
	 * Indexa todos os diretórios em data/native-path/ que seguem o padrão {worldId}_{nome}/xxxx.dat.
	 */
	public void indexNativePathDirectories() {
		String baseDirStr = NativePathConfig.NATIVE_PATH_DIR != null ? NativePathConfig.NATIVE_PATH_DIR : "data/native-path/";
		Path baseDir = Path.of(baseDirStr);

		if (!Files.exists(baseDir) || !Files.isDirectory(baseDir)) {
			LOG.warn("NATIVE_PATH: Diretório raiz não encontrado: {}", baseDir.toAbsolutePath());
			return;
		}

		int indexed = 0;
		try (DirectoryStream<Path> stream = Files.newDirectoryStream(baseDir)) {
			for (Path subDir : stream) {
				if (!Files.isDirectory(subDir))
					continue;

				String dirName = subDir.getFileName().toString();
				int underIdx = dirName.indexOf('_');
				String idStr = underIdx > 0 ? dirName.substring(0, underIdx) : dirName;

				try {
					int worldId = Integer.parseInt(idStr);
					Path datFile = findDatFile(subDir);
					if (datFile != null) {
						mapFileIndex.put(worldId, datFile);
						indexed++;
					}
				} catch (NumberFormatException ignored) {
				}
			}
		} catch (IOException e) {
			LOG.error("NATIVE_PATH: Erro ao indexar diretórios de mapas.", e);
		}

		LOG.info("NATIVE_PATH: {} mapas nativos CryEngine indexados em {}", indexed, baseDirStr);
	}

	private static Path findDatFile(Path dir) {
		try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.dat")) {
			for (Path p : stream) {
				return p;
			}
		} catch (IOException ignored) {
		}
		return null;
	}

	public boolean hasMap(int worldId) {
		return mapFileIndex.containsKey(worldId);
	}

	public void onPlayerEnterMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return;

		MapActivity activity = mapActivity.computeIfAbsent(worldId, id -> new MapActivity());
		activity.incrementPlayerCount();

		if (!cachedMaps.containsKey(worldId) && mapFileIndex.containsKey(worldId)) {
			loadMapAsync(worldId);
		}
	}

	public void onPlayerLeaveMap(int worldId) {
		MapActivity activity = mapActivity.get(worldId);
		if (activity != null) {
			activity.decrementPlayerCount();
		}
	}

	public NativePathMap getNativeMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return null;

		CachedNativeMap cached = cachedMaps.get(worldId);
		if (cached != null) {
			cached.updateAccess();
			cacheHits.incrementAndGet();
			return cached.map;
		}

		Path file = mapFileIndex.get(worldId);
		if (file == null) {
			return null;
		}

		synchronized (cachedMaps) {
			cached = cachedMaps.get(worldId);
			if (cached != null) {
				cached.updateAccess();
				cacheHits.incrementAndGet();
				return cached.map;
			}

			cacheMisses.incrementAndGet();
			long startTime = System.currentTimeMillis();

			try {
				NativePathMap map = NativePathMap.loadFromDisk(file, worldId);
				long loadTime = System.currentTimeMillis() - startTime;
				totalLoadTimeMs.addAndGet(loadTime);
				loadedCount.incrementAndGet();

				cachedMaps.put(worldId, new CachedNativeMap(map));
				evictEldestIfNeeded();

				return map;
			} catch (Exception e) {
				LOG.error("NATIVE_PATH: Erro ao carregar mapa nativo {} do disco.", worldId, e);
				return null;
			}
		}
	}

	private void loadMapAsync(int worldId) {
		CompletableFuture.runAsync(() -> {
			try {
				getNativeMap(worldId);
			} catch (Exception e) {
				LOG.error("NATIVE_PATH: Falha no carregamento assíncrono do mapa {}.", worldId, e);
			}
		}, threadPoolManager);
	}

	private void evictEldestIfNeeded() {
		if (cachedMaps.size() <= NativePathConfig.NATIVE_PATH_MAX_CACHED_MAPS)
			return;

		Integer oldestWorldId = null;
		long oldestTime = Long.MAX_VALUE;
		CachedNativeMap oldestCached = null;

		for (Map.Entry<Integer, CachedNativeMap> entry : cachedMaps.entrySet()) {
			int worldId = entry.getKey();
			MapActivity activity = mapActivity.get(worldId);
			if (activity != null && activity.getPlayerCount() > 0) {
				continue;
			}
			CachedNativeMap c = entry.getValue();
			if (c.lastAccessTime < oldestTime) {
				oldestTime = c.lastAccessTime;
				oldestWorldId = worldId;
				oldestCached = c;
			}
		}

		if (oldestWorldId != null && oldestCached != null) {
			if (cachedMaps.remove(oldestWorldId, oldestCached)) {
				mapActivity.remove(oldestWorldId);
				LOG.info("NATIVE_PATH: LRU removeu mapa {} da memoria.", oldestWorldId);
			}
		}
	}

	private void startCleanupScheduler() {
		long interval = NativePathConfig.NATIVE_PATH_CLEANUP_INTERVAL_MS;
		if (interval <= 0)
			interval = 180000;

		threadPoolManager.scheduleAtFixedRate(() -> {
			try {
				cleanupInactiveMaps();
			} catch (Exception e) {
				LOG.error("NATIVE_PATH: Erro durante limpeza periódica.", e);
			}
		}, interval, interval);
	}

	private void cleanupInactiveMaps() {
		long now = System.currentTimeMillis();
		long timeout = NativePathConfig.NATIVE_PATH_INACTIVE_TIMEOUT_MS;

		for (Map.Entry<Integer, CachedNativeMap> entry : cachedMaps.entrySet()) {
			int worldId = entry.getKey();
			CachedNativeMap cached = entry.getValue();
			MapActivity activity = mapActivity.get(worldId);

			if (activity != null && activity.getPlayerCount() > 0)
				continue;

			boolean isInactive = activity == null ||
				(activity.getPlayerCount() == 0 && (now - activity.getLastAccessTime()) > timeout);

			if (isInactive) {
				if (cachedMaps.remove(worldId, cached)) {
					mapActivity.remove(worldId);
					LOG.info("NATIVE_PATH: Mapa {} liberado da memória por inatividade.", worldId);
				}
			}
		}
	}

	private static class CachedNativeMap {
		final NativePathMap map;
		volatile long lastAccessTime;

		CachedNativeMap(NativePathMap map) {
			this.map = map;
			this.lastAccessTime = System.currentTimeMillis();
		}

		void updateAccess() {
			this.lastAccessTime = System.currentTimeMillis();
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
			playerCount.updateAndGet(c -> Math.max(0, c - 1));
			lastAccessTime = System.currentTimeMillis();
		}

		int getPlayerCount() {
			return playerCount.get();
		}

		long getLastAccessTime() {
			return lastAccessTime;
		}
	}

	public static NativePathData getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private static final class SingletonHolder {
		static final NativePathData INSTANCE = new NativePathData();
	}
}
