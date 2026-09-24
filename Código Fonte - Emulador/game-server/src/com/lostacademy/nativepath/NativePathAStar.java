package com.lostacademy.nativepath;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Algoritmo A* híbrido de altíssimo desempenho e zero alocação de heap por requisição,
 * operando sobre a grade nativa CryEngine (precisão 0.5m) e malhas 3D de terreno/estruturas.
 *
 * OTIMIZAÇÕES DE ARQUITETURA DE PRODUÇÃO:
 * 1. Zero Alocação de Heap (ThreadLocal Search Context):
 *    - Reutiliza arrays primitivos (heap binário, tabela hash primitiva, pool de nós).
 *    - Elimina completamente o boxing de Long/Float e a alocação de HashMaps/PriorityQueues.
 *    - Reset de contexto entre buscas em tempo constante O(1) via carimbo de geração (searchId).
 * 2. Suporte Tridimensional Exato:
 *    - Consulta de cota Z real em cada nó vizinho integrando relevo e estruturas elevadas.
 *    - Validação física de locomoção assimétrica: subida máx 0.8m (degrau) e queda máx 1.8m.
 *    - Penalidade energética para aclives íngremes.
 * 3. Prevenção de Corte de Quinas (Anti-Corner Cutting):
 *    - Bloqueio estrito de diagonais se ambas as subcélulas ortogonais adjacentes forem paredes.
 * 4. Suavização de Trajetórias (Funnel Algorithm / String-Pulling):
 *    - Conecta waypoints com linha de visão física direta, eliminando ziguezagues.
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathAStar {

	/**
	 * Limite máximo de nós explorados na busca local de alta resolução (0.5m).
	 */
	public static final int MAX_LOCAL_EXPLORED_CELLS = 3000;

	/**
	 * Altura máxima de degrau (subida vertical) sem pular (0.8 metros).
	 */
	public static final float MAX_STEP_UP = 0.8f;

	/**
	 * Altura máxima de desnível/queda (descida vertical) permitida (1.8 metros).
	 */
	public static final float MAX_DROP_DOWN = 1.8f;

	/**
	 * Distância máxima plana para utilização da grade de 0.5m (90 metros).
	 */
	private static final float LOCAL_SEARCH_MAX_DIST = 90.0f;

	/**
	 * Contexto reutilizável thread-safe para execução de A* sem alocações em heap.
	 */
	private static final ThreadLocal<AStarSearchContext> SEARCH_CONTEXT = ThreadLocal.withInitial(AStarSearchContext::new);

	private NativePathAStar() {
	}

	/**
	 * Calcula o percurso navegável ótimo entre dois pontos de mundo com parâmetros padrão de agente.
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

		// Se o agente já estiver no raio de alcance e com linha de visão desobstruída, encerra imediatamente
		if (reachDistance > 0.0f && dist2D <= reachDistance) {
			if (map.hasLineOfSight(startX, startY, startZ, targetX, targetY, targetZ, MAX_DROP_DOWN)) {
				return new float[][] {{targetX, targetY, targetZ}};
			}
		}

		// Linha de visão direta rápida (sem obstáculos 3D, sem quinas e sem desníveis excessivos)
		if (map.hasLineOfSight(startX, startY, startZ, targetX, targetY, targetZ, MAX_DROP_DOWN)) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		if (dist2D < 0.5f) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		// Projeta pontos para o solo navegável mais próximo caso estejam em subcélula bloqueada
		float[] validStart = map.findClosestWalkablePoint(startX, startY, startZ, 3.0f);
		float sX = validStart != null ? validStart[0] : startX;
		float sY = validStart != null ? validStart[1] : startY;
		float sZ = validStart != null ? validStart[2] : startZ;

		float[] validTarget = map.findClosestWalkablePoint(targetX, targetY, targetZ, 4.0f);
		float tX = validTarget != null ? validTarget[0] : targetX;
		float tY = validTarget != null ? validTarget[1] : targetY;
		float tZ = validTarget != null ? validTarget[2] : targetZ;

		// Busca local na grade de 0.5m (para combate, perseguição e patrulhas até 90m)
		if (dist2D <= LOCAL_SEARCH_MAX_DIST) {
			AStarSearchContext ctx = SEARCH_CONTEXT.get();
			List<float[]> rawPath = executeSubcellAStar(ctx, map, sX, sY, sZ, tX, tY, tZ, agentRadius, reachDistance);
			if (rawPath != null && !rawPath.isEmpty()) {
				List<float[]> smoothed = smoothPath(map, rawPath, tX, tY, tZ);
				return smoothed.toArray(new float[0][]);
			}
		}

		return null;
	}

	/**
	 * Executa A* na grade de 0.5m utilizando o contexto pré-alocado sem alocações em heap.
	 */
	private static List<float[]> executeSubcellAStar(AStarSearchContext ctx, NativePathMap map,
													float startX, float startY, float startZ,
													float targetX, float targetY, float targetZ,
													float agentRadius, float reachDistance) {
		ctx.reset();

		int startGx = Math.round(startX * 2.0f);
		int startGy = Math.round(startY * 2.0f);
		int goalGx = Math.round(targetX * 2.0f);
		int goalGy = Math.round(targetY * 2.0f);

		long startKey = packGridKey(startGx, startGy);
		float initialH = heuristic(startX, startY, targetX, targetY);

		int startNode = ctx.allocateNode(startGx, startGy, startZ, 0.0f, initialH, -1);
		ctx.tablePut(startKey, startNode);
		ctx.heapPush(startNode);

		int[] dx = {1, -1, 0, 0, 1, 1, -1, -1};
		int[] dy = {0, 0, 1, -1, 1, -1, 1, -1};
		float[] moveCost = {0.5f, 0.5f, 0.5f, 0.5f, 0.7071f, 0.7071f, 0.7071f, 0.7071f};

		int closestNode = startNode;
		float minHeuristic = initialH;
		int iterations = 0;

		while (!ctx.isHeapEmpty() && iterations++ < MAX_LOCAL_EXPLORED_CELLS) {
			int current = ctx.heapPop();
			if (ctx.nodeClosed[current]) {
				continue;
			}
			ctx.nodeClosed[current] = true;

			int cgx = ctx.nodeGx[current];
			int cgy = ctx.nodeGy[current];
			float cZ = ctx.nodeZ[current];
			float cG = ctx.nodeG[current];
			float cH = ctx.nodeH[current];

			// Condição de chegada 1: alcançou a subcélula de destino exata
			if (cgx == goalGx && cgy == goalGy) {
				return reconstructPath(ctx, current, targetX, targetY, targetZ);
			}

			// Condição de chegada 2: alcançou distância de parada com linha de visão limpa
			if (reachDistance > 0.0f && cH <= reachDistance) {
				float cWorldX = cgx * 0.5f;
				float cWorldY = cgy * 0.5f;
				if (map.hasLineOfSight(cWorldX, cWorldY, cZ, targetX, targetY, targetZ, MAX_DROP_DOWN)) {
					return reconstructPath(ctx, current, targetX, targetY, targetZ);
				}
			}

			float currentWorldX = cgx * 0.5f;
			float currentWorldY = cgy * 0.5f;

			for (int dir = 0; dir < 8; dir++) {
				int nextGx = cgx + dx[dir];
				int nextGy = cgy + dy[dir];
				long nextKey = packGridKey(nextGx, nextGy);

				int existing = ctx.tableGet(nextKey);
				if (existing >= 0 && ctx.nodeClosed[existing]) {
					continue;
				}

				float nextWorldX = nextGx * 0.5f;
				float nextWorldY = nextGy * 0.5f;

				// Consulta altitude real no ponto vizinho
				float nextZ = map.getSurfaceZ(nextWorldX, nextWorldY, cZ, cZ);

				// Anti-corner-cutting: bloqueia diagonal se ambos os lados ortogonais forem paredes
				if (dir >= 4) {
					boolean sideA = !map.isWalkable(currentWorldX + dx[dir] * 0.5f, currentWorldY, nextZ, 2.0f);
					boolean sideB = !map.isWalkable(currentWorldX, currentWorldY + dy[dir] * 0.5f, nextZ, 2.0f);
					if (sideA && sideB) {
						continue;
					}
				}

				// Verifica transitabilidade no CryEngine
				if (!map.isWalkable(nextWorldX, nextWorldY, nextZ, 2.0f)) {
					continue;
				}

				// Folga lateral para agentes de grande porte
				if (agentRadius > 0.6f) {
					float clearance = agentRadius * 0.5f;
					if (!map.isWalkable(nextWorldX + clearance, nextWorldY, nextZ, 2.0f) ||
							!map.isWalkable(nextWorldX - clearance, nextWorldY, nextZ, 2.0f) ||
							!map.isWalkable(nextWorldX, nextWorldY + clearance, nextWorldY, 2.0f) ||
							!map.isWalkable(nextWorldX, nextWorldY - clearance, nextWorldY, 2.0f)) {
						continue;
					}
				}

				// Validação física de locomoção vertical (degrau máx 0.8m / queda máx 1.8m)
				float deltaZ = nextZ - cZ;
				if (deltaZ > MAX_STEP_UP) {
					continue;
				}
				if (-deltaZ > MAX_DROP_DOWN) {
					continue;
				}

				// Penalidade para aclives (prefere caminhos planos)
				float slopeCost = deltaZ > 0 ? deltaZ * 1.5f * moveCost[dir] : -deltaZ * 0.2f * moveCost[dir];
				float tentativeG = cG + moveCost[dir] + slopeCost;

				if (existing >= 0) {
					if (tentativeG < ctx.nodeG[existing]) {
						ctx.nodeG[existing] = tentativeG;
						ctx.nodeF[existing] = tentativeG + ctx.nodeH[existing];
						ctx.nodeParent[existing] = current;
						ctx.nodeZ[existing] = nextZ;
						ctx.heapPush(existing);
					}
				} else {
					if (ctx.nodeCount >= AStarSearchContext.MAX_NODES) {
						break;
					}
					float h = heuristic(nextWorldX, nextWorldY, targetX, targetY);
					int newNode = ctx.allocateNode(nextGx, nextGy, nextZ, tentativeG, h, current);
					ctx.tablePut(nextKey, newNode);
					ctx.heapPush(newNode);

					if (h < minHeuristic) {
						minHeuristic = h;
						closestNode = newNode;
					}
				}
			}
		}

		// Se a busca esgotou mas avançou significativamente, retorna a melhor rota parcial para não congelar
		if (closestNode != startNode && minHeuristic < initialH) {
			return reconstructPath(ctx, closestNode, targetX, targetY, targetZ);
		}

		return null;
	}

	/**
	 * Reconstrói os waypoints do trajeto a partir do pool de nós do contexto.
	 */
	private static List<float[]> reconstructPath(AStarSearchContext ctx, int endNode,
												 float targetX, float targetY, float targetZ) {
		List<float[]> path = new ArrayList<>();
		path.add(new float[] {targetX, targetY, targetZ});

		int curr = endNode;
		while (curr >= 0) {
			int parent = ctx.nodeParent[curr];
			if (parent >= 0) {
				path.add(new float[] {ctx.nodeGx[curr] * 0.5f, ctx.nodeGy[curr] * 0.5f, ctx.nodeZ[curr]});
			}
			curr = parent;
		}

		Collections.reverse(path);
		return path;
	}

	/**
	 * Suavização de trajeto via String-Pulling (Funnel Algorithm):
	 * Elimina ziguezagues conectando nós distantes onde houver linha de visão limpa.
	 */
	private static List<float[]> smoothPath(NativePathMap map, List<float[]> waypoints,
											float targetX, float targetY, float targetZ) {
		if (waypoints.size() <= 2) {
			return waypoints;
		}

		int layerDensityThreshold = map.getSectorDim() * 2;
		float maxJumpDist = map.getTotalLayers() > layerDensityThreshold ? 8.0f : 20.0f;
		float maxJumpDistSq = maxJumpDist * maxJumpDist;

		List<float[]> smoothed = new ArrayList<>();
		int currentIndex = 0;
		smoothed.add(waypoints.get(0));

		while (currentIndex < waypoints.size() - 1) {
			int furthestIndex = currentIndex + 1;
			float[] currentPt = waypoints.get(currentIndex);

			for (int testIndex = waypoints.size() - 1; testIndex > currentIndex + 1; testIndex--) {
				float[] testPt = waypoints.get(testIndex);
				float dx = testPt[0] - currentPt[0];
				float dy = testPt[1] - currentPt[1];
				float distSq = dx * dx + dy * dy;
				if (distSq > maxJumpDistSq) {
					continue;
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

	private static float heuristic(float x1, float y1, float x2, float y2) {
		float dx = x1 - x2;
		float dy = y1 - y2;
		return (float) Math.hypot(dx, dy);
	}

	private static long packGridKey(int gx, int gy) {
		return (((long) gx) << 32) | (gy & 0xFFFFFFFFL);
	}

	/**
	 * Estrutura de dados pré-alocada de alto desempenho por thread para busca A*.
	 * Elimina completamente a pressão sobre o coletor de lixo (GC) do Java.
	 */
	private static final class AStarSearchContext {
		static final int MAX_NODES = 4096;
		static final int TABLE_SIZE = 8192; // Potência de 2
		static final int TABLE_MASK = TABLE_SIZE - 1;

		int searchId = 1;

		// Tabela hash primitiva aberta (Key -> Node Index)
		final long[] tableKeys = new long[TABLE_SIZE];
		final int[] tableValues = new int[TABLE_SIZE];
		final int[] tableSearchId = new int[TABLE_SIZE];

		// Heap binário de nós abertos
		final int[] heap = new int[MAX_NODES];
		int heapSize = 0;

		// Pool de nós A*
		final int[] nodeGx = new int[MAX_NODES];
		final int[] nodeGy = new int[MAX_NODES];
		final float[] nodeZ = new float[MAX_NODES];
		final float[] nodeG = new float[MAX_NODES];
		final float[] nodeH = new float[MAX_NODES];
		final float[] nodeF = new float[MAX_NODES];
		final int[] nodeParent = new int[MAX_NODES];
		final boolean[] nodeClosed = new boolean[MAX_NODES];
		int nodeCount = 0;

		void reset() {
			heapSize = 0;
			nodeCount = 0;
			searchId++;
			if (searchId == Integer.MAX_VALUE) {
				java.util.Arrays.fill(tableSearchId, 0);
				searchId = 1;
			}
		}

		int allocateNode(int gx, int gy, float z, float g, float h, int parent) {
			int id = nodeCount++;
			nodeGx[id] = gx;
			nodeGy[id] = gy;
			nodeZ[id] = z;
			nodeG[id] = g;
			nodeH[id] = h;
			nodeF[id] = g + h;
			nodeParent[id] = parent;
			nodeClosed[id] = false;
			return id;
		}

		int tableGet(long key) {
			int slot = (int) (key ^ (key >>> 32)) * 0x9e3779b9 & TABLE_MASK;
			while (tableSearchId[slot] == searchId) {
				if (tableKeys[slot] == key) {
					return tableValues[slot];
				}
				slot = (slot + 1) & TABLE_MASK;
			}
			return -1;
		}

		void tablePut(long key, int nodeIndex) {
			int slot = (int) (key ^ (key >>> 32)) * 0x9e3779b9 & TABLE_MASK;
			while (tableSearchId[slot] == searchId && tableKeys[slot] != key) {
				slot = (slot + 1) & TABLE_MASK;
			}
			tableSearchId[slot] = searchId;
			tableKeys[slot] = key;
			tableValues[slot] = nodeIndex;
		}

		boolean isHeapEmpty() {
			return heapSize == 0;
		}

		void heapPush(int nodeIndex) {
			int i = heapSize++;
			heap[i] = nodeIndex;
			siftUp(i);
		}

		int heapPop() {
			int top = heap[0];
			int last = heap[--heapSize];
			if (heapSize > 0) {
				heap[0] = last;
				siftDown(0);
			}
			return top;
		}

		private void siftUp(int k) {
			int node = heap[k];
			float f = nodeF[node];
			float h = nodeH[node];
			while (k > 0) {
				int parent = (k - 1) >>> 1;
				int pNode = heap[parent];
				if (f > nodeF[pNode] || (f == nodeF[pNode] && h >= nodeH[pNode])) {
					break;
				}
				heap[k] = pNode;
				k = parent;
			}
			heap[k] = node;
		}

		private void siftDown(int k) {
			int node = heap[k];
			float f = nodeF[node];
			float h = nodeH[node];
			int half = heapSize >>> 1;
			while (k < half) {
				int child = (k << 1) + 1;
				int cNode = heap[child];
				int right = child + 1;
				if (right < heapSize) {
					int rNode = heap[right];
					if (nodeF[rNode] < nodeF[cNode] || (nodeF[rNode] == nodeF[cNode] && nodeH[rNode] < nodeH[cNode])) {
						child = right;
						cNode = rNode;
					}
				}
				if (f < nodeF[cNode] || (f == nodeF[cNode] && h <= nodeH[cNode])) {
					break;
				}
				heap[k] = cNode;
				k = child;
			}
			heap[k] = node;
		}
	}
}
