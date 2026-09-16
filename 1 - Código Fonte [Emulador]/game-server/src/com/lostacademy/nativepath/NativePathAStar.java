package com.lostacademy.nativepath;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.BitSet;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Algoritmo A* de alto desempenho na grade de nós nativa CryEngine, com suavização
 * de trajetória por linha de visão (String-Pulling).
 *
 * @author KAMIDAKI
 */
public final class NativePathAStar {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathAStar.class);

	private static final int MAX_EXPLORED_NODES = 3500;
	private static final float MAX_SAFE_STEP_DROP = 2.5f;

	private NativePathAStar() {
	}

	/**
	 * Calcula o caminho ideal entre duas coordenadas de mundo utilizando a malha nativa CryEngine.
	 * Retorna float[][] compatível com os controladores de movimento do emulador.
	 */
	public static float[][] findPath(NativePathMap map, float startX, float startY, float startZ,
									 float targetX, float targetY, float targetZ) {
		if (map == null || map.getNodeCount() == 0) {
			return null;
		}

		// Se há linha de visão direta sem desnível excessivo, retorna direto o destino
		if (map.hasLineOfSight(startX, startY, startZ, targetX, targetY, targetZ, MAX_SAFE_STEP_DROP)) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		// Localiza os nós mais próximos de início e fim
		NativePathNode startNode = map.findClosestNode(startX, startY, startZ, 8.0f);
		if (startNode == null) {
			return null;
		}

		NativePathNode targetNode = map.findClosestNode(targetX, targetY, targetZ, 8.0f);
		if (targetNode == null) {
			return null;
		}

		if (startNode.getId() == targetNode.getId()) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		// Executa A*
		List<NativePathNode> nodePath = executeAStar(map, startNode, targetNode);
		if (nodePath == null || nodePath.isEmpty()) {
			return null;
		}

		// Suavização da rota eliminando waypoints redundantes
		List<float[]> smoothedWaypoints = smoothPath(map, nodePath, startX, startY, startZ, targetX, targetY, targetZ);
		return smoothedWaypoints.toArray(new float[0][]);
	}

	private static List<NativePathNode> executeAStar(NativePathMap map, NativePathNode startNode, NativePathNode goalNode) {
		int nodeCount = map.getNodeCount();
		PriorityQueue<AStarItem> openSet = new PriorityQueue<>(64);
		Map<Integer, Float> gScore = new HashMap<>(128);
		Map<Integer, Integer> cameFrom = new HashMap<>(128);
		BitSet closedSet = new BitSet(nodeCount);

		gScore.put(startNode.getId(), 0.0f);
		openSet.add(new AStarItem(startNode.getId(), heuristic(startNode, goalNode)));

		int iterations = 0;

		while (!openSet.isEmpty() && iterations++ < MAX_EXPLORED_NODES) {
			AStarItem currentItem = openSet.poll();
			int currentId = currentItem.nodeId;

			if (currentId == goalNode.getId()) {
				return reconstructPath(map, cameFrom, currentId);
			}

			if (closedSet.get(currentId)) {
				continue;
			}
			closedSet.set(currentId);

			NativePathNode currentNode = map.getNode(currentId);
			if (currentNode == null)
				continue;

			float currentG = gScore.getOrDefault(currentId, Float.POSITIVE_INFINITY);

			for (int neighborId : currentNode.getNeighborIds()) {
				if (closedSet.get(neighborId)) {
					continue;
				}

				NativePathNode neighborNode = map.getNode(neighborId);
				if (neighborNode == null) {
					continue;
				}

				float stepDist = currentNode.distanceTo(neighborNode);
				float tentativeG = currentG + stepDist;

				float oldG = gScore.getOrDefault(neighborId, Float.POSITIVE_INFINITY);
				if (tentativeG < oldG) {
					cameFrom.put(neighborId, currentId);
					gScore.put(neighborId, tentativeG);
					float fScore = tentativeG + heuristic(neighborNode, goalNode);
					openSet.add(new AStarItem(neighborId, fScore));
				}
			}
		}

		return null;
	}

	private static float heuristic(NativePathNode a, NativePathNode b) {
		return a.distanceTo(b);
	}

	private static List<NativePathNode> reconstructPath(NativePathMap map, Map<Integer, Integer> cameFrom, int currentId) {
		List<NativePathNode> path = new ArrayList<>();
		Integer curr = currentId;
		while (curr != null) {
			NativePathNode node = map.getNode(curr);
			if (node != null) {
				path.add(node);
			}
			curr = cameFrom.get(curr);
		}
		Collections.reverse(path);
		return path;
	}

	/**
	 * Suaviza os nós usando String-Pulling para gerar uma trajetória fluida e natural.
	 */
	private static List<float[]> smoothPath(NativePathMap map, List<NativePathNode> nodes,
											float startX, float startY, float startZ,
											float targetX, float targetY, float targetZ) {
		List<float[]> waypoints = new ArrayList<>();
		if (nodes.isEmpty()) {
			waypoints.add(new float[] {targetX, targetY, targetZ});
			return waypoints;
		}

		int currentIndex = 0;
		while (currentIndex < nodes.size() - 1) {
			int furthestIndex = currentIndex + 1;
			// Tenta avançar o mais longe possível com linha de visão desobstruída
			for (int testIndex = nodes.size() - 1; testIndex > currentIndex; testIndex--) {
				NativePathNode currNode = nodes.get(currentIndex);
				NativePathNode testNode = nodes.get(testIndex);
				if (map.hasLineOfSight(currNode.getX(), currNode.getY(), currNode.getZ(),
					testNode.getX(), testNode.getY(), testNode.getZ(), MAX_SAFE_STEP_DROP)) {
					furthestIndex = testIndex;
					break;
				}
			}

			NativePathNode nextTarget = nodes.get(furthestIndex);
			waypoints.add(new float[] {nextTarget.getX(), nextTarget.getY(), nextTarget.getZ()});
			currentIndex = furthestIndex;
		}

		// Adiciona o ponto final exato
		if (waypoints.isEmpty()) {
			waypoints.add(new float[] {targetX, targetY, targetZ});
		} else {
			float[] last = waypoints.get(waypoints.size() - 1);
			float dSq = (last[0] - targetX) * (last[0] - targetX) + (last[1] - targetY) * (last[1] - targetY);
			if (dSq > 1.0f) {
				waypoints.add(new float[] {targetX, targetY, targetZ});
			} else {
				waypoints.set(waypoints.size() - 1, new float[] {targetX, targetY, targetZ});
			}
		}

		return waypoints;
	}

	private static class AStarItem implements Comparable<AStarItem> {
		final int nodeId;
		final float fScore;

		AStarItem(int nodeId, float fScore) {
			this.nodeId = nodeId;
			this.fScore = fScore;
		}

		@Override
		public int compareTo(AStarItem other) {
			return Float.compare(this.fScore, other.fScore);
		}
	}
}
