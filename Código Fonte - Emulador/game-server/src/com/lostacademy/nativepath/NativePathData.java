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
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldMap;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Gerenciador central de dados e repositório de malhas na memória RAM com carregamento 100%
 * sob demanda e desalocação segura por inatividade.
 *
 * ARQUITETURA DE CICLO DE VIDA DE ALTA PERFORMANCE (100% SOB DEMANDA):
 * 1. Resolução dinâmica de arquivos .dat em data/native-path/ (apenas catálogo de caminhos na inicialização).
 * 2. Carregamento 100% sob demanda: nenhum mapa é carregado na inicialização do servidor.
 * 3. Sem limite artificial de mapas: mapas são mantidos na RAM enquanto houver jogadores ou atividade recente.
 * 4. Rastreamento rigoroso de jogadores ativos por mapa (onPlayerEnterMap / onPlayerLeaveMap).
 * 5. Desalocação automática e segura após 3 minutos sem nenhum jogador no mapa.
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathData {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathData.class);

	// Índice de worldId -> Path do arquivo .dat correspondente no disco
	private final ConcurrentHashMap<Integer, Path> mapFileIndex = new ConcurrentHashMap<>();

	// Cache de instâncias de NativePathMap residentes na memória RAM
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
		private volatile long emptySince = 0L;

		public void incrementPlayerCount() {
			playerCount.incrementAndGet();
			lastAccessTime = System.currentTimeMillis();
			emptySince = 0L;
		}

		public void decrementPlayerCount() {
			int remaining = playerCount.updateAndGet(c -> Math.max(0, c - 1));
			lastAccessTime = System.currentTimeMillis();
			if (remaining == 0 && emptySince == 0L) {
				emptySince = System.currentTimeMillis();
			}
		}

		public int getPlayerCount() {
			return playerCount.get();
		}

		public void setPlayerCount(int count) {
			playerCount.set(count);
			if (count == 0) {
				if (emptySince == 0L) {
					emptySince = System.currentTimeMillis();
				}
			} else {
				emptySince = 0L;
			}
		}

		public long getEmptySince() {
			return emptySince;
		}

		public void setEmptySince(long time) {
			this.emptySince = time;
		}

		public void resetEmptySince() {
			this.emptySince = 0L;
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
	 * Não carrega nenhum byte na RAM — apenas indexa a localização dos arquivos no disco.
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

		LOG.info("NATIVE_PATH: {} mapas nativos CryEngine catalogados (100% sob demanda) em {}", indexed, baseDirStr);
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
	 * Invocado quando um jogador entra no mapa (login, teleporte, CM_LEVEL_READY).
	 * Atualiza presença de jogadores e dispara carregamento sob demanda se necessário.
	 */
	public void onPlayerEnterMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return;

		MapActivity act = getOrCreateActivity(worldId);
		act.incrementPlayerCount();

		// Se o mapa ainda não estiver carregado na memória, inicia o carregamento sob demanda imediatamente
		if (!maps.containsKey(worldId) && mapFileIndex.containsKey(worldId)) {
			ThreadPoolManager.getInstance().execute(() -> getNativeMap(worldId));
		}
	}

	/**
	 * Invocado quando um jogador sai do mapa (logout, teleporte para outro mapa).
	 * Atualiza contagem de presença e agenda checagem de desalocação caso o mapa fique vazio.
	 */
	public void onPlayerLeaveMap(int worldId) {
		MapActivity act = mapActivity.get(worldId);
		if (act != null) {
			act.decrementPlayerCount();
			if (act.getPlayerCount() == 0) {
				long timeout = Math.max(60000L, NativePathConfig.NATIVE_PATH_INACTIVE_TIMEOUT_MS);
				ThreadPoolManager.getInstance().schedule(() -> unloadIfEmpty(worldId), timeout);
			}
		}
	}

	/**
	 * Consulta a quantidade real de jogadores ativos no mapa através do WorldMap do servidor.
	 */
	public int getActivePlayerCount(int worldId) {
		try {
			if (World.getInstance() != null) {
				WorldMap worldMap = World.getInstance().getWorldMap(worldId);
				if (worldMap != null) {
					int count = 0;
					for (WorldMapInstance inst : worldMap) {
						count += inst.getPlayerCount();
					}
					return count;
				}
			}
		} catch (Throwable ignored) {
		}
		MapActivity act = mapActivity.get(worldId);
		return act != null ? act.getPlayerCount() : 0;
	}

	/**
	 * Retorna a instância de NativePathMap para o worldId solicitado.
	 * Carrega 100% sob demanda de forma thread-safe se ainda não estiver residente na RAM.
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
				maps.put(worldId, map);
				loadedCount.incrementAndGet();
				long elapsed = System.currentTimeMillis() - t0;
				totalLoadTimeMs.addAndGet(elapsed);
				getOrCreateActivity(worldId).updateAccess();

				LOG.info("NATIVE_PATH: Mapa {} carregado 100% sob demanda em {} ms ({} camadas ativas, {} MB RAM | Total carregados: {}).",
						worldId, elapsed, map.getTotalLayers(), map.getEstimatedSizeMB(), maps.size());
			} catch (Exception e) {
				LOG.error("NATIVE_PATH: Falha ao carregar mapa nativo {} sob demanda ({}).", worldId, filePath.getFileName(), e);
				return null;
			}
		}

		return map;
	}

	/**
	 * Desaloca com segurança o mapa da memória RAM se ele permanecer sem jogadores ativos após 3 minutos.
	 */
	public void unloadIfEmpty(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE) {
			return;
		}

		NativePathMap map = maps.get(worldId);
		if (map == null) {
			return;
		}

		int players = getActivePlayerCount(worldId);
		MapActivity act = mapActivity.get(worldId);
		if (act != null) {
			act.setPlayerCount(players);
		}

		if (players > 0) {
			if (act != null) {
				act.resetEmptySince();
			}
			return;
		}

		long now = System.currentTimeMillis();
		long emptySince = act != null ? act.getEmptySince() : now;
		long timeout = Math.max(60000L, NativePathConfig.NATIVE_PATH_INACTIVE_TIMEOUT_MS);

		if (emptySince > 0 && (now - emptySince) >= timeout) {
			synchronized (this) {
				// Re-valida sob lock
				players = getActivePlayerCount(worldId);
				if (players == 0) {
					NativePathMap removed = maps.remove(worldId);
					if (removed != null) {
						removed.dispose();
						LOG.info("NATIVE_PATH: Mapa {} sem jogadores há mais de 3 minutos descarregado com segurança da RAM (Mapas ativos restantes: {}).",
								worldId, maps.size());
					}
				}
			}
		}
	}

	/**
	 * Inicia o agendador de limpeza periódica de mapas inativos sem jogadores.
	 */
	private void startCleanupScheduler() {
		long interval = Math.max(30000L, NativePathConfig.NATIVE_PATH_CLEANUP_INTERVAL_MS);
		ThreadPoolManager.getInstance().scheduleAtFixedRate(this::cleanupInactiveMaps, interval, interval);
	}

	/**
	 * Executa varredura de mapas inativos e desaloca com segurança aqueles com 0 jogadores após 3 minutos.
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
			int players = getActivePlayerCount(wid);
			MapActivity act = getOrCreateActivity(wid);
			act.setPlayerCount(players);

			if (players == 0) {
				long emptySince = act.getEmptySince();
				if (emptySince == 0L) {
					act.setEmptySince(now);
				} else if ((now - emptySince) >= timeout) {
					NativePathMap removed = maps.remove(wid);
					if (removed != null) {
						removed.dispose();
						evicted++;
					}
				}
			} else {
				act.resetEmptySince();
			}
		}

		if (evicted > 0) {
			LOG.info("NATIVE_PATH: Limpeza periódica: {} mapas inativos descarregados com segurança da RAM. Mapas ativos restantes: {}.",
					evicted, maps.size());
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
