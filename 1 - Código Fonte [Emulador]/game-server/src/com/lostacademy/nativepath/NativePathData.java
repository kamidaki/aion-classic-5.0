package com.lostacademy.nativepath;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.templates.world.WorldMapTemplate;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Gerenciador central de dados e repositório de malhas na memória RAM.
 *
 * ARQUITETURA RESIDENTE PERMANENTE (PARIDADE COM GEODATA):
 * 1. Pré-carregamento Integral no Boot: 100% dos arquivos *-path.dat são lidos em paralelo
 *    durante a inicialização do GameServer.
 * 2. Sem Carregamento sob Demanda: Elimina qualquer operação de I/O de disco durante o jogo,
 *    eliminando engasgos (lag spikes) quando jogadores entram em novas zonas ou masmorras.
 * 3. Sem Evicção / Sem Limpeza: Todos os mapas permanecem 100% na memória RAM a todo momento,
 *    prontos para consultas instantâneas em tempo constante O(1), exatamente como o GeoData (.geo).
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathData {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathData.class);

	// Índice de worldId -> Path do arquivo .dat correspondente no disco
	private final ConcurrentHashMap<Integer, Path> mapFileIndex = new ConcurrentHashMap<>();

	// Armazenamento 100% em memória RAM das instâncias de NativePathMap carregadas
	private final ConcurrentHashMap<Integer, NativePathMap> maps = new ConcurrentHashMap<>();

	public final AtomicLong cacheHits = new AtomicLong(0);
	public final AtomicLong totalLoadTimeMs = new AtomicLong(0);
	public final AtomicLong loadedCount = new AtomicLong(0);

	private NativePathData() {
		indexNativePathDirectories();
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
	 * Fallback de compatibilidade com o cliente oficial Classic 5.0 (D:/GameForge/aionclassic/levels).
	 */
	private void indexClientLevelsFallback() {
		Path clientLevels = Path.of("D:/GameForge/aionclassic/levels");
		if (!Files.exists(clientLevels) || !Files.isDirectory(clientLevels)) {
			return;
		}

		if (DataManager.WORLD_MAPS_DATA == null) {
			return;
		}

		int added = 0;
		for (WorldMapTemplate template : DataManager.WORLD_MAPS_DATA) {
			int worldId = template.getMapId();
			if (mapFileIndex.containsKey(worldId)) {
				continue;
			}
			String cName = template.getCName();
			if (cName == null || cName.isEmpty()) {
				continue;
			}
			Path clientDat = clientLevels.resolve(cName.toLowerCase()).resolve(cName.toUpperCase() + "-path.dat");
			if (!Files.exists(clientDat)) {
				clientDat = clientLevels.resolve(cName.toLowerCase()).resolve(cName.toLowerCase() + "-path.dat");
			}
			if (Files.exists(clientDat)) {
				mapFileIndex.put(worldId, clientDat);
				added++;
			}
		}
		if (added > 0) {
			LOG.info("NATIVE_PATH: {} mapas adicionais indexados a partir do cliente em {}", added, clientLevels);
		}
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
	 * Carrega 100% de todos os mapas nativos indexados para a memória RAM de forma paralela e concorrente.
	 * Invocado durante o boot do GameServer na fase de inicialização de subsistemas de mundo.
	 */
	public void loadAllMaps() {
		if (!NativePathConfig.NATIVE_PATH_ENABLE) {
			LOG.info("NATIVE_PATH: Subsistema desativado por configuração. Nenhum mapa carregado.");
			return;
		}

		if (mapFileIndex.isEmpty()) {
			indexNativePathDirectories();
		}
		indexClientLevelsFallback();

		long startTime = System.currentTimeMillis();
		AtomicInteger successCount = new AtomicInteger(0);
		AtomicInteger failCount = new AtomicInteger(0);
		AtomicLong totalMemoryMB = new AtomicLong(0);

		// Carregamento paralelo multi-threaded de todos os mapas
		mapFileIndex.entrySet().parallelStream().forEach(entry -> {
			int worldId = entry.getKey();
			Path file = entry.getValue();

			try {
				NativePathMap map = NativePathMap.loadFromDisk(file, worldId);
				maps.put(worldId, map);
				successCount.incrementAndGet();
				totalMemoryMB.addAndGet(map.getEstimatedSizeMB());
			} catch (Exception e) {
				failCount.incrementAndGet();
				LOG.error("NATIVE_PATH: Falha crítica ao carregar mapa {} ({}) na inicialização.", worldId, file.getFileName(), e);
			}
		});

		long duration = System.currentTimeMillis() - startTime;
		totalLoadTimeMs.set(duration);
		loadedCount.set(successCount.get());

		LOG.info("NATIVE_PATH: [BOOT COMPLETO] 100% dos mapas CryEngine carregados na RAM: {} mapas prontos ({} falhas, ~{} MB) em {} ms.",
				successCount.get(), failCount.get(), totalMemoryMB.get(), duration);
	}

	/**
	 * Retorna a instância residente de NativePathMap em tempo constante O(1) sem travas e sem leitura de disco.
	 *
	 * @param worldId Identificador numérico do mapa.
	 * @return A instância de NativePathMap ou null se não houver malha cadastrada.
	 */
	public NativePathMap getNativeMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return null;

		NativePathMap map = maps.get(worldId);
		if (map != null) {
			cacheHits.incrementAndGet();
			return map;
		}

		return null;
	}

	/**
	 * Verifica se o mapa está carregado e disponível na memória.
	 */
	public boolean hasMap(int worldId) {
		return maps.containsKey(worldId);
	}

	/**
	 * Retorna a quantidade total de mapas atualmente residentes na memória RAM.
	 */
	public int getLoadedMapCount() {
		return maps.size();
	}

	@Deprecated
	public void onPlayerEnterMap(int worldId) {
		// No-op: mantido para retrocompatibilidade, mapas já residem na memória RAM
	}

	@Deprecated
	public void onPlayerLeaveMap(int worldId) {
		// No-op: mantido para retrocompatibilidade, mapas já residem na memória RAM
	}

	public static NativePathData getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private static final class SingletonHolder {
		static final NativePathData INSTANCE = new NativePathData();
	}
}
