package com.lostacademy.nativepath;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.templates.world.WorldMapTemplate;
import com.aionemu.gameserver.world.geo.GeoService;

/**
 * Representação em memória da malha de navegação nativa CryEngine (*-path.dat).
 * Contém os nós da grade, indexação espacial em grade hash para buscas O(1) e
 * métodos de verificação de transitabilidade e visibilidade linear.
 *
 * @author KAMIDAKI
 */
public final class NativePathMap {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathMap.class);

	private static final float SPATIAL_CELL_SIZE = 16.0f;
	private static final float GRID_SCALE = 0.5f;

	private final int worldId;
	private final NativePathNode[] nodes;
	private final Map<Long, int[]> spatialGrid;
	private final long estimatedSizeMB;

	public NativePathMap(int worldId, NativePathNode[] nodes) {
		this.worldId = worldId;
		this.nodes = nodes != null ? nodes : new NativePathNode[0];
		this.spatialGrid = buildSpatialGrid(this.nodes);
		this.estimatedSizeMB = Math.max(1, (this.nodes.length * 128L) / (1024 * 1024));
	}

	public int getWorldId() {
		return worldId;
	}

	public int getNodeCount() {
		return nodes.length;
	}

	public NativePathNode getNode(int id) {
		if (id >= 0 && id < nodes.length) {
			return nodes[id];
		}
		return null;
	}

	public NativePathNode[] getNodes() {
		return nodes;
	}

	public long getEstimatedSizeMB() {
		return estimatedSizeMB;
	}

	/**
	 * Constrói o índice espacial em células 2D de 16x16 metros para buscas O(1).
	 */
	private static Map<Long, int[]> buildSpatialGrid(NativePathNode[] nodeList) {
		Map<Long, List<Integer>> cellMap = new HashMap<>();
		for (int i = 0; i < nodeList.length; i++) {
			NativePathNode node = nodeList[i];
			int cx = (int) Math.floor(node.getX() / SPATIAL_CELL_SIZE);
			int cy = (int) Math.floor(node.getY() / SPATIAL_CELL_SIZE);
			long key = (((long) cx) << 32) | (cy & 0xFFFFFFFFL);
			cellMap.computeIfAbsent(key, k -> new ArrayList<>()).add(i);
		}

		Map<Long, int[]> result = new HashMap<>(cellMap.size());
		for (Map.Entry<Long, List<Integer>> entry : cellMap.entrySet()) {
			List<Integer> list = entry.getValue();
			int[] arr = new int[list.size()];
			for (int j = 0; j < list.size(); j++) {
				arr[j] = list.get(j);
			}
			result.put(entry.getKey(), arr);
		}
		return result;
	}

	/**
	 * Localiza o nó transitável mais próximo da coordenada 3D fornecida dentro do raio máximo,
	 * aplicando penalidade vertical (3.0x) para priorizar a camada navegável correta (evita
	 * selecionar piso de ponte quando a entidade está embaixo, ou água quando está sobre a ponte).
	 */
	public NativePathNode findClosestNode(float x, float y, float z, float maxRadius) {
		if (nodes.length == 0)
			return null;

		float maxRadiusSq = maxRadius * maxRadius;
		int minCx = (int) Math.floor((x - maxRadius) / SPATIAL_CELL_SIZE);
		int maxCx = (int) Math.floor((x + maxRadius) / SPATIAL_CELL_SIZE);
		int minCy = (int) Math.floor((y - maxRadius) / SPATIAL_CELL_SIZE);
		int maxCy = (int) Math.floor((y + maxRadius) / SPATIAL_CELL_SIZE);

		NativePathNode bestNode = null;
		float bestScore = Float.MAX_VALUE;

		for (int cx = minCx; cx <= maxCx; cx++) {
			for (int cy = minCy; cy <= maxCy; cy++) {
				long key = (((long) cx) << 32) | (cy & 0xFFFFFFFFL);
				int[] cellNodes = spatialGrid.get(key);
				if (cellNodes == null)
					continue;

				for (int nodeIdx : cellNodes) {
					NativePathNode node = nodes[nodeIdx];
					float dx = node.getX() - x;
					float dy = node.getY() - y;
					float dz = node.getZ() - z;
					float dist2DSq = dx * dx + dy * dy;
					if (dist2DSq > maxRadiusSq)
						continue;

					// Rejeita nós com desnível vertical desproporcional
					if (Math.abs(dz) > Math.max(3.5f, maxRadius * 0.75f))
						continue;

					// Ponderação vertical (3.0x): distância horizontal prevalece sobre salto vertical
					float score = dist2DSq + (dz * 3.0f) * (dz * 3.0f);
					if (score < bestScore) {
						bestScore = score;
						bestNode = node;
					}
				}
			}
		}

		return bestNode;
	}

	/**
	 * Retorna a elevação Z da superfície navegável na coordenada (x, y).
	 */
	public float getSurfaceZ(float x, float y, float fallbackZ) {
		NativePathNode closest = findClosestNode(x, y, fallbackZ, 6.0f);
		if (closest != null) {
			return closest.getZ();
		}
		return fallbackZ;
	}

	/**
	 * Verifica se a coordenada está sobre uma malha transitável.
	 */
	public boolean isWalkable(float x, float y, float z, float tolerance) {
		return findClosestNode(x, y, z, tolerance) != null;
	}

	/**
	 * Verifica linha de visão desobstruída entre dois pontos sobre nós navegáveis (String-Pulling / Raycast).
	 * Valida inclinação máxima do terreno e continuidade de superfície transitável passo a passo.
	 */
	public boolean hasLineOfSight(float x1, float y1, float z1, float x2, float y2, float z2, float maxDropHeight) {
		float dx = x2 - x1;
		float dy = y2 - y1;
		float dz = z2 - z1;
		float dist2D = (float) Math.hypot(dx, dy);

		if (dist2D < 0.5f) {
			return Math.abs(dz) <= maxDropHeight;
		}

		// Validação de inclinação: rejeita segmentos com rampa excessivamente íngreme (> ~50 graus)
		if (Math.abs(dz) / dist2D > 1.2f) {
			return false;
		}

		int steps = Math.max(1, (int) Math.ceil(dist2D / 1.0f));
		float stepX = dx / steps;
		float stepY = dy / steps;
		float stepZ = dz / steps;

		float currX = x1;
		float currY = y1;
		float currZ = z1;

		for (int i = 1; i <= steps; i++) {
			currX += stepX;
			currY += stepY;
			currZ += stepZ;

			NativePathNode node = findClosestNode(currX, currY, currZ, 2.5f);
			if (node == null) {
				return false;
			}
			if (Math.abs(node.getZ() - currZ) > maxDropHeight) {
				return false;
			}
		}

		return true;
	}

	/**
	 * Carrega e faz o parse binário exato de um arquivo *-path.dat oficial do CryEngine.
	 * Decodifica o fluxo polimórfico de camadas conforme engenharia reversa do Cry3DEngine.dll.
	 */
	public static NativePathMap loadFromDisk(Path file, int worldId) throws IOException {
		if (!Files.exists(file)) {
			throw new IOException("Arquivo path.dat não encontrado: " + file);
		}

		long fileSize = Files.size(file);
		if (fileSize < 128) {
			throw new IOException("Arquivo path.dat truncado (tamanho < 128 bytes): " + file);
		}

		try (DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(file.toFile()), 65536))) {
			byte[] header = in.readNBytes(128);
			int version = ((header[16] & 0xFF)) |
				((header[17] & 0xFF) << 8) |
				((header[18] & 0xFF) << 16) |
				((header[19] & 0xFF) << 24);

			int major = (version >> 16) & 0xFFFF;
			if (major != 6 && version != 0x00060005) {
				LOG.warn("NATIVE_PATH: Versao CryEngine inesperada ({}) para mapa {}, prosseguindo parse compativel.",
					Integer.toHexString(version), worldId);
			}

			// Leitura das tabelas iniciais
			int count1 = readLittleEndianInt(in);
			if (count1 > 0 && count1 < 100_000_000) {
				in.skipNBytes(count1);
			}

			int count2 = readLittleEndianInt(in);
			if (count2 > 0 && count2 < 100_000_000) {
				in.skipNBytes((long) count2 * 4);
			}

			// Determina dimensão do mapa
			int mapSize = 3072;
			if (DataManager.WORLD_MAPS_DATA != null) {
				WorldMapTemplate template = DataManager.WORLD_MAPS_DATA.getTemplate(worldId);
				if (template != null && template.getWorldSize() > 0) {
					mapSize = template.getWorldSize();
				}
			}

			List<NativePathNode> parsedNodes = new ArrayList<>(Math.min(60000, (int) (fileSize / 80)));
			int nodeId = 0;
			short gridX = 0;
			short gridY = 0;

			// Loop de leitura da grade de setores CryEngine
			while (in.available() > 0) {
				int layerCount = in.read();
				if (layerCount == -1)
					break;

				if (layerCount > 0) {
					for (int l = 0; l < layerCount; l++) {
						if (in.available() <= 0)
							break;

						int layerType = in.read();
						if (layerType == -1)
							break;

						// Tipo 16: índice espacial CryEngine (6 bytes de payload)
						if (layerType == 16) {
							in.skipNBytes(6);
							continue;
						}

						int subType = in.read();
						int elevRaw = readLittleEndianInt(in);

						// Decodificação polimórfica de payload por tipo de layer CryEngine
						switch (layerType) {
							case 0:
							case 1:
								in.skipNBytes(4);
								break;
							case 2:
							case 3:
								// Sem máscara
								break;
							case 4:
							case 5:
								in.skipNBytes(1024);
								break;
							case 6:
							case 7:
								in.skipNBytes(128);
								break;
							case 8:
							case 9:
								in.skipNBytes(8 + 256);
								break;
							case 10:
							case 11:
								in.skipNBytes(56 + 512);
								break;
							case 12:
							case 13:
								in.skipNBytes(4 + 1024);
								break;
							case 14:
							case 15:
								in.skipNBytes(4 + 2048);
								break;
							default:
								LOG.warn("NATIVE_PATH: Layer desconhecido {} em mapa {}", layerType, worldId);
								break;
						}

						// Tipos ímpares leem buffer adicional de terreno de 512 bytes
						if (layerType % 2 == 1 && layerType <= 15) {
							in.skipNBytes(512);
						}

						// 12 bytes finais de conexões / metadados
						in.skipNBytes(12);

						// Cálculo exato de coordenadas de mundo CryEngine: centro da célula de 16m
						float worldX = gridX + 8.0f;
						float worldY = gridY + 8.0f;

						// No CryEngine elevRaw é armazenado em centímetros como inteiro (cvtdq2ps / divss 100.0f)
						float worldZ = elevRaw / 100.0f;

						// Se GeoService estiver disponível e a altitude nativa for nula/padrão, obtém Z sub-métrico do terreno
						try {
							if (GeoService.getInstance() != null) {
								float geoZ = GeoService.getInstance().getZ(worldId, worldX, worldY);
								if (!Float.isNaN(geoZ) && geoZ > -500.0f && geoZ < 5000.0f) {
									// Se a elevação nativa for 0 (nível base) ou inconsistente, usa geoZ
									if (Math.abs(worldZ) < 0.5f || Math.abs(worldZ - geoZ) > 40.0f || worldZ < -500.0f || worldZ > 5000.0f) {
										worldZ = geoZ;
									}
								}
							}
						} catch (Throwable ignored) {
						}

						if (worldZ < -500.0f || worldZ > 5000.0f) {
							worldZ = 0.0f;
						}

						parsedNodes.add(new NativePathNode(nodeId++, worldX, worldY, worldZ,
							gridX, gridY, (byte) layerType, new int[0]));
					}
				}

				gridX += 16;
				if (gridX >= mapSize) {
					gridX = 0;
					gridY += 16;
				}
			}

			NativePathNode[] array = parsedNodes.toArray(new NativePathNode[0]);
			connectAdjacentNodes(array);

			LOG.info("NATIVE_PATH: Mapa {} carregado com sucesso. {} nós gerados a partir de {}",
				worldId, array.length, file.getFileName());

			return new NativePathMap(worldId, array);
		}
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

	/**
	 * Conecta nós adjacentes espacialmente (até 8 direções na grade de 16m) com limite estrito
	 * de desnível vertical (delta Z <= 2.5m) para prevenir saltos impossíveis sobre água ou entre pontes.
	 */
	private static void connectAdjacentNodes(NativePathNode[] array) {
		if (array.length == 0)
			return;

		Map<Long, List<Integer>> gridPosMap = new HashMap<>(array.length);
		for (int i = 0; i < array.length; i++) {
			NativePathNode node = array[i];
			long key = (((long) node.getGridX()) << 32) | (node.getGridY() & 0xFFFFFFFFL);
			gridPosMap.computeIfAbsent(key, k -> new ArrayList<>()).add(i);
		}

		short[] dx = {16, -16, 0, 0, 16, 16, -16, -16};
		short[] dy = {0, 0, 16, -16, 16, -16, 16, -16};

		for (NativePathNode node : array) {
			List<Integer> neighbors = new ArrayList<>(8);
			for (int dir = 0; dir < 8; dir++) {
				short nx = (short) (node.getGridX() + dx[dir]);
				short ny = (short) (node.getGridY() + dy[dir]);
				long key = (((long) nx) << 32) | (ny & 0xFFFFFFFFL);
				List<Integer> candList = gridPosMap.get(key);
				if (candList != null) {
					for (int candIdx : candList) {
						NativePathNode cand = array[candIdx];
						// Limite estrito de rampa caminhável (2.5m) para não atravessar parapeitos ou pontes suspensas
						if (Math.abs(cand.getZ() - node.getZ()) <= 2.5f) {
							neighbors.add(cand.getId());
						}
					}
				}
			}

			if (!neighbors.isEmpty()) {
				int[] newNeighbors = new int[neighbors.size()];
				for (int i = 0; i < neighbors.size(); i++) {
					newNeighbors[i] = neighbors.get(i);
				}
				node.setNeighborIds(newNeighbors);
			}
		}
	}
}
