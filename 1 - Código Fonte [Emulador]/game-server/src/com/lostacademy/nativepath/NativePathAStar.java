package com.lostacademy.nativepath;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Algoritmo A* híbrido de alto desempenho na grade nativa CryEngine (precisão 0.5m),
 * com suavização por String-Pulling (Funnel Algorithm) para contorno fluido de obstáculos.
 *
 * Características da Implementação Oficial:
 * 1. Resolução Subcelular de 0.5m: contorno preciso de quinas, pilares, portas e cercas.
 * 2. Ordenação Canônica A* f(n) = g(n) + h(n): desempate inteligente pelo menor h(n).
 * 3. Física de Locomoção Assimétrica: limite de subida de degraus (0.8m) e queda (1.8m).
 * 4. Folga Lateral de Raio (Clearance): cálculo baseado no raio de colisão do monstro/agente.
 * 5. Parada por Alcance (Reach Distance): encerra a busca quando o agente atinge alcance de ataque.
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathAStar {

	/**
	 * Limite máximo de nós explorados na busca local de alta resolução (0.5m).
	 */
	private static final int MAX_LOCAL_EXPLORED_CELLS = 3000;

	/**
	 * Limite máximo de nós explorados na busca macro (8m/16m).
	 */
	private static final int MAX_MACRO_EXPLORED_NODES = 1500;

	/**
	 * Altura máxima de degrau (subida vertical) sem pular (0.8 metros).
	 */
	public static final float MAX_STEP_UP = 0.8f;

	/**
	 * Altura máxima de desnível/queda (descida vertical) permitida (1.8 metros).
	 */
	public static final float MAX_DROP_DOWN = 1.8f;

	/**
	 * Distância máxima plana para utilização da grade de 0.5m (60 metros).
	 */
	private static final float LOCAL_SEARCH_MAX_DIST = 60.0f;

	private NativePathAStar() {
	}

	/**
	 * Calcula o percurso navegável ótimo entre dois pontos de mundo com parâmetros padrão de agente.
	 *
	 * @param map     Instância do mapa de navegação CryEngine.
	 * @param startX  Coordenada X inicial em metros.
	 * @param startY  Coordenada Y inicial em metros.
	 * @param startZ  Coordenada Z inicial em metros.
	 * @param targetX Coordenada X do destino em metros.
	 * @param targetY Coordenada Y do destino em metros.
	 * @param targetZ Coordenada Z do destino em metros.
	 * @return Matriz float[][] com os waypoints (x, y, z) transitáveis, ou null se rota inacessível.
	 */
	public static float[][] findPath(NativePathMap map, float startX, float startY, float startZ,
									 float targetX, float targetY, float targetZ) {
		return findPath(map, startX, startY, startZ, targetX, targetY, targetZ, 0.5f, 0.0f);
	}

	/**
	 * Calcula o percurso navegável ótimo considerando o raio de colisão do agente e distância de alcance.
	 *
	 * @param map           Instância do mapa de navegação CryEngine.
	 * @param startX        Coordenada X inicial em metros.
	 * @param startY        Coordenada Y inicial em metros.
	 * @param startZ        Coordenada Z inicial em metros.
	 * @param targetX       Coordenada X do destino em metros.
	 * @param targetY       Coordenada Y do destino em metros.
	 * @param targetZ       Coordenada Z do destino em metros.
	 * @param agentRadius   Raio de colisão do agente em metros (folga lateral).
	 * @param reachDistance Distância de parada aceitável (ex: alcance de ataque em metros).
	 * @return Matriz float[][] com waypoints desobstruídos, ou null se inacessível.
	 */
	public static float[][] findPath(NativePathMap map, float startX, float startY, float startZ,
									 float targetX, float targetY, float targetZ,
									 float agentRadius, float reachDistance) {
		if (map == null) {
			return null;
		}

		float dist2D = (float) Math.hypot(targetX - startX, targetY - startY);

		// Se o agente já estiver no raio de alcance e com linha de visão livre, encerra imediatamente
		if (reachDistance > 0.0f && dist2D <= reachDistance) {
			if (map.hasLineOfSight(startX, startY, startZ, targetX, targetY, targetZ, MAX_DROP_DOWN)) {
				return new float[][] {{targetX, targetY, targetZ}};
			}
		}

		// 1. Linha de visão direta rápida (sem obstáculos 3D, sem quinas e sem desníveis excessivos)
		if (map.hasLineOfSight(startX, startY, startZ, targetX, targetY, targetZ, MAX_DROP_DOWN)) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		if (dist2D < 0.5f) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		// Garante que os pontos inicial e final estão sobre superfícies transitáveis válidas
		float[] validStart = map.findClosestWalkablePoint(startX, startY, startZ, 3.0f);
		float sX = validStart != null ? validStart[0] : startX;
		float sY = validStart != null ? validStart[1] : startY;
		float sZ = validStart != null ? validStart[2] : startZ;

		float[] validTarget = map.findClosestWalkablePoint(targetX, targetY, targetZ, 4.0f);
		float tX = validTarget != null ? validTarget[0] : targetX;
		float tY = validTarget != null ? validTarget[1] : targetY;
		float tZ = validTarget != null ? validTarget[2] : targetZ;

		// 2. Busca local de alta resolução (grade de 0.5m) para combate e perseguição (distância <= 60m)
		if (dist2D <= LOCAL_SEARCH_MAX_DIST) {
			List<float[]> rawPath = executeSubcellAStar(map, sX, sY, sZ, tX, tY, tZ, agentRadius, reachDistance);
			if (rawPath != null && !rawPath.isEmpty()) {
				List<float[]> smoothed = smoothPath(map, rawPath, tX, tY, tZ);
				return smoothed.toArray(new float[0][]);
			}
		}

		// 3. Busca macro (nós de 8m) para longas distâncias (retorno ao spawn / patrulhas extensas)
		List<float[]> macroPath = executeMacroAStar(map, sX, sY, sZ, tX, tY, tZ);
		if (macroPath != null && !macroPath.isEmpty()) {
			List<float[]> smoothed = smoothPath(map, macroPath, tX, tY, tZ);
			return smoothed.toArray(new float[0][]);
		}

		return null;
	}

	/**
	 * A* preciso na grade nativa de 0.5m com ordenação estrita f(n) = g(n) + h(n).
	 *
	 * @param map           Instância do mapa de navegação.
	 * @param startX        X inicial.
	 * @param startY        Y inicial.
	 * @param startZ        Z inicial.
	 * @param targetX       X final.
	 * @param targetY       Y final.
	 * @param targetZ       Z final.
	 * @param agentRadius   Raio de colisão do agente.
	 * @param reachDistance Alcance de parada.
	 * @return Lista de pontos brutos do caminho ou null se inacessível.
	 */
	private static List<float[]> executeSubcellAStar(NativePathMap map, float startX, float startY, float startZ,
													float targetX, float targetY, float targetZ,
													float agentRadius, float reachDistance) {
		int startGx = Math.round(startX * 2.0f);
		int startGy = Math.round(startY * 2.0f);
		int goalGx = Math.round(targetX * 2.0f);
		int goalGy = Math.round(targetY * 2.0f);

		long startKey = packGridKey(startGx, startGy);

		PriorityQueue<GridNode> openSet = new PriorityQueue<>(256);
		Map<Long, Float> gScore = new HashMap<>(4096);
		Map<Long, GridNode> cameFrom = new HashMap<>(4096);
		Set<Long> closedSet = new HashSet<>(4096);

		float initialH = heuristic(startX, startY, targetX, targetY);
		GridNode startNode = new GridNode(startGx, startGy, startZ, 0.0f, initialH);
		openSet.add(startNode);
		gScore.put(startKey, 0.0f);

		int iterations = 0;
		int[] dx = {1, -1, 0, 0, 1, 1, -1, -1};
		int[] dy = {0, 0, 1, -1, 1, -1, 1, -1};
		float[] moveCost = {0.5f, 0.5f, 0.5f, 0.5f, 0.7071f, 0.7071f, 0.7071f, 0.7071f};

		GridNode closestToGoal = startNode;
		float minHeuristic = initialH;

		while (!openSet.isEmpty() && iterations++ < MAX_LOCAL_EXPLORED_CELLS) {
			GridNode current = openSet.poll();
			long currentKey = packGridKey(current.gx, current.gy);

			// Condição de chegada 1: alcançou a célula exata do objetivo
			if (current.gx == goalGx && current.gy == goalGy) {
				return reconstructGridPath(cameFrom, current, targetX, targetY, targetZ);
			}

			// Condição de chegada 2: alcançou a distância de parada/ataque com linha de visão
			if (reachDistance > 0.0f && current.h <= reachDistance) {
				float cWorldX = current.gx * 0.5f;
				float cWorldY = current.gy * 0.5f;
				if (map.hasLineOfSight(cWorldX, cWorldY, current.z, targetX, targetY, targetZ, MAX_DROP_DOWN)) {
					return reconstructGridPath(cameFrom, current, targetX, targetY, targetZ);
				}
			}

			if (closedSet.contains(currentKey)) {
				continue;
			}
			closedSet.add(currentKey);

			float currentWorldX = current.gx * 0.5f;
			float currentWorldY = current.gy * 0.5f;

			for (int dir = 0; dir < 8; dir++) {
				int nextGx = current.gx + dx[dir];
				int nextGy = current.gy + dy[dir];
				long nextKey = packGridKey(nextGx, nextGy);

				if (closedSet.contains(nextKey)) {
					continue;
				}

				float nextWorldX = nextGx * 0.5f;
				float nextWorldY = nextGy * 0.5f;

				// Prevenção estrita de "Corner Cutting": movimentos diagonais exigem ambos vizinhos ortogonais livres
				if (dir >= 4) {
					if (!map.isWalkable(currentWorldX + dx[dir] * 0.5f, currentWorldY, current.z, 1.5f) ||
							!map.isWalkable(currentWorldX, currentWorldY + dy[dir] * 0.5f, current.z, 1.5f)) {
						continue;
					}
				}

				// Verifica transitabilidade da subcélula destino
				if (!map.isWalkable(nextWorldX, nextWorldY, current.z, 1.8f)) {
					continue;
				}

				// Folga lateral (Clearance) para agentes de raio avantajado (> 0.6m)
				if (agentRadius > 0.6f) {
					float clearanceOffset = agentRadius * 0.5f;
					if (!map.isWalkable(nextWorldX + clearanceOffset, nextWorldY, current.z, 1.5f) ||
							!map.isWalkable(nextWorldX - clearanceOffset, nextWorldY, current.z, 1.5f) ||
							!map.isWalkable(nextWorldX, nextWorldY + clearanceOffset, current.z, 1.5f) ||
							!map.isWalkable(nextWorldX, nextWorldY - clearanceOffset, current.z, 1.5f)) {
						continue;
					}
				}

				// Validação física de elevação assimétrica (subida máx 0.8m / queda máx 1.8m)
				float nextZ = map.getSurfaceZ(nextWorldX, nextWorldY, current.z, current.z);
				float deltaZ = nextZ - current.z;

				if (deltaZ > MAX_STEP_UP) { // Degrau muito alto para subir
					continue;
				}
				if (-deltaZ > MAX_DROP_DOWN) { // Desnível muito profundo para descer
					continue;
				}

				// Custo energético: subir rampa custa mais (proporcional ao custo de movimento), descida é barata
				// A proporcionalidade garante que diagonal (já mais cara) penaliza rampas adequadamente
				float slopeCost = deltaZ > 0 ? deltaZ * 2.0f * moveCost[dir] : -deltaZ * 0.2f * moveCost[dir];
				float tentativeG = current.g + moveCost[dir] + slopeCost;
				float oldG = gScore.getOrDefault(nextKey, Float.POSITIVE_INFINITY);

				if (tentativeG < oldG) {
					float h = heuristic(nextWorldX, nextWorldY, targetX, targetY);
					GridNode neighbor = new GridNode(nextGx, nextGy, nextZ, tentativeG, h);
					cameFrom.put(nextKey, current);
					gScore.put(nextKey, tentativeG);
					openSet.add(neighbor);

					if (h < minHeuristic) {
						minHeuristic = h;
						closestToGoal = neighbor;
					}
				}
			}
		}

		// Se a busca esgotou as iterações mas chegou muito perto (<= 2 metros), retorna a melhor rota parcial
		if (minHeuristic < 2.0f && closestToGoal != startNode) {
			return reconstructGridPath(cameFrom, closestToGoal, targetX, targetY, targetZ);
		}

		return null;
	}

	/**
	 * A* Macro em grade de 8m para retorno ao spawn ou longas travessias.
	 */
	private static List<float[]> executeMacroAStar(NativePathMap map, float startX, float startY, float startZ,
												  float targetX, float targetY, float targetZ) {
		int startMx = Math.round(startX / 8.0f);
		int startMy = Math.round(startY / 8.0f);
		int goalMx = Math.round(targetX / 8.0f);
		int goalMy = Math.round(targetY / 8.0f);

		long startKey = packGridKey(startMx, startMy);

		PriorityQueue<GridNode> openSet = new PriorityQueue<>(128);
		Map<Long, Float> gScore = new HashMap<>(2048);
		Map<Long, GridNode> cameFrom = new HashMap<>(2048);
		Set<Long> closedSet = new HashSet<>(2048);

		float initialH = heuristic(startX, startY, targetX, targetY);
		GridNode startNode = new GridNode(startMx, startMy, startZ, 0.0f, initialH);
		openSet.add(startNode);
		gScore.put(startKey, 0.0f);

		int iterations = 0;
		int[] dx = {1, -1, 0, 0, 1, 1, -1, -1};
		int[] dy = {0, 0, 1, -1, 1, -1, 1, -1};
		float[] moveCost = {8.0f, 8.0f, 8.0f, 8.0f, 11.31f, 11.31f, 11.31f, 11.31f};

		while (!openSet.isEmpty() && iterations++ < MAX_MACRO_EXPLORED_NODES) {
			GridNode current = openSet.poll();
			long currentKey = packGridKey(current.gx, current.gy);

			if (current.gx == goalMx && current.gy == goalMy) {
				return reconstructGridPathMacro(cameFrom, current, targetX, targetY, targetZ);
			}

			if (closedSet.contains(currentKey)) {
				continue;
			}
			closedSet.add(currentKey);

			float currentWorldX = current.gx * 8.0f;
			float currentWorldY = current.gy * 8.0f;

			for (int dir = 0; dir < 8; dir++) {
				int nextMx = current.gx + dx[dir];
				int nextMy = current.gy + dy[dir];
				long nextKey = packGridKey(nextMx, nextMy);

				if (closedSet.contains(nextKey)) {
					continue;
				}

				float nextWorldX = nextMx * 8.0f;
				float nextWorldY = nextMy * 8.0f;

				if (!map.isWalkable(nextWorldX, nextWorldY, current.z, 4.0f)) {
					continue;
				}

				float nextZ = map.getSurfaceZ(nextWorldX, nextWorldY, current.z, current.z);
				float deltaZ = Math.abs(nextZ - current.z);
				if (deltaZ > 5.0f) {
					continue;
				}

				float tentativeG = current.g + moveCost[dir] + deltaZ * 1.5f;
				float oldG = gScore.getOrDefault(nextKey, Float.POSITIVE_INFINITY);

				if (tentativeG < oldG) {
					float h = heuristic(nextWorldX, nextWorldY, targetX, targetY);
					GridNode neighbor = new GridNode(nextMx, nextMy, nextZ, tentativeG, h);
					cameFrom.put(nextKey, current);
					gScore.put(nextKey, tentativeG);
					openSet.add(neighbor);
				}
			}
		}

		return null;
	}

	/**
	 * Heurística euclidiana admissível para estimativa da distância restante até o alvo.
	 */
	private static float heuristic(float x1, float y1, float x2, float y2) {
		float dx = x1 - x2;
		float dy = y1 - y2;
		return (float) Math.hypot(dx, dy);
	}

	/**
	 * Compacta dois inteiros de grade (gx, gy) em uma chave primitiva de 64 bits (long) para hash rápido.
	 */
	private static long packGridKey(int gx, int gy) {
		return (((long) gx) << 32) | (gy & 0xFFFFFFFFL);
	}

	/**
	 * Reconstrói o percurso navegável a partir da tabela cameFrom.
	 */
	private static List<float[]> reconstructGridPath(Map<Long, GridNode> cameFrom, GridNode current,
													float targetX, float targetY, float targetZ) {
		List<float[]> path = new ArrayList<>();
		path.add(new float[] {targetX, targetY, targetZ});

		GridNode curr = current;
		while (curr != null) {
			long key = packGridKey(curr.gx, curr.gy);
			GridNode parent = cameFrom.get(key);
			// Não adiciona o nó raiz (startNode não está em cameFrom, parent será null)
			// Se parent != null, este nó é intermediário e deve entrar na rota
			if (parent != null) {
				path.add(new float[] {curr.gx * 0.5f, curr.gy * 0.5f, curr.z});
			}
			curr = parent;
		}

		Collections.reverse(path);
		return path;
	}

	private static List<float[]> reconstructGridPathMacro(Map<Long, GridNode> cameFrom, GridNode current,
														 float targetX, float targetY, float targetZ) {
		List<float[]> path = new ArrayList<>();
		path.add(new float[] {targetX, targetY, targetZ});

		GridNode curr = current;
		while (curr != null) {
			path.add(new float[] {curr.gx * 8.0f, curr.gy * 8.0f, curr.z});
			long key = packGridKey(curr.gx, curr.gy);
			curr = cameFrom.get(key);
		}

		Collections.reverse(path);
		return path;
	}

	/**
	 * Suavização de trajeto via String-Pulling (Funnel Algorithm):
	 * Elimina ziguezagues e atalhos conectando nós distantes onde houver linha de visão limpa.
	 *
	 * Limitação de salto:
	 * - Em ambientes fechados (muitas camadas = dungeons/fortalezas): máx 8m por salto.
	 * - Em campo aberto: máx 20m por salto.
	 * Evita que o String-Pulling crie segmentos que atravessem paredes em corredores curvos.
	 */
	private static List<float[]> smoothPath(NativePathMap map, List<float[]> waypoints,
											float targetX, float targetY, float targetZ) {
		if (waypoints.size() <= 2) {
			return waypoints;
		}

		// Determina distância máxima de salto baseada na densidade de camadas do mapa
		// Mapas com muitas camadas (fortalezas, dungeons) usam salto menor para evitar atalhos inválidos
		int layerDensityThreshold = map.getSectorDim() * 2;
		float maxJumpDist = map.getTotalLayers() > layerDensityThreshold ? 8.0f : 20.0f;
		float maxJumpDistSq = maxJumpDist * maxJumpDist;

		List<float[]> smoothed = new ArrayList<>();
		int currentIndex = 0;
		smoothed.add(waypoints.get(0));

		while (currentIndex < waypoints.size() - 1) {
			int furthestIndex = currentIndex + 1;
			float[] currentPt = waypoints.get(currentIndex);

			// Avança gananciosamente até o ponto mais distante diretamente visível dentro do limite de salto
			for (int testIndex = waypoints.size() - 1; testIndex > currentIndex + 1; testIndex--) {
				float[] testPt = waypoints.get(testIndex);
				float dx = testPt[0] - currentPt[0];
				float dy = testPt[1] - currentPt[1];
				float distSq = dx * dx + dy * dy;
				if (distSq > maxJumpDistSq) {
					continue; // Salto muito longo — pula este candidato
				}
				if (map.hasLineOfSight(currentPt[0], currentPt[1], currentPt[2],
						testPt[0], testPt[1], testPt[2], MAX_DROP_DOWN)) {
					furthestIndex = testIndex;
					break;
				}
			}

			float[] nextPt = waypoints.get(furthestIndex);
			smoothed.add(nextPt);
			currentIndex = furthestIndex;
		}

		// Garante waypoint final no destino exato
		float[] last = smoothed.get(smoothed.size() - 1);
		float dSq = (last[0] - targetX) * (last[0] - targetX) + (last[1] - targetY) * (last[1] - targetY);
		if (dSq > 0.25f) {
			smoothed.add(new float[] {targetX, targetY, targetZ});
		} else {
			smoothed.set(smoothed.size() - 1, new float[] {targetX, targetY, targetZ});
		}

		return smoothed;
	}

	/**
	 * Nó de busca A* com campos explícitos de custo real g, heurística h e custo total f = g + h.
	 * O desempate em igualdade de f prioriza o menor h (maior proximidade ao objetivo).
	 */
	private static final class GridNode implements Comparable<GridNode> {
		final int gx;
		final int gy;
		final float z;
		final float g;
		final float h;
		final float f;

		GridNode(int gx, int gy, float z, float g, float h) {
			this.gx = gx;
			this.gy = gy;
			this.z = z;
			this.g = g;
			this.h = h;
			this.f = g + h;
		}

		@Override
		public int compareTo(GridNode other) {
			int cmp = Float.compare(this.f, other.f);
			if (cmp == 0) {
				// Desempate em favor do nó mais promissor (mais próximo do objetivo)
				return Float.compare(this.h, other.h);
			}
			return cmp;
		}
	}
}
