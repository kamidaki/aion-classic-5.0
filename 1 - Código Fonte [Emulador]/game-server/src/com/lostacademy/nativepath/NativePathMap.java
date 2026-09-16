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
	 * Localiza o nó transitável mais próximo da coordenada 3D fornecida dentro do raio máximo.
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
		float bestDistSq = maxRadiusSq;

		for (int cx = minCx; cx <= maxCx; cx++) {
			for (int cy = minCy; cy <= maxCy; cy++) {
				long key = (((long) cx) << 32) | (cy & 0xFFFFFFFFL);
				int[] cellNodes = spatialGrid.get(key);
				if (cellNodes == null)
					continue;

				for (int nodeIdx : cellNodes) {
					NativePathNode node = nodes[nodeIdx];
					float distSq = node.distanceSquaredTo(x, y, z);
					if (distSq < bestDistSq) {
						bestDistSq = distSq;
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
	 */
	public boolean hasLineOfSight(float x1, float y1, float z1, float x2, float y2, float z2, float maxDropHeight) {
		float dx = x2 - x1;
		float dy = y2 - y1;
		float dz = z2 - z1;
		float dist2D = (float) Math.hypot(dx, dy);

		if (dist2D < 0.5f) {
			return Math.abs(dz) <= maxDropHeight;
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
	 * Carrega e faz o parse binário de um arquivo *-path.dat do CryEngine.
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

			List<NativePathNode> parsedNodes = new ArrayList<>(Math.min(50000, (int) (fileSize / 147)));
			int nodeId = 0;
			short gridX = 0;
			short gridY = 0;

			// Loop de leitura da grade CryEngine
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

						// Leitura do registro do nó (formato padrão CryEngine ~145 bytes)
						int subType = in.read();
						int elevRaw = readLittleEndianInt(in);

						byte[] mask = in.readNBytes(128);
						byte[] connections = in.readNBytes(12);

						float worldX = (gridX + 16) * GRID_SCALE;
						float worldY = (gridY + 16) * GRID_SCALE;
						float worldZ = (float) elevRaw;
						if (Float.isNaN(worldZ) || Math.abs(worldZ) > 10000f) {
							worldZ = 0.0f;
						}

						int[] neighborIds = parseNeighbors(nodeId, connections);

						parsedNodes.add(new NativePathNode(nodeId++, worldX, worldY, worldZ,
							gridX, gridY, (byte) layerType, neighborIds));
					}
				}

				gridX += 16;
				if (gridX >= 4096) {
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

	private static int[] parseNeighbors(int currentId, byte[] connections) {
		if (connections == null || connections.length < 4) {
			return new int[0];
		}
		List<Integer> list = new ArrayList<>(4);
		for (int i = 0; i < connections.length - 3; i += 4) {
			int nId = (connections[i] & 0xFF) |
				((connections[i + 1] & 0xFF) << 8) |
				((connections[i + 2] & 0xFF) << 16) |
				((connections[i + 3] & 0xFF) << 24);
			if (nId >= 0 && nId != currentId && nId < 100_000_000) {
				list.add(nId);
			}
		}
		int[] res = new int[list.size()];
		for (int i = 0; i < list.size(); i++) {
			res[i] = list.get(i);
		}
		return res;
	}

	/**
	 * Conecta nós adjacentes espacialmente (até 8 direções na grade de 8m) para garantir conectividade perfeita.
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
			if (node.getNeighborIds().length > 0)
				continue;

			List<Integer> neighbors = new ArrayList<>(8);
			for (int dir = 0; dir < 8; dir++) {
				short nx = (short) (node.getGridX() + dx[dir]);
				short ny = (short) (node.getGridY() + dy[dir]);
				long key = (((long) nx) << 32) | (ny & 0xFFFFFFFFL);
				List<Integer> candList = gridPosMap.get(key);
				if (candList != null) {
					for (int candIdx : candList) {
						NativePathNode cand = array[candIdx];
						if (Math.abs(cand.getZ() - node.getZ()) <= 3.0f) {
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
