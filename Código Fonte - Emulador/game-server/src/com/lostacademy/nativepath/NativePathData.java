package com.lostacademy.nativepath;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.utils.ThreadPoolManager;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Gerenciador central de dados e repositório de malhas na memória RAM com Cache LRU limitado.
 *
 * ARQUITETURA DE CICLO DE VIDA DE ALTA PERFORMANCE:
 * 1. Resolução dinâmica de arquivos .dat em data/native-path/.
 * 2. Carregamento sob demanda com Cache LRU limitado a NATIVE_PATH_MAX_CACHED_MAPS.
 * 3. Rastreamento de jogadores ativos por mapa (onPlayerEnterMap / onPlayerLeaveMap).
 * 4. Desalocação automática periódica de mapas inativos com 0 jogadores (evita vazamento de 2 GB).
 * 5. Pré-carregamento imediato dos mundos primários para latência zero no spawn de jogadores.
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathData {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathData.class);

	// Índice de worldId -> Path do arquivo .dat correspondente no disco
	private final ConcurrentHashMap<Integer, Path> mapFileIndex = new ConcurrentHashMap<>();

	// Cache delimitado em memória RAM das instâncias de NativePathMap
	private final ConcurrentHashMap<Integer, NativePathMap> maps = new ConcurrentHashMap<>();

	// Controle de atividade e presença de jogadores por mapa
	private final ConcurrentHashMap<Integer, MapActivity> mapActivity = new ConcurrentHashMap<>();

	public final AtomicLong cacheHits = new AtomicLong(0);
	public final AtomicLong cacheMisses = new AtomicLong(0);
	public final AtomicLong totalLoadTimeMs = new AtomicLong(0);
	public final AtomicLong loadedCount = new AtomicLong(0);

	/**
	 * Rastreamento de atividade e tempo de acesso de cada mapa.
	 */
	public static final class MapActivity {
		private final AtomicInteger playerCount = new AtomicInteger(0);
		private volatile long lastAccessTime = System.currentTimeMillis();

		public void incrementPlayerCount() {
			playerCount.incrementAndGet();
			lastAccessTime = System.currentTimeMillis();
		}

		public void decrementPlayerCount() {
			playerCount.updateAndGet(c -> Math.max(0, c - 1));
			lastAccessTime = System.currentTimeMillis();
		}

		public int getPlayerCount() {
			return playerCount.get();
		}

		public void updateAccess() {
			lastAccessTime = System.currentTimeMillis();
		}

		public long getLastAccessTime() {
			return lastAccessTime;
		}
	}

	private NativePathData() {
		indexNativePathDirectories();
		startCleanupScheduler();
	}

	/**
	 * Indexa todos os diretórios em data/native-path/ que seguem o padrão canônico {worldId}_{nome}/xxxx-path.dat.
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

	/**
	 * Localiza o primeiro arquivo *.dat contido no subdiretório do mapa.
	 */
	private static Path findDatFile(Path dir) {
		try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.dat")) {
			for (Path p : stream) {
				return p;
			}
		} catch (IOException ignored) {
		}
		return null;
	}

	/**
	 * Retorna ou cria a estrutura de rastreamento de atividade de um mapa.
	 */
	private MapActivity getOrCreateActivity(int worldId) {
		return mapActivity.computeIfAbsent(worldId, k -> new MapActivity());
	}

	/**
	 * Invocado quando um jogador entra no mapa. Atualiza atividade e dispara pré-carregamento assíncrono.
	 */
	public void onPlayerEnterMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return;

		MapActivity act = getOrCreateActivity(worldId);
		act.incrementPlayerCount();

		if (!maps.containsKey(worldId) && mapFileIndex.containsKey(worldId)) {
			ThreadPoolManager.getInstance().execute(() -> getNativeMap(worldId));
		}
	}

	/**
	 * Invocado quando um jogador sai do mapa. Atualiza a contagem de presença.
	 */
	public void onPlayerLeaveMap(int worldId) {
		MapActivity act = mapActivity.get(worldId);
		if (act != null) {
			act.decrementPlayerCount();
		}
	}

	/**
	 * Retorna a instância de NativePathMap para o worldId solicitado.
	 * Carrega sob demanda de forma thread-safe se ainda não estiver residente na RAM.
	 *
	 * @param worldId Identificador numérico do mapa.
	 * @return A instância de NativePathMap ou null se não houver malha indexada.
	 */
	public NativePathMap getNativeMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return null;

		NativePathMap map = maps.get(worldId);
		if (map != null) {
			cacheHits.incrementAndGet();
			MapActivity act = mapActivity.get(worldId);
			if (act != null) {
				act.updateAccess();
			}
			return map;
		}

		Path filePath = mapFileIndex.get(worldId);
		if (filePath == null) {
			return null;
		}

		// Carregamento sob demanda sincronizado por mapa
		synchronized (this) {
			map = maps.get(worldId);
			if (map != null) {
				cacheHits.incrementAndGet();
				return map;
			}

			cacheMisses.incrementAndGet();
			long t0 = System.currentTimeMillis();

			try {
				map = NativePathMap.loadFromDisk(filePath, worldId);
				checkAndEvictOldestMap();
				maps.put(worldId, map);
				loadedCount.incrementAndGet();
				long elapsed = System.currentTimeMillis() - t0;
				totalLoadTimeMs.addAndGet(elapsed);
				getOrCreateActivity(worldId).updateAccess();

				LOG.info("NATIVE_PATH: Mapa {} carregado sob demanda em {} ms (Cache: {}/{} mapas).",
						worldId, elapsed, maps.size(), NativePathConfig.NATIVE_PATH_MAX_CACHED_MAPS);
			} catch (Exception e) {
				LOG.error("NATIVE_PATH: Falha ao carregar mapa nativo {} ({}).", worldId, filePath.getFileName(), e);
				return null;
			}
		}

		return map;
	}

	/**
	 * Desaloca o mapa menos recentemente utilizado que possua 0 jogadores ativos caso o limite seja atingido.
	 */
	private void checkAndEvictOldestMap() {
		int maxMaps = Math.max(5, NativePathConfig.NATIVE_PATH_MAX_CACHED_MAPS);
		if (maps.size() < maxMaps) {
			return;
		}

		int oldestWorldId = -1;
		long oldestTime = Long.MAX_VALUE;

		for (Map.Entry<Integer, NativePathMap> entry : maps.entrySet()) {
			int wid = entry.getKey();
			MapActivity act = mapActivity.get(wid);
			int players = act != null ? act.getPlayerCount() : 0;
			long lastAccess = act != null ? act.getLastAccessTime() : 0;

			// Nunca descarrega mapas com jogadores ativos
			if (players == 0 && lastAccess < oldestTime) {
				oldestTime = lastAccess;
				oldestWorldId = wid;
			}
		}

		if (oldestWorldId > 0) {
			maps.remove(oldestWorldId);
			LOG.info("NATIVE_PATH: Cache LRU: Mapa inativo {} despejado da memória RAM (novo tamanho: {}).",
					oldestWorldId, maps.size());
		}
	}

	/**
	 * Inicia o agendador de limpeza periódica de mapas inativos sem jogadores.
	 */
	private void startCleanupScheduler() {
		long interval = Math.max(60000L, NativePathConfig.NATIVE_PATH_CLEANUP_INTERVAL_MS);
		ThreadPoolManager.getInstance().scheduleAtFixedRate(this::cleanupInactiveMaps, interval, interval);
	}

	/**
	 * Executa varredura de mapas inativos e desaloca aqueles sem jogadores além do timeout.
	 */
	public void cleanupInactiveMaps() {
		if (maps.isEmpty()) {
			return;
		}

		long now = System.currentTimeMillis();
		long timeout = Math.max(60000L, NativePathConfig.NATIVE_PATH_INACTIVE_TIMEOUT_MS);
		int evicted = 0;

		for (Map.Entry<Integer, NativePathMap> entry : maps.entrySet()) {
			int wid = entry.getKey();
			MapActivity act = mapActivity.get(wid);
			int players = act != null ? act.getPlayerCount() : 0;
			long lastAccess = act != null ? act.getLastAccessTime() : 0;

			if (players == 0 && (now - lastAccess) > timeout) {
				maps.remove(wid);
				evicted++;
			}
		}

		if (evicted > 0) {
			LOG.info("NATIVE_PATH: Limpeza periódica: {} mapas inativos liberados da RAM. Mapas ativos restantes: {}.",
					evicted, maps.size());
		}
	}

	/**
	 * Pré-carrega mapas iniciais mais frequentes durante a inicialização para eliminar latência.
	 */
	public void preloadStarterMaps() {
		if (!NativePathConfig.NATIVE_PATH_ENABLE) {
			return;
		}

		int[] commonWorlds = {
				210010000, // Poeta
				220010000, // Ishalgen
				110010000, // Sanctum
				120010000  // Pandaemonium
		};

		for (int wid : commonWorlds) {
			if (mapFileIndex.containsKey(wid)) {
				getNativeMap(wid);
			}
		}
	}

	/**
	 * Verifica se o mapa está catalogado no disco ou carregado na memória.
	 */
	public boolean hasMap(int worldId) {
		return maps.containsKey(worldId) || mapFileIndex.containsKey(worldId);
	}

	/**
	 * Retorna a quantidade total de mapas atualmente residentes na memória RAM.
	 */
	public int getLoadedMapCount() {
		return maps.size();
	}

	public static NativePathData getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private static final class SingletonHolder {
		static final NativePathData INSTANCE = new NativePathData();
	}
}
