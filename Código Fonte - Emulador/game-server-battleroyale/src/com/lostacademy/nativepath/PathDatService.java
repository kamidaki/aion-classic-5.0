package com.lostacademy.nativepath;

import java.io.File;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.GeoDataConfig;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.templates.world.WorldMapTemplate;
import com.aionemu.gameserver.world.geo.GeoService;

/**
 * Caminho de NPC pela grade oficial do path.dat ({@link PathDatMap} + {@link PathDatGrid}). Cada mapa é carregado na primeira busca
 * e fica em memória. Usado na perseguição e na volta ao spawn. Num mapa com grade, sem caminho na grade não há caminho (a navmesh
 * fica só para mapas sem path.dat e NPCs que voam).
 */
public final class PathDatService {

	private static final Logger log = LoggerFactory.getLogger(PathDatService.class);

	private final Map<Integer, Optional<PathDatGrid>> grades = new ConcurrentHashMap<>();

	/** Última busca sem caminho de cada NPC: mesma célula de partida e de destino não é buscada de novo antes de {@link #ESPERA_SEM_CAMINHO_MS}. */
	private record SemCaminho(long partida, long destino, long quando) {
	}

	private static final long ESPERA_SEM_CAMINHO_MS = 1000;
	private final Map<Integer, SemCaminho> semCaminho = new ConcurrentHashMap<>();

	/** Desde quando a perseguição de cada NPC não acha rota andando até o alvo (removido ao achar). */
	private final Map<Integer, Long> inalcancavelDesde = new ConcurrentHashMap<>();

	public static PathDatService getInstance() {
		return SingletonHolder.INSTANCE;
	}

	private PathDatService() {
	}

	private Optional<PathDatGrid> grade(int worldId) {
		if (!GeoDataConfig.PATHDAT_ENABLE)
			return Optional.empty();
		return grades.computeIfAbsent(worldId, this::carrega);
	}

	/** O mapa tem grade (path.dat): o chão dele é decidido por ela, a navmesh não é usada. */
	public boolean temGrade(int worldId) {
		return grade(worldId).isPresent();
	}

	/** Altura do piso livre da grade em (x, y) mais perto de z; NaN sem grade ou se a célula não tem piso livre. */
	public float pisoZ(int worldId, float x, float y, float z) {
		Optional<PathDatGrid> g = grade(worldId);
		return g.isEmpty() ? Float.NaN : g.get().alturaPiso(x, y, z);
	}

	/** Linha reta andável pela grade entre as duas criaturas (sem queda); true se o mapa não tem grade. */
	public boolean retaAndavel(Creature a, Creature b) {
		Optional<PathDatGrid> g = grade(a.getWorldId());
		return g.isEmpty() || g.get().retaAndavel(a.getX(), a.getY(), a.getZ(), b.getX(), b.getY(), b.getZ());
	}

	private Optional<PathDatGrid> carrega(int worldId) {
		File[] dirs = new File(GeoDataConfig.PATHDAT_DIR).listFiles((d, nome) -> nome.startsWith(worldId + "_"));
		if (dirs == null || dirs.length == 0)
			return Optional.empty();
		File[] dats = dirs[0].listFiles((d, nome) -> nome.toLowerCase().endsWith(".dat"));
		if (dats == null || dats.length == 0)
			return Optional.empty();
		WorldMapTemplate t = DataManager.WORLD_MAPS_DATA.getTemplate(worldId);
		int tamanho = t == null || t.getWorldSize() <= 0 ? 3072 : t.getWorldSize();
		long t0 = System.currentTimeMillis();
		try {
			PathDatMap m = PathDatMap.carrega(Path.of(dats[0].getPath()), tamanho,
				(x, y) -> GeoService.getInstance().getTerrainHeight(worldId, x, y));
			log.info("path.dat de {} carregado em {} ms ({} m, {})", worldId, System.currentTimeMillis() - t0, m.getTamanho(), dats[0].getName());
			return Optional.of(new PathDatGrid(m, GeoDataConfig.PATHDAT_FOLLOW_FLOOR, GeoDataConfig.PATHDAT_ALLOW_DROP));
		} catch (Exception e) {
			log.warn("path.dat de {} não carregou ({}): {}", worldId, dats[0].getName(), e.toString());
			return Optional.empty();
		}
	}

	/**
	 * true se o NPC anda pela grade neste mapa (grade ligada, mapa com path.dat, NPC de chão). Nesse caso, sem caminho na grade não há
	 * caminho: a navmesh antiga não serve de reserva (é ela que atravessa parede fora de Pandaemonium).
	 */
	public boolean usaGrade(Creature npc) {
		return GeoDataConfig.PATHDAT_ENABLE && npc != null && !npc.isFlying() && npc.getInstanceId() >= 0 && grade(npc.getWorldId()).isPresent();
	}

	/**
	 * Caminho do NPC até (x, y, z), sem o ponto de partida; null se o mapa não tem grade, o NPC voa ou não há caminho.
	 */
	public float[][] caminho(Creature npc, float x, float y, float z) {
		return caminho(npc, x, y, z, Float.MAX_VALUE);
	}

	/** Perseguição: rota andando de até gameserver.geodata.pathdat.max_path_length metros; mais longa = alvo inalcançável. */
	public float[][] caminhoAteAlvo(Creature npc, float x, float y, float z) {
		float[][] r = caminho(npc, x, y, z, GeoDataConfig.PATHDAT_MAX_PATH_LENGTH);
		if (npc != null) {
			if (r != null)
				inalcancavelDesde.remove(npc.getObjectId());
			else if (usaGrade(npc))
				inalcancavelDesde.putIfAbsent(npc.getObjectId(), System.currentTimeMillis());
		}
		return r;
	}

	/** ms desde que o alvo da perseguição ficou sem rota andando (0 = alcançável ou sem busca). */
	public long millisInalcancavel(Creature npc) {
		Long t = inalcancavelDesde.get(npc.getObjectId());
		return t == null ? 0 : System.currentTimeMillis() - t;
	}

	/** Esquece o estado da perseguição (desistiu, morreu, trocou de alvo). */
	public void esquece(Creature npc) {
		inalcancavelDesde.remove(npc.getObjectId());
		semCaminho.remove(npc.getObjectId());
	}

	private static long celula(float x, float y, float z) {
		return ((long) (x / 0.5f) << 40) | ((long) (y / 0.5f) << 20) | ((long) Math.round(z) & 0xFFFFF);
	}

	private float[][] caminho(Creature npc, float x, float y, float z, float maxComprimento) {
		if (!GeoDataConfig.PATHDAT_ENABLE || npc == null || npc.isFlying() || npc.getInstanceId() < 0)
			return null;
		Optional<PathDatGrid> g = grade(npc.getWorldId());
		if (g.isEmpty())
			return null;
		long partida = celula(npc.getX(), npc.getY(), npc.getZ()), destino = celula(x, y, z), agora = System.currentTimeMillis();
		SemCaminho sc = semCaminho.get(npc.getObjectId());
		if (sc != null && sc.partida() == partida && sc.destino() == destino && agora - sc.quando() < ESPERA_SEM_CAMINHO_MS)
			return null;
		try {
			List<float[]> r = g.get().encontra(npc.getX(), npc.getY(), npc.getZ(), x, y, z, GeoDataConfig.PATHDAT_MAX_NODES, maxComprimento);
			if (r == null || r.isEmpty()) {
				if (semCaminho.size() > 5000)
					semCaminho.values().removeIf(v -> agora - v.quando() > ESPERA_SEM_CAMINHO_MS);
				semCaminho.put(npc.getObjectId(), new SemCaminho(partida, destino, agora));
				return null;
			}
			semCaminho.remove(npc.getObjectId());
			// o último ponto é o pedido exato (passo de rota, posição do alvo), com o z do piso da grade: o centro da célula fica até
			// 0,35 m fora e a chegada no passo é medida em x/y
			float[] ult = r.get(r.size() - 1);
			if ((int) (ult[0] / 0.5f) == (int) (x / 0.5f) && (int) (ult[1] / 0.5f) == (int) (y / 0.5f)) {
				ult[0] = x;
				ult[1] = y;
			}
			return r.toArray(new float[0][]);
		} catch (RuntimeException e) {
			log.warn("path.dat: busca falhou em {} ({}, {}, {}) -> ({}, {}, {}): {}", npc.getWorldId(), npc.getX(), npc.getY(), npc.getZ(), x, y, z,
				e.toString());
			return null;
		}
	}

	private static final class SingletonHolder {

		private static final PathDatService INSTANCE = new PathDatService();
	}
}
