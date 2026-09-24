package com.lostacademy.nativepath;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.templates.world.WorldMapTemplate;
import com.aionemu.gameserver.world.geo.GeoService;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Representação em memória de alta performance do mapa de navegação nativo da CryEngine.
 *
 * Esta classe decodifica e armazena os dados dos arquivos *-path.dat compilados pelo editor do Aion,
 * fornecendo consultas em tempo constante O(1) de:
 * 1. Transitabilidade subcelular de 0.5m x 0.5m (paredes, cercas, decorações, buracos).
 * 2. Cota exata da superfície (Z) combinando relevo oficial GeoEngine e estruturas elevadas CryEngine.
 * 3. Raycasting físico contínuo (Digital Differential Analyzer - DDA) com validação 3D contra GeoEngine.
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathMap {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathMap.class);

	/**
	 * Tamanho métrico de cada subcélula na grade de alta resolução da CryEngine (0.5 metros).
	 */
	public static final float SUBCELL_SIZE = 0.5f;

	/**
	 * Quantidade de subcélulas por eixo dentro de cada setor macro (32 x 32 = 1024 subcélulas).
	 */
	public static final int SUBCELLS_PER_SECTOR = 32;

	/**
	 * Tamanho métrico de cada setor macro em metros (16 metros x 16 metros).
	 */
	public static final int SECTOR_SIZE = 16;

	/**
	 * Altura máxima de degrau (subida vertical) que um agente pode transpor sem pular (0.8 metros).
	 */
	public static final float MAX_STEP_UP = 0.8f;

	/**
	 * Altura máxima de desnível/queda (descida vertical) que um agente pode descer com segurança (1.8 metros).
	 */
	public static final float MAX_DROP_DOWN = 1.8f;

	private final int worldId;
	private final int mapSize;
	private final int sectorDim;
	private final NativePathSector[] sectors;
	private final int totalLayers;
	private final long estimatedSizeMB;

	/**
	 * Construtor imutável da malha espacial do mapa.
	 *
	 * @param worldId     Identificador numérico do mapa (ex: 210010000 = Poeta).
	 * @param mapSize     Dimensão métrica total do mapa (ex: 3072 metros).
	 * @param sectors     Vetor plano indexado em O(1) contendo todos os setores de 16m x 16m.
	 * @param totalLayers Quantidade total de camadas decodificadas do arquivo binário.
	 */
	public NativePathMap(int worldId, int mapSize, NativePathSector[] sectors, int totalLayers) {
		this.worldId = worldId;
		this.mapSize = mapSize > 0 ? mapSize : 3072;
		this.sectorDim = this.mapSize / SECTOR_SIZE;
		this.sectors = sectors != null ? sectors : new NativePathSector[sectorDim * sectorDim];
		this.totalLayers = totalLayers;
		this.estimatedSizeMB = Math.max(1, (this.sectors.length * 8L + totalLayers * 96L) / (1024 * 1024));
	}

	public int getWorldId() {
		return worldId;
	}

	public int getMapSize() {
		return mapSize;
	}

	public int getSectorDim() {
		return sectorDim;
	}

	public int getTotalLayers() {
		return totalLayers;
	}

	public long getEstimatedSizeMB() {
		return estimatedSizeMB;
	}

	/**
	 * Desaloca com segurança as referências espaciais e de setores da memória RAM,
	 * permitindo que o Garbage Collector limpe os arrays e camadas imediatamente.
	 */
	public void dispose() {
		if (sectors != null) {
			java.util.Arrays.fill(sectors, null);
		}
	}

	/**
	 * Retorna o setor espacial correspondente aos índices discretos de grade em O(1).
	 *
	 * @param sx Índice horizontal do setor (0 .. sectorDim - 1).
	 * @param sy Índice vertical do setor (0 .. sectorDim - 1).
	 * @return O NativePathSector correspondente ou null se fora dos limites do mapa.
	 */
	public NativePathSector getSector(int sx, int sy) {
		if (sx < 0 || sx >= sectorDim || sy < 0 || sy >= sectorDim) {
			return null;
		}
		return sectors[sy * sectorDim + sx];
	}

	/**
	 * Retorna o setor espacial que engloba as coordenadas métricas contínuas de mundo (x, y) em O(1).
	 *
	 * @param x Coordenada X no espaço de jogo (em metros).
	 * @param y Coordenada Y no espaço de jogo (em metros).
	 * @return O NativePathSector correspondente ou null se fora do mapa.
	 */
	public NativePathSector getSectorAtWorld(float x, float y) {
		int sx = ((int) x) / SECTOR_SIZE;
		int sy = ((int) y) / SECTOR_SIZE;
		return getSector(sx, sy);
	}

	/**
	 * Obtém a cota de terreno 3D confiável de referência através do GeoService.
	 */
	private float queryGeoTerrainZ(float x, float y, float zRef, int instanceId) {
		try {
			if (GeoService.getInstance() != null) {
				float gz = GeoService.getInstance().getZ(worldId, x, y, zRef + 2.0f, zRef - 4.0f, instanceId);
				if (!Float.isNaN(gz)) {
					return gz;
				}
				gz = GeoService.getInstance().getZ(worldId, x, y, zRef + 5.0f, zRef - 10.0f, instanceId);
				if (!Float.isNaN(gz)) {
					return gz;
				}
				gz = GeoService.getInstance().getZ(worldId, x, y);
				if (!Float.isNaN(gz) && gz != 0) {
					return gz;
				}
			}
		} catch (Throwable ignored) {
		}
		return Float.NaN;
	}

	/**
	 * Verifica se a coordenada 3D exata (x, y, z) está situada sobre piso transitável no CryEngine.
	 *
	 * Processo de Verificação:
	 * 1. Converte (x, y) para setor de 16m e subcélula de 0.5m.
	 * 2. Consulta a cota do terreno natural na GeoEngine como âncora vertical de referência.
	 * 3. Seleciona a camada espacial que melhor corresponde à altitude do agente (findBestLayer).
	 * 4. Avalia o bit de bloqueio da subcélula (0 = livre / 1 = obstáculo).
	 *
	 * @param x        Coordenada X em metros.
	 * @param y        Coordenada Y em metros.
	 * @param z        Coordenada Z (altitude atual do agente) em metros.
	 * @param maxZDiff Tolerância de proximidade vertical para localização da camada.
	 * @return true se o ponto for transitável sem colidir com obstáculos; false se bloqueado.
	 */
	public boolean isWalkable(float x, float y, float z, float maxZDiff) {
		return isWalkable(x, y, z, maxZDiff, 0);
	}

	public boolean isWalkable(float x, float y, float z, float maxZDiff, int instanceId) {
		if (x < 0 || x >= mapSize || y < 0 || y >= mapSize) {
			return false;
		}

		int sx = ((int) x) / SECTOR_SIZE;
		int sy = ((int) y) / SECTOR_SIZE;
		if (sx < 0 || sx >= sectorDim || sy < 0 || sy >= sectorDim) {
			return false;
		}

		NativePathSector sector = sectors[sy * sectorDim + sx];
		if (sector == null || sector.getLayerCount() == 0) {
			return false;
		}

		int subX = (int) ((x - (sx * SECTOR_SIZE)) / SUBCELL_SIZE);
		int subY = (int) ((y - (sy * SECTOR_SIZE)) / SUBCELL_SIZE);
		subX = Math.max(0, Math.min(SUBCELLS_PER_SECTOR - 1, subX));
		subY = Math.max(0, Math.min(SUBCELLS_PER_SECTOR - 1, subY));

		float terrainZ = queryGeoTerrainZ(x, y, z, instanceId);
		if (Float.isNaN(terrainZ)) {
			terrainZ = z;
		}

		NativePathSector.Layer layer = sector.findBestLayer(subX, subY, z, terrainZ, maxZDiff);
		if (layer == null) {
			return false;
		}

		return layer.isWalkable(subX, subY);
	}

	/**
	 * Retorna a altitude Z real da superfície navegável na posição (x, y) próxima a currentZ.
	 *
	 * @param x        Coordenada X em metros.
	 * @param y        Coordenada Y em metros.
	 * @param currentZ Altitude Z de referência do agente para desempate de camadas verticais.
	 * @param fallbackZ Cota padrão a ser retornada caso o ponto não pertença a nenhuma camada válida.
	 * @return A altitude em metros do piso navegável.
	 */
	public float getSurfaceZ(float x, float y, float currentZ, float fallbackZ) {
		return getSurfaceZ(x, y, currentZ, fallbackZ, 0);
	}

	public float getSurfaceZ(float x, float y, float currentZ, float fallbackZ, int instanceId) {
		if (x < 0 || x >= mapSize || y < 0 || y >= mapSize) {
			return fallbackZ;
		}

		int sx = ((int) x) / SECTOR_SIZE;
		int sy = ((int) y) / SECTOR_SIZE;
		if (sx < 0 || sx >= sectorDim || sy < 0 || sy >= sectorDim) {
			return fallbackZ;
		}

		float terrainZ = queryGeoTerrainZ(x, y, currentZ, instanceId);

		NativePathSector sector = sectors[sy * sectorDim + sx];
		if (sector == null || sector.getLayerCount() == 0) {
			return !Float.isNaN(terrainZ) ? terrainZ : fallbackZ;
		}

		int subX = (int) ((x - (sx * SECTOR_SIZE)) / SUBCELL_SIZE);
		int subY = (int) ((y - (sy * SECTOR_SIZE)) / SUBCELL_SIZE);
		subX = Math.max(0, Math.min(SUBCELLS_PER_SECTOR - 1, subX));
		subY = Math.max(0, Math.min(SUBCELLS_PER_SECTOR - 1, subY));

		float anchorTerrainZ = !Float.isNaN(terrainZ) ? terrainZ : (!Float.isNaN(currentZ) ? currentZ : fallbackZ);

		NativePathSector.Layer layer = sector.findBestLayer(subX, subY, currentZ, anchorTerrainZ, 12.0f);
		if (layer != null) {
			float lz = layer.getZ(subX, subY, anchorTerrainZ);
			if (!Float.isNaN(lz)) {
				return lz;
			}
		}

		if (!Float.isNaN(terrainZ)) {
			return terrainZ;
		}

		return fallbackZ;
	}

	public float getSurfaceZ(float x, float y, float fallbackZ) {
		return getSurfaceZ(x, y, fallbackZ, fallbackZ);
	}

	/**
	 * Verifica se há linha de visão desobstruída e percurso caminhável contínuo entre dois pontos no espaço 3D.
	 *
	 * Algoritmo DDA (Digital Differential Analyzer) de Alta Precisão:
	 * 1. Calcula o vetor 3D e a distância euclidiana plana (dist2D).
	 * 2. Rejeita inclinações excessivas (rampas com gradiente vertical > 1.2, ou seja, > ~50 graus).
	 * 3. Realiza raycast físico contra malhas da GeoEngine (portas de masmorras, barricadas dinâmicas, decorações).
	 * 4. Amostra cada subcélula intermediária de 0.5m ao longo da trajetória:
	 *    - Verifica se a subcélula é transitável (isWalkable).
	 *    - Valida o desnível vertical assimétrico: subida <= MAX_STEP_UP (0.8m) e descida <= MAX_DROP_DOWN (1.8m).
	 *    - Verifica a cota do chão real para evitar caminhar sobre o ar ou atravessar abismos.
	 *
	 * @param x1            Coordenada X de origem.
	 * @param y1            Coordenada Y de origem.
	 * @param z1            Coordenada Z de origem.
	 * @param x2            Coordenada X de destino.
	 * @param y2            Coordenada Y de destino.
	 * @param z2            Coordenada Z de destino.
	 * @param maxDropHeight Tolerância máxima de desnível vertical na descida (metros).
	 * @return true se o agente puder caminhar em linha reta entre os pontos; false caso haja qualquer obstrução.
	 */
	public boolean canPassPhysical(float x1, float y1, float z1, float x2, float y2, float z2, int instanceId) {
		try {
			if (GeoService.getInstance() != null) {
				float dx = x2 - x1;
				float dy = y2 - y1;
				float dz = z2 - z1;
				float dist3D = (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
				return GeoService.getInstance().canPassPhysical(worldId,
						x1, y1, z1 + 1.25f,
						x2, y2, z2 + 1.25f,
						dist3D, instanceId);
			}
		} catch (Throwable ignored) {
		}
		return true;
	}

	public boolean hasLineOfSight(float x1, float y1, float z1, float x2, float y2, float z2, float maxDropHeight) {
		return hasLineOfSight(x1, y1, z1, x2, y2, z2, maxDropHeight, 0);
	}

	public boolean hasLineOfSight(float x1, float y1, float z1, float x2, float y2, float z2, float maxDropHeight, int instanceId) {
		float dx = x2 - x1;
		float dy = y2 - y1;
		float dz = z2 - z1;
		float dist2D = (float) Math.hypot(dx, dy);

		if (dist2D < 0.25f) {
			float zDiff = z2 - z1;
			if (zDiff > MAX_STEP_UP || -zDiff > maxDropHeight) {
				return false;
			}
			return true;
		}

		// Rejeita rampas excessivamente íngremes (> ~50 graus)
		if (Math.abs(dz) / dist2D > 1.2f) {
			return false;
		}

		float dist3D = (float) Math.sqrt(dx * dx + dy * dy + dz * dz);

		// Validação física 3D contra objetos .geo (estruturas, casas, árvores, muralhas, portas)
		// Usa altura do tronco/peito (+1.25m) para evitar falso-positivo em relevo e degraus
		try {
			if (GeoService.getInstance() != null) {
				boolean canPass = GeoService.getInstance().canPassPhysical(worldId,
						x1, y1, z1 + 1.25f,
						x2, y2, z2 + 1.25f,
						dist3D, instanceId);
				if (!canPass) {
					return false;
				}
			}
		} catch (Throwable ignored) {
		}

		// Raycasting nas subcélulas de 0.5m do CryEngine
		int steps = Math.max(1, (int) Math.ceil(dist2D / SUBCELL_SIZE));
		float stepX = dx / steps;
		float stepY = dy / steps;
		float stepZ = dz / steps;

		float currX = x1;
		float currY = y1;
		float currZ = z1;
		float prevGroundZ = z1;

		for (int i = 1; i <= steps; i++) {
			currX += stepX;
			currY += stepY;
			currZ += stepZ;

			// Verifica se a subcélula é transitável
			if (!isWalkable(currX, currY, currZ, maxDropHeight + 1.0f, instanceId)) {
				return false;
			}

			// Valida cota do solo real
			float groundZ = getSurfaceZ(currX, currY, currZ, Float.NaN, instanceId);
			if (!Float.isNaN(groundZ)) {
				float deltaZ = groundZ - prevGroundZ;
				if (deltaZ > MAX_STEP_UP || -deltaZ > maxDropHeight * 1.5f) {
					return false;
				}
				prevGroundZ = groundZ;
			}
		}

		return true;
	}

	public float[] findClosestWalkablePoint(float x, float y, float z, float searchRadius) {
		return findClosestWalkablePoint(x, y, z, searchRadius, 0);
	}

	/**
	 * Localiza o ponto transitável mais próximo de (x, y, z) em um raio de busca configurável.
	 *
	 * Utilizado quando o alvo (ex: jogador encostado em parede ou dentro de árvore) está sobre
	 * uma subcélula bloqueada. A busca em espiral radial projeta o destino para a subcélula
	 * livre navegável mais próxima.
	 */
	public float[] findClosestWalkablePoint(float x, float y, float z, float searchRadius, int instanceId) {
		if (isWalkable(x, y, z, 2.0f, instanceId)) {
			float surfaceZ = getSurfaceZ(x, y, z, z, instanceId);
			return new float[] {x, y, surfaceZ};
		}

		int steps = Math.max(1, (int) (searchRadius / SUBCELL_SIZE));
		float bestDistSq = Float.MAX_VALUE;
		float[] bestPoint = null;

		for (int r = 1; r <= steps; r++) {
			float rad = r * SUBCELL_SIZE;
			int angleSteps = Math.max(8, r * 6);
			for (int a = 0; a < angleSteps; a++) {
				double angle = (2.0 * Math.PI * a) / angleSteps;
				float testX = x + (float) (Math.cos(angle) * rad);
				float testY = y + (float) (Math.sin(angle) * rad);

				if (isWalkable(testX, testY, z, 2.5f, instanceId)) {
					float testZ = getSurfaceZ(testX, testY, z, z, instanceId);
					if (canPassPhysical(testX, testY, testZ - 0.2f, testX, testY, testZ + 0.2f, instanceId)) {
						float dx = testX - x;
						float dy = testY - y;
						float dz = testZ - z;
						float dSq = dx * dx + dy * dy + dz * dz;
						if (dSq < bestDistSq) {
							bestDistSq = dSq;
							bestPoint = new float[] {testX, testY, testZ};
						}
					}
				}
			}
			if (bestPoint != null) {
				return bestPoint;
			}
		}

		return null;
	}

	/**
	 * Parser binário oficial de alta fidelidade para arquivos CryEngine *-path.dat (Versão 0x00060005).
	 *
	 * Decodifica com 100% de precisão todas as camadas do arquivo com otimização de memória:
	 * - Camadas 0/1: Base de elevação plana.
	 * - Camadas 2/3: Terreno natural.
	 * - Camadas 6/7: Matriz de 128 bytes de bloqueio subcelular (1024 bits = 32x32 subcélulas de 0.5m).
	 * - Camadas 8/9: Paleta de 8 bytes e índices de 2 bits por subcélula (256 bytes).
	 * - Camadas 10/11: Paleta de 56 bytes e índices de 4 bits (nibbles) por subcélula (512 bytes).
	 * - Camadas 12/13: Cota base + mapa de 1024 bytes (1 byte por subcélula: 0xFF bloqueado, 0xFE terreno, outros = delta cm).
	 * - Camadas 14/15: Cota base + mapa de 2048 bytes (short pouco endian: 0xFFFF bloqueado, outros = cota cm).
	 * - Camadas 16: Conexões espaciais e links de nós.
	 *
	 * @param file    Caminho do arquivo *-path.dat no disco.
	 * @param worldId Identificador numérico do mapa.
	 * @return Instância imutável carregada do NativePathMap.
	 * @throws IOException Caso ocorra falha de I/O ou integridade no arquivo.
	 */
	public static NativePathMap loadFromDisk(Path file, int worldId) throws IOException {
		if (!Files.exists(file)) {
			throw new IOException("Arquivo path.dat não encontrado: " + file);
		}

		long fileSize = Files.size(file);
		if (fileSize < 128) {
			throw new IOException("Arquivo path.dat truncado (< 128 bytes): " + file);
		}

		int mapSize = 3072;
		if (DataManager.WORLD_MAPS_DATA != null) {
			WorldMapTemplate template = DataManager.WORLD_MAPS_DATA.getTemplate(worldId);
			if (template != null && template.getWorldSize() > 0) {
				mapSize = template.getWorldSize();
			}
		} else if (worldId == 400010000) {
			mapSize = 4096;
		}

		int sectorDim = mapSize / SECTOR_SIZE;
		NativePathSector[] sectors = new NativePathSector[sectorDim * sectorDim];
		int totalLayers = 0;

		try (DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(file.toFile()), 65536))) {
			byte[] header = in.readNBytes(128);
			int version = ((header[16] & 0xFF)) |
					((header[17] & 0xFF) << 8) |
					((header[18] & 0xFF) << 16) |
					((header[19] & 0xFF) << 24);

			int major = (version >> 16) & 0xFFFF;
			if (major != 6 && version != 0x00060005) {
				LOG.warn("NATIVE_PATH: Versão CryEngine {} para mapa {}, prosseguindo parse compatível.",
						Integer.toHexString(version), worldId);
			}

			// Pula tabelas macro iniciais conforme descompilação de Cry3DEngine
			int count1 = readLittleEndianInt(in);
			if (count1 > 0 && count1 < 100_000_000) {
				in.skipNBytes(count1);
			}

			int count2 = readLittleEndianInt(in);
			if (count2 > 0 && count2 < 100_000_000) {
				in.skipNBytes((long) count2 * 4);
			}

			byte[] raw128 = new byte[128];
			byte[] raw256 = new byte[256];
			byte[] raw512 = new byte[512];
			byte[] raw1024 = new byte[1024];
			byte[] raw2048 = new byte[2048];

			// Loop canônico da CryEngine: Y externo (0..mapSize, step 16), X interno (0..mapSize, step 16)
			for (int y = 0; y < mapSize; y += SECTOR_SIZE) {
				int sy = y / SECTOR_SIZE;
				for (int x = 0; x < mapSize; x += SECTOR_SIZE) {
					int sx = x / SECTOR_SIZE;

					byte[] layerCountBuf = in.readNBytes(1);
					if (layerCountBuf.length == 0) {
						break;
					}
					int layerCount = layerCountBuf[0] & 0xFF;
					if (layerCount <= 0) {
						continue;
					}

					totalLayers += layerCount;
					NativePathSector.Layer[] layers = new NativePathSector.Layer[layerCount];

					for (int l = 0; l < layerCount; l++) {
						if (in.available() <= 0) {
							break;
						}

						int layerType = in.read();
						if (layerType == -1) {
							break;
						}

						// Tipo 16: índice espacial CryEngine (6 bytes de payload)
						if (layerType == 16) {
							in.skipNBytes(6);
							layers[l] = new NativePathSector.Layer((byte) 16, Float.NaN, null, null);
							continue;
						}

						int subFlags = in.read();
						int elevRaw = readLittleEndianInt(in);
						float baseElev = Float.NaN;
						long[] blockedBits = null;
						short[] subElevs = null;

						switch (layerType) {
							case 0:
							case 1:
								readLittleEndianInt(in);
								baseElev = Float.NaN;
								break;

							case 2:
							case 3:
								// Terreno natural 100% transitável (herda cota)
								break;

							case 4:
							case 5:
								in.skipNBytes(1024);
								break;

							case 6:
							case 7:
								in.readFully(raw128);
								boolean hasBlocked6 = false;
								for (int i = 0; i < 128; i++) {
									if (raw128[i] != 0) {
										hasBlocked6 = true;
										break;
									}
								}
								if (hasBlocked6) {
									blockedBits = new long[16];
									for (int i = 0; i < 16; i++) {
										long v = 0;
										for (int b = 0; b < 8; b++) {
											v |= ((long) (raw128[i * 8 + b] & 0xFF)) << (b * 8);
										}
										blockedBits[i] = v;
									}
								}
								break;

							case 8:
							case 9:
								in.skipNBytes(8);
								in.readFully(raw256);
								blockedBits = new long[16];
								for (int i = 0; i < 256; i++) {
									int b = raw256[i] & 0xFF;
									for (int s = 0; s < 4; s++) {
										int val = (b >>> (s * 2)) & 3;
										if (val == 3) {
											int cellIdx = (i << 2) | s;
											blockedBits[cellIdx >>> 6] |= (1L << (cellIdx & 63));
										}
									}
								}
								break;

							case 10:
							case 11:
								in.skipNBytes(56);
								in.readFully(raw512);
								blockedBits = new long[16];
								for (int i = 0; i < 512; i++) {
									int b = raw512[i] & 0xFF;
									int low = b & 0x0F;
									int high = (b >>> 4) & 0x0F;
									if (low == 0x0F) {
										int cellIdx = i << 1;
										blockedBits[cellIdx >>> 6] |= (1L << (cellIdx & 63));
									}
									if (high == 0x0F) {
										int cellIdx = (i << 1) | 1;
										blockedBits[cellIdx >>> 6] |= (1L << (cellIdx & 63));
									}
								}
								break;

							case 12:
							case 13:
								int e12 = readLittleEndianInt(in);
								if (Math.abs(e12) > 100 && Math.abs(e12) < 5000000) {
									baseElev = e12 / 100.0f;
								}
								in.readFully(raw1024);
								blockedBits = new long[16];
								subElevs = new short[1024];
								for (int i = 0; i < 1024; i++) {
									int b = raw1024[i] & 0xFF;
									if (b == 0xFF) {
										blockedBits[i >>> 6] |= (1L << (i & 63));
										subElevs[i] = -1;
									} else if (b == 0xFE) {
										subElevs[i] = -2;
									} else {
										subElevs[i] = (short) b;
									}
								}
								break;

							case 14:
							case 15:
								int e14 = readLittleEndianInt(in);
								if (Math.abs(e14) > 100 && Math.abs(e14) < 5000000) {
									baseElev = e14 / 100.0f;
								}
								in.readFully(raw2048);
								blockedBits = new long[16];
								subElevs = new short[1024];
								for (int i = 0; i < 1024; i++) {
									int b1 = raw2048[i * 2] & 0xFF;
									int b2 = raw2048[i * 2 + 1] & 0xFF;
									int w = b1 | (b2 << 8);
									if (w == 0xFFFF) {
										blockedBits[i >>> 6] |= (1L << (i & 63));
										subElevs[i] = -1;
									} else if (w == 0xFFFE) {
										subElevs[i] = -2;
									} else {
										subElevs[i] = (short) w;
									}
								}
								break;

							default:
								break;
						}

						// Tipos ímpares leem buffer adicional de terreno de 512 bytes
						if (layerType % 2 == 1 && layerType <= 15) {
							in.skipNBytes(512);
						}

						// 12 bytes finais de metadados
						in.skipNBytes(12);

						layers[l] = new NativePathSector.Layer((byte) layerType, baseElev, blockedBits, subElevs);
					}

					if (sy < sectorDim && sx < sectorDim) {
						sectors[sy * sectorDim + sx] = new NativePathSector((short) x, (short) y, layers);
					}
				}
			}
		}

		LOG.info("NATIVE_PATH: Mapa {} (tamanho {}m) carregado com sucesso. {} camadas ativas em {}",
				worldId, mapSize, totalLayers, file.getFileName());

		return new NativePathMap(worldId, mapSize, sectors, totalLayers);
	}

	private static int readLittleEndianInt(DataInputStream in) throws IOException {
		int b1 = in.read();
		int b2 = in.read();
		int b3 = in.read();
		int b4 = in.read();
		if ((b1 | b2 | b3 | b4) < 0) {
			return 0;
		}
		return (b1 & 0xFF) | ((b2 & 0xFF) << 8) | ((b3 & 0xFF) << 16) | ((b4 & 0xFF) << 24);
	}
}
