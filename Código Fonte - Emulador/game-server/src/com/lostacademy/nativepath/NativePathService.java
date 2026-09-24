package com.lostacademy.nativepath;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.world.geo.GeoService;

/**
 * =========================================================================================
 * LOST ACADEMY — SISTEMA OFICIAL DE NAVEGAÇÃO NATIVA CRYENGINE (*-PATH.DAT)
 * =========================================================================================
 * Fachada pública e ponto de entrada central do subsistema de navegação nativa CryEngine.
 *
 * Responsabilidades:
 * 1. Inicialização e monitoramento de telemetria (QPS, tempo de consulta, requisições em voo).
 * 2. Validação de percurso direto (canWalkDirectly) sem atravessar cercas ou quinas.
 * 3. Encaminhamento de rotas para o algoritmo híbrido NativePathAStar com suporte a raio de colisão
 *    e distância de ataque (reachDistance).
 * 4. Validação de linhas de puxão / habilidades de combate (canPullTarget).
 *
 * @author KAMIDAKI & Equipe Lost Academy
 */
public final class NativePathService {

	private static final Logger LOG = LoggerFactory.getLogger(NativePathService.class);

	private final NativePathData data = NativePathData.getInstance();

	public static final AtomicLong totalQueries = new AtomicLong(0);
	public static final AtomicLong totalQueryTimeNs = new AtomicLong(0);
	public static final AtomicInteger queriesInFlight = new AtomicInteger(0);
	public static final AtomicLong lastQueryTimeNs = new AtomicLong(0);

	private static final AtomicLong queriesInLastSecond = new AtomicLong(0);
	private static volatile double queriesPerSecond = 0.0;
	private static volatile long lastQpsResetTime = System.currentTimeMillis();

	/**
	 * Retorna a taxa atualizada de consultas de navegação por segundo (QPS).
	 * Cálculo stateless: divide o total acumulado pelo delta real desde o último reset,
	 * garantindo precisão mesmo sem chamadas periódicas regulares (evita drift).
	 */
	public static double getQueriesPerSecond() {
		long now = System.currentTimeMillis();
		long delta = now - lastQpsResetTime;
		if (delta >= 1000) {
			// Cálculo exato: usa o delta real em vez de assumir exatamente 1s
			queriesPerSecond = (double) queriesInLastSecond.getAndSet(0) / (delta / 1000.0);
			lastQpsResetTime = now;
		}
		return queriesPerSecond;
	}

	/**
	 * Registra a conclusão de uma consulta de caminho, computando métricas de latência.
	 */
	private static void recordQuery(long startTimeNs) {
		queriesInFlight.decrementAndGet();
		long duration = System.nanoTime() - startTimeNs;
		totalQueryTimeNs.addAndGet(duration);
		lastQueryTimeNs.set(duration);
	}

	private NativePathService() {
	}

	/**
	 * Inicializa o serviço e carrega 100% dos mapas nativos CryEngine na memória RAM em paralelo.
	 * Todas as malhas permanecem permanentemente residentes (paridade com GeoData .geo).
	 */
	public void initialize() {
		if (!NativePathConfig.NATIVE_PATH_ENABLE) {
			LOG.info("NATIVE_PATH: Subsistema CryEngine desativado por configuração.");
			return;
		}
		LOG.info("NATIVE_PATH: Subsistema CryEngine habilitado. Iniciando pré-carregamento integral de 100% dos mapas na RAM...");
		data.loadAllMaps();
	}

	/**
	 * Informa se o mapa especificado possui malha binária *-path.dat indexada no disco.
	 *
	 * @param worldId Identificador numérico do mapa (ex: 210010000).
	 * @return true se o arquivo .dat existir e estiver disponível para carregamento.
	 */
	public boolean hasMap(int worldId) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return false;
		return data.hasMap(worldId);
	}

	/**
	 * Valida se uma criatura consegue caminhar diretamente em linha reta até a coordenada alvo,
	 * verificando todas as subcélulas de 0.5m do CryEngine e colisões 3D da GeoEngine.
	 *
	 * @param owner   A criatura que deseja se mover.
	 * @param targetX Coordenada X do destino.
	 * @param targetY Coordenada Y do destino.
	 * @param targetZ Coordenada Z do destino.
	 * @return true se a linha reta for 100% caminhável; false se houver paredes, desníveis ou obstáculos.
	 */
	public boolean canWalkDirectly(Creature owner, float targetX, float targetY, float targetZ) {
		if (owner == null)
			return false;
		if (owner.isFlying())
			return true;

		int worldId = owner.getWorldId();
		NativePathMap map = data.getNativeMap(worldId);
		if (map != null) {
			// Usa instanceId correto para validar instâncias de masmorras (portais diferentes por instância)
			int instanceId = owner.getInstanceId();
			return map.hasLineOfSight(owner.getX(), owner.getY(), owner.getZ(), targetX, targetY, targetZ, NativePathMap.MAX_DROP_DOWN, instanceId);
		}

		// Fallback GeoEngine se não houver mapa .dat no disco
		if (GeoService.getInstance() != null) {
			float dist2D = (float) Math.hypot(targetX - owner.getX(), targetY - owner.getY());
			return GeoService.getInstance().canPass(worldId,
					owner.getX(), owner.getY(), owner.getZ() + 0.5f,
					targetX, targetY, targetZ + 0.5f,
					dist2D, owner.getInstanceId());
		}

		return true;
	}

	/**
	 * Valida se há linha de visão física e folga desobstruída para habilidades de puxão/gancho (Pull).
	 *
	 * @param creature Criatura conjuradora.
	 * @param target   Criatura alvo do efeito.
	 * @return true se o trajeto estiver limpo sem interceptar geometrias sólidas.
	 */
	public boolean canPullTarget(Creature creature, Creature target) {
		long start = System.nanoTime();
		queriesInFlight.incrementAndGet();
		totalQueries.incrementAndGet();
		queriesInLastSecond.incrementAndGet();

		try {
			if (!NativePathConfig.NATIVE_PATH_ENABLE)
				return true;
			if (creature == null || target == null)
				return true;

			int worldId = creature.getWorldId();
			if (target.isFlying() || creature.isFlying())
				return true;

			NativePathMap map = data.getNativeMap(worldId);
			if (map == null) {
				if (GeoService.getInstance() != null) {
					return GeoService.getInstance().canSee(creature, target);
				}
				return true;
			}

			float x1 = creature.getX(), y1 = creature.getY(), z1 = creature.getZ();
			float x2 = target.getX(), y2 = target.getY(), z2 = target.getZ();
			int instanceId = creature.getInstanceId();

			return map.hasLineOfSight(x1, y1, z1, x2, y2, z2, 2.5f, instanceId);
		} finally {
			recordQuery(start);
		}
	}

	/**
	 * Calcula a rota de perseguição de uma criatura até seu alvo vivo, considerando o raio de
	 * colisão do agente e seu alcance de ataque para parada antecipada.
	 *
	 * @param pathOwner Criatura que está se movendo (NPC ou monstro).
	 * @param target    Criatura alvo a ser alcançada.
	 * @return Matriz de waypoints float[][] ou null se não houver caminho possível.
	 */
	public float[][] navigateToTarget(Creature pathOwner, Creature target) {
		long start = System.nanoTime();
		queriesInFlight.incrementAndGet();
		totalQueries.incrementAndGet();
		queriesInLastSecond.incrementAndGet();

		try {
			if (!NativePathConfig.NATIVE_PATH_ENABLE)
				return null;
			if (pathOwner == null || target == null)
				return null;
			if (pathOwner.getLifeStats().isDead())
				return null;
			if (pathOwner.getWorldId() != target.getWorldId())
				return null;

			int worldId = pathOwner.getWorldId();
			NativePathMap map = data.getNativeMap(worldId);
			if (map == null)
				return null;

			float x1 = pathOwner.getX(), y1 = pathOwner.getY(), z1 = pathOwner.getZ();
			float x2 = target.getX(), y2 = target.getY(), z2 = target.getZ();

			// Extrai raio de colisão do template do agente
			float agentRadius = 0.5f;
			if (pathOwner.getObjectTemplate() != null && pathOwner.getObjectTemplate().getBoundRadius() != null) {
				float r = pathOwner.getObjectTemplate().getBoundRadius().getCollision();
				if (r > 0.1f) {
					agentRadius = r;
				}
			}

			// Extrai alcance de ataque para encerramento de trajeto
			float reachDistance = 0.0f;
			if (pathOwner.getGameStats() != null && pathOwner.getGameStats().getAttackRange() != null) {
				float atkRange = pathOwner.getGameStats().getAttackRange().getCurrent() / 1000.0f;
				if (atkRange > 1.5f) {
					reachDistance = Math.max(1.0f, atkRange - 0.5f);
				}
			}

			float[][] path = NativePathAStar.findPath(map, x1, y1, z1, x2, y2, z2, agentRadius, reachDistance);
			if (NativePathConfig.NATIVE_PATH_DEBUG) {
				if (path != null) {
					LOG.info("NATIVE_PATH [TARGET]: [{}] ({}, {}, {}) -> ({}, {}, {}) | {} waypoints | r={} reach={}",
							pathOwner.getName(), x1, y1, z1, x2, y2, z2, path.length, agentRadius, reachDistance);
				} else {
					LOG.debug("NATIVE_PATH [TARGET]: [{}] Sem rota para ({}, {}, {})",
							pathOwner.getName(), x2, y2, z2);
				}
			}
			return path;
		} finally {
			recordQuery(start);
		}
	}

	/**
	 * Calcula o percurso até uma coordenada espacial estática (x, y, z), por exemplo retorno
	 * ao spawn ou destino de patrulha.
	 *
	 * @param pathOwner Criatura em locomoção.
	 * @param x         Coordenada X de destino.
	 * @param y         Coordenada Y de destino.
	 * @param z         Coordenada Z de destino.
	 * @return Matriz de waypoints ou null se rota inacessível.
	 */
	public float[][] navigateToLocation(Creature pathOwner, float x, float y, float z) {
		long start = System.nanoTime();
		queriesInFlight.incrementAndGet();
		totalQueries.incrementAndGet();
		queriesInLastSecond.incrementAndGet();

		try {
			if (!NativePathConfig.NATIVE_PATH_ENABLE)
				return null;
			if (pathOwner == null)
				return null;
			if (pathOwner.getLifeStats().isDead())
				return null;

			int worldId = pathOwner.getWorldId();
			NativePathMap map = data.getNativeMap(worldId);
			if (map == null)
				return null;

			float x1 = pathOwner.getX(), y1 = pathOwner.getY(), z1 = pathOwner.getZ();

			float agentRadius = 0.5f;
			if (pathOwner.getObjectTemplate() != null && pathOwner.getObjectTemplate().getBoundRadius() != null) {
				float r = pathOwner.getObjectTemplate().getBoundRadius().getCollision();
				if (r > 0.1f) {
					agentRadius = r;
				}
			}

			float[][] path = NativePathAStar.findPath(map, x1, y1, z1, x, y, z, agentRadius, 0.0f);
			if (NativePathConfig.NATIVE_PATH_DEBUG) {
				if (path != null) {
					LOG.info("NATIVE_PATH [LOC]: [{}] ({}, {}, {}) -> ({}, {}, {}) | {} waypoints | r={}",
							pathOwner.getName(), x1, y1, z1, x, y, z, path.length, agentRadius);
				} else {
					LOG.debug("NATIVE_PATH [LOC]: [{}] Sem rota para ({}, {}, {})",
							pathOwner.getName(), x, y, z);
				}
			}
			return path;
		} finally {
			recordQuery(start);
		}
	}

	/**
	 * Consulta a altitude Z da superfície navegável CryEngine em um mundo e posição informados.
	 */
	public float getSurfaceZ(int worldId, float x, float y, float z) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return Float.NaN;

		NativePathMap map = data.getNativeMap(worldId);
		if (map == null)
			return Float.NaN;

		return map.getSurfaceZ(x, y, z, z);
	}

	/**
	 * Verifica se a coordenada 3D é transitável no mapa de navegação nativo.
	 */
	public boolean isWalkable(int worldId, float x, float y, float z) {
		if (!NativePathConfig.NATIVE_PATH_ENABLE)
			return false;

		NativePathMap map = data.getNativeMap(worldId);
		if (map == null)
			return false;

		return map.isWalkable(x, y, z, 2.0f);
	}

	public static NativePathService getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private static final class SingletonHolder {
		static final NativePathService INSTANCE = new NativePathService();
	}
}
