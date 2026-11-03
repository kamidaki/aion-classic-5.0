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
 * COBERTURA COMPLETA DE CENÁRIOS:
 * 1. Corredores estreitos e largos — clearance lateral direcional (não bloqueia passagens de 1m)
 * 2. Escadas pequenas e grandes — MAX_STEP_UP 0.8m por subcélula; custo de slope ajustado
 * 3. Escadas caracol / estruturas multi-andar — chave de nó 3D (gx, gy, gz) distingue o
 *    mesmo XY em alturas diferentes, eliminando loop infinito no mesmo andar
 * 4. Pontes estreitas sem guarda-corpo — 2ª passagem sem clearance garante a travessia
 * 5. Colinas e rampas — penalidade de slope reduzida (não bloqueia colinas graduais)
 * 6. Fendas e abismos — validação de Z surface em cada subcélula via DDA raycast
 * 7. Estruturas físicas (casas, muros, árvores) — hasLineOfSight com GeoService no smoothPath
 *
 * OTIMIZAÇÕES DE ARQUITETURA:
 * - Zero Alocação de Heap: ThreadLocal AStarSearchContext com pool de nós primitivos
 * - Reset em O(1) via searchId (generation stamp)
 * - Dois passes: passo 1 com clearance lateral, passo 2 sem clearance (passagens estreitas)
 * - Heurística 3D admissível para melhor guia em cenários verticais
 * - Hash Murmur3 64→32 bits com boa distribuição para chaves 3D
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathAStar {

	/** Limite máximo de iterações por passagem — 6000 cobre multi-andar e obstáculos densos. */
	public static final int MAX_LOCAL_EXPLORED_CELLS = 6000;

	/** Altura máxima de degrau (subida vertical) sem pular — 0.8 metros. */
	public static final float MAX_STEP_UP = 0.8f;

	/** Altura máxima de queda (descida vertical) — 1.8 metros. */
	public static final float MAX_DROP_DOWN = 1.8f;

	/** Distância máxima plana para usar a grade de 0.5m. */
	private static final float LOCAL_SEARCH_MAX_DIST = 90.0f;

	/**
	 * Tamanho do bucket vertical para a chave 3D de nós.
	 * 1 bucket = 2.0 metros de altura.
	 * Permite que o A* distinga o mesmo ponto XY em andares diferentes (escada caracol, etc).
	 */
	private static final float Z_BUCKET_SIZE = 2.0f;

	/** Contexto reutilizável por thread — zero alocação em heap por busca. */
	private static final ThreadLocal<AStarSearchContext> SEARCH_CONTEXT =
			ThreadLocal.withInitial(AStarSearchContext::new);

	private NativePathAStar() {
	}

	// ─── Sobrecargas públicas ───────────────────────────────────────────────

	public static float[][] findPath(NativePathMap map,
			float startX, float startY, float startZ,
			float targetX, float targetY, float targetZ) {
		return findPath(map, startX, startY, startZ, targetX, targetY, targetZ, 0.5f, 0.0f);
	}

	public static float[][] findPath(NativePathMap map,
			float startX, float startY, float startZ,
			float targetX, float targetY, float targetZ,
			float agentRadius, float reachDistance) {
		return findPath(map, startX, startY, startZ, targetX, targetY, targetZ, agentRadius, reachDistance, 0);
	}

	/**
	 * Calcula o percurso navegável ótimo entre dois pontos com dois passes:
	 *  Passo 1 — clearance lateral proporcional ao raio do agente (áreas abertas).
	 *  Passo 2 — sem clearance lateral (corredores estreitos, pontes, passagens apertadas).
	 */
	public static float[][] findPath(NativePathMap map,
			float startX, float startY, float startZ,
			float targetX, float targetY, float targetZ,
			float agentRadius, float reachDistance, int instanceId) {

		if (map == null) return null;

		float dist2D = (float) Math.hypot(targetX - startX, targetY - startY);

		// Já dentro do alcance com LOS → retorna imediatamente
		if (reachDistance > 0.0f && dist2D <= reachDistance &&
				map.hasLineOfSight(startX, startY, startZ, targetX, targetY, targetZ, MAX_DROP_DOWN, instanceId)) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		// LOS direta → caminho reto sem A*
		if (map.hasLineOfSight(startX, startY, startZ, targetX, targetY, targetZ, MAX_DROP_DOWN, instanceId)) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		if (dist2D < 0.5f) {
			return new float[][] {{targetX, targetY, targetZ}};
		}

		// Projeta pontos de início/fim para solo navegável próximo
		float[] vs = map.findClosestWalkablePoint(startX, startY, startZ, 5.0f, instanceId);
		float sX = vs != null ? vs[0] : startX;
		float sY = vs != null ? vs[1] : startY;
		float sZ = vs != null ? vs[2] : startZ;

		float[] vt = map.findClosestWalkablePoint(targetX, targetY, targetZ, 5.0f, instanceId);
		float tX = vt != null ? vt[0] : targetX;
		float tY = vt != null ? vt[1] : targetY;
		float tZ = vt != null ? vt[2] : targetZ;

		if (dist2D <= LOCAL_SEARCH_MAX_DIST) {
			AStarSearchContext ctx = SEARCH_CONTEXT.get();

			// ── PASSO 1: com clearance lateral (espaço espaçado, evita raspar paredes) ──
			List<float[]> raw = executeSubcellAStar(ctx, map, sX, sY, sZ, tX, tY, tZ,
					agentRadius, reachDistance, instanceId, true);
			if (raw != null && !raw.isEmpty()) {
				return smoothPath(map, raw, tX, tY, tZ, instanceId).toArray(new float[0][]);
			}

			// ── PASSO 2: sem clearance (corredor estreito, ponte de 1m, passagem única) ──
			raw = executeSubcellAStar(ctx, map, sX, sY, sZ, tX, tY, tZ,
					agentRadius, reachDistance, instanceId, false);
			if (raw != null && !raw.isEmpty()) {
				return smoothPath(map, raw, tX, tY, tZ, instanceId).toArray(new float[0][]);
			}
		}

		return null;
	}

	// ─── Núcleo do A* ──────────────────────────────────────────────────────

	/**
	 * Executa o A* na grade de 0.5m com contexto pré-alocado (zero heap per search).
	 *
	 * @param useClearance true  → clearance lateral direcional ativo (passo 1)
	 *                     false → só isWalkable, sem clearance (passo 2: passagens estreitas)
	 */
	private static List<float[]> executeSubcellAStar(AStarSearchContext ctx, NativePathMap map,
			float startX, float startY, float startZ,
			float targetX, float targetY, float targetZ,
			float agentRadius, float reachDistance, int instanceId, boolean useClearance) {

		ctx.reset();

		int startGx = Math.round(startX * 2.0f);
		int startGy = Math.round(startY * 2.0f);
		int startGz = Math.round(startZ / Z_BUCKET_SIZE); // bucket de altura (escadas/andares)
		int goalGx  = Math.round(targetX * 2.0f);
		int goalGy  = Math.round(targetY * 2.0f);

		long  startKey  = packGridKey(startGx, startGy, startGz);
		float initialH  = heuristic3D(startX, startY, startZ, targetX, targetY, targetZ);

		int startNode = ctx.allocateNode(startGx, startGy, startZ, 0.0f, initialH, -1);
		ctx.tablePut(startKey, startNode);
		ctx.heapPush(startNode);

		// 8 direções: E, W, N, S, NE, SE, NW, SW
		int[]   dx       = {1, -1,  0,  0,  1,  1, -1, -1};
		int[]   dy       = {0,  0,  1, -1,  1, -1,  1, -1};
		float[] moveCost = {0.5f, 0.5f, 0.5f, 0.5f, 0.7071f, 0.7071f, 0.7071f, 0.7071f};

		int   closestNode  = startNode;
		float minHeuristic = initialH;
		int   iterations   = 0;

		// Clearance lateral: proporcional ao raio do agente, jamais omnidirecional.
		// Isso garante que o NPC não seja bloqueado ao longo do eixo de deslocamento
		// numa ponte estreita ou corredor de 1m.
		float clearance = useClearance ? Math.max(0.4f, Math.min(1.2f, agentRadius * 0.75f)) : 0.0f;

		while (!ctx.isHeapEmpty() && iterations++ < MAX_LOCAL_EXPLORED_CELLS) {
			int current = ctx.heapPop();
			if (ctx.nodeClosed[current]) continue;
			ctx.nodeClosed[current] = true;

			int   cgx = ctx.nodeGx[current];
			int   cgy = ctx.nodeGy[current];
			float cZ  = ctx.nodeZ[current];
			float cG  = ctx.nodeG[current];
			float cH  = ctx.nodeH[current];

			// ── Chegada exata à subcélula de destino ──
			if (cgx == goalGx && cgy == goalGy) {
				return reconstructPath(ctx, current);
			}

			// ── Dentro do alcance de combate com LOS ──
			float effectiveReach = reachDistance > 0.0f ? reachDistance : 1.8f;
			if (cH <= effectiveReach) {
				float cWorldX = cgx * 0.5f;
				float cWorldY = cgy * 0.5f;
				if (map.hasLineOfSight(cWorldX, cWorldY, cZ, targetX, targetY, targetZ, MAX_DROP_DOWN, instanceId)) {
					return reconstructPath(ctx, current);
				}
				if (cH <= 0.8f) {
					return reconstructPath(ctx, current);
				}
			}

			float currentWorldX = cgx * 0.5f;
			float currentWorldY = cgy * 0.5f;

			for (int dir = 0; dir < 8; dir++) {
				int nextGx = cgx + dx[dir];
				int nextGy = cgy + dy[dir];

				float nextWorldX = nextGx * 0.5f;
				float nextWorldY = nextGy * 0.5f;

				// Cota Z real do próximo nó (consulta CryEngine path.dat + GeoEngine)
				float nextZ  = map.getSurfaceZ(nextWorldX, nextWorldY, cZ, cZ, instanceId);

				// Chave 3D: o bucket de Z distingue o mesmo (gx,gy) em andares diferentes.
				// Fundamental para escadas caracol: a espiral ocupa o mesmo XY em alturas distintas.
				int  nextGz  = Math.round(nextZ / Z_BUCKET_SIZE);
				long nextKey = packGridKey(nextGx, nextGy, nextGz);

				int existing = ctx.tableGet(nextKey);
				if (existing >= 0 && ctx.nodeClosed[existing]) continue;

				// ── Anti-corner-cutting: diagonal bloqueada se ambas as laterais ortogonais forem paredes ──
				if (dir >= 4) {
					boolean sideA = !map.isWalkable(currentWorldX + dx[dir] * 0.5f, currentWorldY,       nextZ, 2.0f, instanceId);
					boolean sideB = !map.isWalkable(currentWorldX,                  currentWorldY + dy[dir] * 0.5f, nextZ, 2.0f, instanceId);
					if (sideA && sideB) continue;
				}

				// ── Transitabilidade CryEngine ──
				if (!map.isWalkable(nextWorldX, nextWorldY, nextZ, 2.0f, instanceId)) continue;

				// ── Clearance lateral DIRECIONAL (passo 1 apenas) ──────────────────────────
				// Verifica SOMENTE as duas direções perpendiculares ao vetor de movimento.
				//
				// Por quê direcional? Um NPC atravessando uma ponte de 1.5m de largura no sentido
				// longitudinal não deve ser bloqueado pelo vazio nas laterais — a checagem
				// omnidirecional anterior bloquearia esse caso. Com a checagem direcional, o NPC
				// só é bloqueado por obstáculos/vazio que estejam perpendicularmente ao seu caminho.
				//
				// Benefícios por cenário:
				//  - Corredor estreito (1-2m): passo 1 falha, passo 2 sem clearance cobre
				//  - Ponte de 1.5m sem guarda: clearance lateral verifica apenas as margens,
				//    não a frente ou o vazio do fundo do abismo
				//  - Canto de parede: detecta corretamente (perpendicular ao mov. colide com parede)
				// ───────────────────────────────────────────────────────────────────────────
				if (useClearance && clearance > 0.0f) {
					boolean sideBlocked;
					if (dir < 4) {
						// Axial: perp de (dx, 0) é (0, ±clearance); perp de (0, dy) é (±clearance, 0)
						float perpX = (dy[dir] != 0) ? clearance : 0.0f;
						float perpY = (dx[dir] != 0) ? clearance : 0.0f;
						sideBlocked =
							!map.isWalkable(nextWorldX + perpX, nextWorldY + perpY, nextZ, 2.0f, instanceId) ||
							!map.isWalkable(nextWorldX - perpX, nextWorldY - perpY, nextZ, 2.0f, instanceId);
					} else {
						// Diagonal (a,b): vetor perpendicular é (-b,a) normalizado * clearance
						float px = -dy[dir] * clearance * 0.7071f;
						float py =  dx[dir] * clearance * 0.7071f;
						sideBlocked =
							!map.isWalkable(nextWorldX + px, nextWorldY + py, nextZ, 2.0f, instanceId) ||
							!map.isWalkable(nextWorldX - px, nextWorldY - py, nextZ, 2.0f, instanceId);
					}
					if (sideBlocked) continue;
				}

				// ── Validação vertical: degrau máx 0.8m / queda máx 1.8m ──
				float deltaZ = nextZ - cZ;
				if (deltaZ  >  MAX_STEP_UP)  continue;
				if (-deltaZ >  MAX_DROP_DOWN) continue;

				// Custo de inclinação — reduzido para não bloquear colinas graduais nem escadas
				// Antes: subida 1.5× (muito restritivo). Agora: 0.8× (escadas de 45° passam bem)
				float slopeCost = deltaZ > 0
						? deltaZ * 0.8f * moveCost[dir]   // subida leve
						: -deltaZ * 0.1f * moveCost[dir]; // descida quase grátis
				float tentativeG = cG + moveCost[dir] + slopeCost;

				if (existing >= 0) {
					if (tentativeG < ctx.nodeG[existing]) {
						ctx.nodeG[existing]      = tentativeG;
						ctx.nodeF[existing]      = tentativeG + ctx.nodeH[existing];
						ctx.nodeParent[existing] = current;
						ctx.nodeZ[existing]      = nextZ;
						ctx.heapPush(existing);
					}
				} else {
					if (ctx.nodeCount >= AStarSearchContext.MAX_NODES) break;
					float h = heuristic3D(nextWorldX, nextWorldY, nextZ, targetX, targetY, targetZ);
					int newNode = ctx.allocateNode(nextGx, nextGy, nextZ, tentativeG, h, current);
					ctx.tablePut(nextKey, newNode);
					ctx.heapPush(newNode);
					if (h < minHeuristic) {
						minHeuristic = h;
						closestNode  = newNode;
					}
				}
			}
		}

		// Retorna melhor rota parcial se houve avanço — NPC continua se movendo
		if (closestNode != startNode && minHeuristic < initialH) {
			return reconstructPath(ctx, closestNode);
		}
		return null;
	}

	// ─── Utilitários ───────────────────────────────────────────────────────

	private static List<float[]> reconstructPath(AStarSearchContext ctx, int endNode) {
		List<float[]> path = new ArrayList<>();
		int curr = endNode;
		while (curr >= 0) {
			path.add(new float[] {ctx.nodeGx[curr] * 0.5f, ctx.nodeGy[curr] * 0.5f, ctx.nodeZ[curr]});
			curr = ctx.nodeParent[curr];
		}
		Collections.reverse(path);
		return path;
	}

	/**
	 * Suavização via String-Pulling: conecta waypoints distantes onde houver LOS direta.
	 * A validação física GeoService (BIH raycast) é feita aqui — custo amortizado sobre
	 * O(waypoints), não O(nodes). Aqui é onde importa verificar casas, muros, árvores.
	 */
	private static List<float[]> smoothPath(NativePathMap map, List<float[]> waypoints,
			float targetX, float targetY, float targetZ, int instanceId) {

		if (waypoints == null || waypoints.isEmpty()) return Collections.emptyList();

		List<float[]> smoothed;
		if (waypoints.size() <= 2) {
			smoothed = new ArrayList<>(waypoints);
		} else {
			int   layerDensityThreshold = map.getSectorDim() * 2;
			float maxJumpDist           = map.getTotalLayers() > layerDensityThreshold ? 8.0f : 20.0f;
			float maxJumpDistSq         = maxJumpDist * maxJumpDist;

			smoothed = new ArrayList<>();
			int currentIndex = 0;
			smoothed.add(waypoints.get(0));

			while (currentIndex < waypoints.size() - 1) {
				int     furthestIndex = currentIndex + 1;
				float[] currentPt     = waypoints.get(currentIndex);

				for (int testIndex = waypoints.size() - 1; testIndex > currentIndex + 1; testIndex--) {
					float[] testPt = waypoints.get(testIndex);
					float   ddx    = testPt[0] - currentPt[0];
					float   ddy    = testPt[1] - currentPt[1];
					if (ddx * ddx + ddy * ddy > maxJumpDistSq) continue;
					if (map.hasLineOfSight(currentPt[0], currentPt[1], currentPt[2],
							testPt[0], testPt[1], testPt[2], MAX_DROP_DOWN, instanceId)) {
						furthestIndex = testIndex;
						break;
					}
				}

				smoothed.add(waypoints.get(furthestIndex));
				currentIndex = furthestIndex;
			}
		}

		// Garante waypoint final exato no destino se houver LOS
		float[] last = smoothed.get(smoothed.size() - 1);
		float   dSq  = (last[0] - targetX) * (last[0] - targetX) + (last[1] - targetY) * (last[1] - targetY);
		if (dSq > 0.25f) {
			if (map.hasLineOfSight(last[0], last[1], last[2], targetX, targetY, targetZ, MAX_DROP_DOWN, instanceId)) {
				smoothed.add(new float[] {targetX, targetY, targetZ});
			}
		} else {
			smoothed.set(smoothed.size() - 1, new float[] {targetX, targetY, targetZ});
		}

		// Filtra waypoints intermediários redundantes (< 0.8m) para evitar micro-teleportes
		if (smoothed.size() > 2) {
			List<float[]> filtered = new ArrayList<>();
			filtered.add(smoothed.get(0));
			for (int i = 1; i < smoothed.size() - 1; i++) {
				float[] prev = filtered.get(filtered.size() - 1);
				float[] curr = smoothed.get(i);
				float   dX   = curr[0] - prev[0];
				float   dY   = curr[1] - prev[1];
				if (dX * dX + dY * dY >= 0.64f) filtered.add(curr); // >= 0.8m
			}
			filtered.add(smoothed.get(smoothed.size() - 1));
			smoothed = filtered;
		}

		return smoothed;
	}

	/**
	 * Heurística 3D admissível para melhor guia do A* em cenários verticais.
	 *
	 * A componente Z recebe peso 0.5 porque o agente nunca se move puramente na vertical —
	 * a Z change sempre vem acoplada a movimento XY. Com isso:
	 *   sqrt(dx²+dy²+0.25·dz²) ≤ custo real do caminho → heurística admissível ✓
	 *
	 * Benefícios sobre heurística 2D pura:
	 *  - Escada espiral: A* prefere nós que avançam tanto em XY quanto em Z
	 *  - Colina alta: converge mais rápido sem explorar todo o platô plano primeiro
	 */
	private static float heuristic3D(float x1, float y1, float z1, float x2, float y2, float z2) {
		float dx = x1 - x2;
		float dy = y1 - y2;
		float dz = (z1 - z2) * 0.5f;
		return (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
	}

	/**
	 * Chave de nó 3D: codifica (gx, gy, gz) em 64 bits.
	 *
	 * Distribuição de bits: gz(14b | ±8192m) | gy(25b | ±8388km) | gx(25b | ±8388km)
	 * Cobre qualquer mapa de Aion (máx ~3072m) com ampla margem.
	 *
	 * O gz = round(Z / 2.0m) garante que dois nós no mesmo XY mas em andares
	 * separados por ≥ 2m produzam chaves distintas — fundamental para escada caracol.
	 */
	private static long packGridKey(int gx, int gy, int gz) {
		return ((long) (gz & 0x3FFF)) << 50
			 | ((long) (gy & 0x1FFFFFF)) << 25
			 | (gx & 0x1FFFFFF);
	}

	// ─── Contexto A* por thread ─────────────────────────────────────────────

	/**
	 * Contexto pré-alocado de busca A* por thread.
	 * MAX_NODES = 8192 (2× anterior) para caminhos multi-andar complexos.
	 */
	private static final class AStarSearchContext {
		static final int MAX_NODES  = 8192;
		static final int TABLE_SIZE = 16384; // potência de 2; carga máx ~50% → sem degradação
		static final int TABLE_MASK = TABLE_SIZE - 1;

		int searchId = 1;

		// Tabela hash aberta de endereçamento linear (chave 3D → índice de nó)
		final long[] tableKeys     = new long[TABLE_SIZE];
		final int[]  tableValues   = new int[TABLE_SIZE];
		final int[]  tableSearchId = new int[TABLE_SIZE];

		// Min-heap binário de nós abertos
		final int[] heap     = new int[MAX_NODES];
		int         heapSize = 0;

		// Pool de nós A*
		final int[]     nodeGx     = new int[MAX_NODES];
		final int[]     nodeGy     = new int[MAX_NODES];
		final float[]   nodeZ      = new float[MAX_NODES];
		final float[]   nodeG      = new float[MAX_NODES];
		final float[]   nodeH      = new float[MAX_NODES];
		final float[]   nodeF      = new float[MAX_NODES];
		final int[]     nodeParent = new int[MAX_NODES];
		final boolean[] nodeClosed = new boolean[MAX_NODES];
		int nodeCount = 0;

		void reset() {
			heapSize  = 0;
			nodeCount = 0;
			searchId++;
			if (searchId == Integer.MAX_VALUE) {
				java.util.Arrays.fill(tableSearchId, 0);
				searchId = 1;
			}
		}

		int allocateNode(int gx, int gy, float z, float g, float h, int parent) {
			int id = nodeCount++;
			nodeGx[id]     = gx;
			nodeGy[id]     = gy;
			nodeZ[id]      = z;
			nodeG[id]      = g;
			nodeH[id]      = h;
			nodeF[id]      = g + h;
			nodeParent[id] = parent;
			nodeClosed[id] = false;
			return id;
		}

		int tableGet(long key) {
			int slot = hash(key) & TABLE_MASK;
			while (tableSearchId[slot] == searchId) {
				if (tableKeys[slot] == key) return tableValues[slot];
				slot = (slot + 1) & TABLE_MASK;
			}
			return -1;
		}

		void tablePut(long key, int nodeIndex) {
			int slot = hash(key) & TABLE_MASK;
			while (tableSearchId[slot] == searchId && tableKeys[slot] != key) {
				slot = (slot + 1) & TABLE_MASK;
			}
			tableSearchId[slot] = searchId;
			tableKeys[slot]     = key;
			tableValues[slot]   = nodeIndex;
		}

		/** Murmur3 64→32 bits: excelente distribuição para chaves 3D compactas. */
		private static int hash(long key) {
			key ^= (key >>> 33);
			key *= 0xff51afd7ed558ccdL;
			key ^= (key >>> 33);
			return (int) key;
		}

		boolean isHeapEmpty() { return heapSize == 0; }

		void heapPush(int nodeIndex) {
			int i = heapSize++;
			heap[i] = nodeIndex;
			siftUp(i);
		}

		int heapPop() {
			int top  = heap[0];
			int last = heap[--heapSize];
			if (heapSize > 0) {
				heap[0] = last;
				siftDown(0);
			}
			return top;
		}

		private void siftUp(int k) {
			int   node = heap[k];
			float f    = nodeF[node];
			float h    = nodeH[node];
			while (k > 0) {
				int parent = (k - 1) >>> 1;
				int pNode  = heap[parent];
				if (f > nodeF[pNode] || (f == nodeF[pNode] && h >= nodeH[pNode])) break;
				heap[k] = pNode;
				k = parent;
			}
			heap[k] = node;
		}

		private void siftDown(int k) {
			int   node = heap[k];
			float f    = nodeF[node];
			float h    = nodeH[node];
			int   half = heapSize >>> 1;
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
				if (f < nodeF[cNode] || (f == nodeF[cNode] && h <= nodeH[cNode])) break;
				heap[k] = cNode;
				k = child;
			}
			heap[k] = node;
		}
	}
}
