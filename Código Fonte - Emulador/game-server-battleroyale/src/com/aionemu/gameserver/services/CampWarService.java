package com.aionemu.gameserver.services;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicBoolean;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.configs.main.SiegeConfig;
import com.aionemu.gameserver.dao.SiegeDAO;
import com.aionemu.gameserver.dataholders.CampWorldStateData;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.base.BaseOccupier;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.siege.CampLocation;
import com.aionemu.gameserver.model.siege.SiegeRace;
import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.model.templates.spawns.basespawns.BaseSpawnTemplate;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CAMP_PVP_ZONE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEGE_LOCATION_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SIEGE_LOCATION_STATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_WORLD_VARIABLE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ZONE_STATE_LIST;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldMap;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * Camp war das torres "Watching Eye" de Tiamaranta Mesa (LDF4b).
 * <p>
 * Todo o ciclo e a ordem dos pacotes vem das duas capturas oficiais 5.0 (2026-09-13 e 2026-09-15):
 *
 * <pre>
 * torre tomada (boss morto)  -> S_ZONE_PVP(0) ; S_CHANGE_ABYSS_PVP_STATUS(0) ; S_ABYSS_INFO(update) ; troca a guarnicao
 *                               fica protegida por 300/600/900 s, sem boss e sem MistOn
 * fim da protecao            -> S_CHANGE_ABYSS_PVP_STATUS(3) ; S_ABYSS_INFO(update) ; nascem boss e MistOn ; S_ZONE_PVP(1)
 * vulneravel e de uma raca   -> se ninguem tomar em 300 s, os Balaur retomam (STR_CAMP_RESET_CHANGE_RACE)
 * vulneravel e dos Balaur    -> fica assim ate alguem matar o boss
 * </pre>
 *
 * Torre com {@code camp_reset_time} 0 nao entra no ciclo: fica protegida para sempre, como o oficial mostra para as 14
 * torres que a Gameforge deixou desligadas.
 *
 * @author Lost Academy Team & Durak
 */
public class CampWarService {

	private static final Logger log = LoggerFactory.getLogger("SIEGE_LOG");
	private static final CampWarService INSTANCE = new CampWarService();

	private final Map<Integer, CampLocation> camps;
	private final AtomicBoolean initialized = new AtomicBoolean();

	private CampWarService() {
		camps = SiegeConfig.SIEGE_ENABLED ? DataManager.SIEGE_LOCATION_DATA.getCamps() : Collections.emptyMap();
	}

	public static CampWarService getInstance() {
		return INSTANCE;
	}

	/**
	 * Comeca o camp war. Roda depois do {@link SiegeService#initSieges()}, que e quem carrega dono e legiao do banco.
	 */
	public void initCamps() {
		if (!initialized.compareAndSet(false, true) || camps.isEmpty())
			return;
		log.info("Initializing camp war ({} towers)...", camps.size());
		for (CampLocation camp : camps.values()) {
			if (camp.isStatic()) {
				// Torre desligada: fica protegida e sem proxima fase. O oficial manda nextState 0 nas 14 desligadas
				// e 1 so nas que ainda tem prazo correndo (offset 19 do S_ABYSS_INFO).
				camp.setVulnerable(false);
				camp.setNextState(0);
				try {
					// as de raca fixa tem guarnicao, estatua e NPC de quest (4402, 4414 e 40008 na captura de 16/09);
					// nunca ficam vulneraveis, entao nao nasce boss nem MistOn
					startBase(camp);
				} catch (Exception e) {
					log.error("Could not start static camp {}, its tower stays offline", camp.getLocationId(), e);
				}
				continue;
			}
			try {
				startBase(camp);
				enterProtected(camp, false);
			} catch (Exception e) {
				// Falta de template ou de spawn numa torre nao pode derrubar o servidor inteiro na subida.
				log.error("Could not start camp {}, its tower stays offline", camp.getLocationId(), e);
			}
		}
	}

	public CampLocation getCamp(int locationId) {
		return camps.get(locationId);
	}

	public boolean isCamp(int locationId) {
		return camps.containsKey(locationId);
	}

	public Collection<CampLocation> getCamps() {
		return camps.values();
	}

	// ------------------------------------------------------------------ fases

	/** Protegida: sem boss, sem MistOn e sem PvP na area. E a fase que comeca sempre que a torre troca de dono. */
	private void enterProtected(CampLocation camp, boolean trocouDeDono) {
		cancelPhaseTask(camp);
		camp.setVulnerable(false);
		camp.setNextState(1);
		camp.setPhaseEndMillis(System.currentTimeMillis() + camp.getProtectTime() * 1000L);

		sendPvpZone(camp, false);
		broadcastState(camp);
		if (trocouDeDono)
			BaseService.getInstance().capture(camp.getLocationId(), BaseOccupier.valueOf(camp.getRace().name()));
		else
			despawnVulnerableNpcs(camp);

		log.info("Camp {} -> PROTEGIDA por {} s, dono {} (legiao {})", camp.getLocationId(), camp.getProtectTime(),
			camp.getRace(), camp.getLegionId());
		camp.setPhaseTask(schedule(() -> enterVulnerable(camp), camp.getProtectTime() * 1000L));
	}

	/** Vulneravel: nascem o boss e o MistOn e a area vira PvP. So aqui a torre pode trocar de dono. */
	private void enterVulnerable(CampLocation camp) {
		cancelPhaseTask(camp);
		camp.setVulnerable(true);
		camp.setNextState(0);
		boolean deRaca = camp.getRace() != SiegeRace.BALAUR;
		camp.setPhaseEndMillis(deRaca ? System.currentTimeMillis() + camp.getResetTime() * 1000L : 0);

		broadcastState(camp);
		spawnVulnerableNpcs(camp);
		sendPvpZone(camp, true);
		// Sem mensagem de sistema aqui: nas duas capturas o oficial so manda texto na conquista (1403775) e na
		// retomada dos Balaur (1403777). STR_CAMP_PVP_ON/OFF nao aparecem nenhuma vez em 28.316 + 3.057 pacotes.

		log.info("Camp {} -> VULNERAVEL, dono {}{}", camp.getLocationId(), camp.getRace(),
			deRaca ? ", Balaur retomam em " + camp.getResetTime() + " s" : " (sem prazo)");
		if (deRaca)
			camp.setPhaseTask(schedule(() -> balaurReset(camp), camp.getResetTime() * 1000L));
	}

	/** Fim do prazo sem ninguem tomar: os Balaur retomam a torre (STR_CAMP_RESET_CHANGE_RACE). */
	private void balaurReset(CampLocation camp) {
		if (camp.getRace() == SiegeRace.BALAUR)
			return;
		camp.setRace(SiegeRace.BALAUR);
		camp.setLegionId(0);
		SiegeDAO.updateSiegeLocation(camp);
		broadcastToMap(camp, SM_SYSTEM_MESSAGE.STR_CAMP_RESET_CHANGE_RACE(race(SiegeRace.BALAUR), name(camp)));
		enterProtected(camp, true);
	}

	// ------------------------------------------------------------------ captura

	/**
	 * Chamado quando morre o NPC marcado como {@code handler="BOSS"} de um base spawn. So a torre vulneravel troca de
	 * dono -- na protegida o boss nem existe.
	 */
	public void onBaseBossKilled(BaseSpawnTemplate spawn, Creature killer) {
		CampLocation camp = camps.get(spawn.getId());
		if (camp == null)
			return; // base comum, nao e torre
		synchronized (camp) {
			if (camp.isStatic() || !camp.isVulnerable()) {
				log.warn("Camp {} boss died but the tower is {}, no capture", camp.getLocationId(),
					camp.isStatic() ? "static" : "protected");
				return;
			}
			Player player = killer instanceof Player p ? p : killer != null && killer.getMaster() instanceof Player m ? m : null;
			if (player == null) {
				log.warn("Camp {} boss died with no player killer ({}), no capture", camp.getLocationId(), killer);
				return;
			}
			SiegeRace nova = SiegeRace.getByRace(player.getRace());
			if (nova == camp.getRace()) {
				log.info("Camp {} boss died but {} already owns it", camp.getLocationId(), nova);
				return;
			}
			camp.setVulnerable(false);
			Legion legion = player.getLegion();
			captura(camp, nova, legion == null ? 0 : legion.getLegionId(), legion == null ? null : legion.getName());
		}
	}

	/**
	 * Troca o dono da torre e recomeca a fase protegida. Serve tanto para a morte do boss quanto para o comando de
	 * administrador, que e como da para testar sem esperar o prazo de protecao.
	 */
	public void captura(CampLocation camp, SiegeRace nova, int legionId, String legionName) {
		cancelPhaseTask(camp);
		camp.setVulnerable(false);
		camp.setRace(nova);
		camp.setLegionId(legionId);
		camp.setOccupiedCount(camp.getOccupiedCount() + 1);
		SiegeDAO.updateSiegeLocation(camp);
		log.info("Camp {} conquistada por {} (legiao {} '{}')", camp.getLocationId(), nova, legionId, legionName);

		broadcastToMap(camp, legionName == null ? SM_SYSTEM_MESSAGE.STR_CAMP_WIN_FORT(race(nova), name(camp))
			: SM_SYSTEM_MESSAGE.STR_CAMP_GUILD_WIN_FORT(race(nova), legionName, name(camp)));
		// fora do onDie: a troca de guarnicao apaga o proprio boss que esta morrendo
		ThreadPoolManager.getInstance().schedule(() -> {
			try {
				enterProtected(camp, true);
			} catch (Exception e) {
				// sem isto o executor engole a falha e a torre fica com o dono novo mas sem trocar a guarnicao
				log.error("Falhou ao trocar a guarnicao da torre {}", camp.getLocationId(), e);
			}
		}, 1000);
	}

	/** Antecipa a vulnerabilidade (comando de administrador); e o que faz o boss nascer. */
	public void tornaVulneravel(CampLocation camp) {
		enterVulnerable(camp);
	}

	// ------------------------------------------------------------------ spawns

	private void startBase(CampLocation camp) {
		int id = camp.getLocationId();
		if (BaseService.getInstance().getBaseLocation(id) == null)
			return; // torre sem dados de spawn: so o estado vai para o cliente
		BaseService.getInstance().getBaseLocation(id).setOccupier(BaseOccupier.valueOf(camp.getRace().name()));
		if (!BaseService.getInstance().isActive(id))
			BaseService.getInstance().start(id);
	}

	private void spawnVulnerableNpcs(CampLocation camp) {
		if (BaseService.getInstance().getActiveBase(camp.getLocationId()) instanceof CampBaseHolder holder)
			holder.spawnVulnerableNpcs();
	}

	private void despawnVulnerableNpcs(CampLocation camp) {
		if (BaseService.getInstance().getActiveBase(camp.getLocationId()) instanceof CampBaseHolder holder)
			holder.despawnVulnerableNpcs();
	}

	/** Implementado pelo {@code CampBase}; mantem o servico independente do pacote de bases. */
	public interface CampBaseHolder {

		void spawnVulnerableNpcs();

		void despawnVulnerableNpcs();
	}

	// ------------------------------------------------------------------ rede

	/** S_CHANGE_ABYSS_PVP_STATUS e o S_ABYSS_INFO de uma linha, na ordem em que o oficial manda. */
	private void broadcastState(CampLocation camp) {
		int estado = camp.isVulnerable() ? SM_SIEGE_LOCATION_STATE.VULNERAVEL : SM_SIEGE_LOCATION_STATE.PROTEGIDA;
		SM_SIEGE_LOCATION_STATE pkt = new SM_SIEGE_LOCATION_STATE(camp.getLocationId(), estado);
		SM_SIEGE_LOCATION_INFO info = new SM_SIEGE_LOCATION_INFO(camp);
		World.getInstance().forEachPlayer(player -> {
			PacketSendUtility.sendPacket(player, pkt);
			PacketSendUtility.sendPacket(player, info);
		});
	}

	/** A zona PvP so existe no mapa da torre, entao o 0x187 vai so para quem esta nele. */
	private void sendPvpZone(CampLocation camp, boolean ligada) {
		if (camp.getPvpZoneName() == null)
			return;
		broadcastToMap(camp, new SM_CAMP_PVP_ZONE(camp.getPvpZoneName(), ligada));
	}

	private void broadcastToMap(CampLocation camp, com.aionemu.gameserver.network.aion.AionServerPacket packet) {
		WorldMap world = World.getInstance().getWorldMap(camp.getWorldId());
		WorldMapInstance map = world == null ? null : world.getMainWorldMapInstance();
		if (map != null)
			PacketSendUtility.broadcastToMap(map, packet);
	}

	/**
	 * O que o oficial manda ao entrar no mundo, na ordem da captura de 2026-09-16 (#114 e #185-#189):
	 * <ol>
	 * <li>S_ABYSS_INFO com a lista inteira. Sem ela o cliente so conhece uma torre quando ela muda de estado, e as que
	 * nunca mudam (as 14 desligadas, entre elas as 6 de raca fixa) ficam com o icone branco no mapa;</li>
	 * <li>no mapa de camp war, as variaveis de mundo (0x180) e a lista de zonas (0x19D), com as TowerWar seguindo a
	 * vulnerabilidade de cada torre agora.</li>
	 * </ol>
	 */
	public void onEnterWorld(Player player) {
		if (camps.isEmpty())
			return;
		PacketSendUtility.sendPacket(player, new SM_SIEGE_LOCATION_INFO());

		CampWorldStateData.CampWorld mundo = DataManager.CAMP_WORLD_STATE_DATA == null ? null
			: DataManager.CAMP_WORLD_STATE_DATA.getWorld(player.getWorldId());
		if (mundo == null)
			return;
		for (CampWorldStateData.Variable v : mundo.getVariables())
			PacketSendUtility.sendPacket(player, new SM_WORLD_VARIABLE(mundo.getWorldId(), v.getName(), v.getValue()));
		for (CampWorldStateData.ZonePacket pacote : mundo.getZonePackets()) {
			List<SM_ZONE_STATE_LIST.ZoneState> zonas = new ArrayList<>(pacote.getZones().size());
			for (CampWorldStateData.Zone z : pacote.getZones()) {
				CampLocation camp = z.getCamp() == 0 ? null : camps.get(z.getCamp());
				int estado = camp != null ? (camp.isVulnerable() ? 1 : 0) : z.getState();
				zonas.add(new SM_ZONE_STATE_LIST.ZoneState(z.getName(), estado));
			}
			PacketSendUtility.sendPacket(player, new SM_ZONE_STATE_LIST(zonas));
		}
	}

	// ------------------------------------------------------------------ util

	private DescriptionId name(CampLocation camp) {
		return new DescriptionId(camp.getTemplate().getL10nId() << 1 | 1);
	}

	private DescriptionId race(SiegeRace race) {
		// 900240 Elyos, 900241 Asmodianos, 900242 Balaur -- os mesmos ids do SiegeRace.BALAUR
		return new DescriptionId((900240 + race.getRaceId()) << 1 | 1);
	}

	private Future<?> schedule(Runnable tarefa, long atrasoMillis) {
		return ThreadPoolManager.getInstance().schedule(tarefa, Math.max(atrasoMillis, 1000L));
	}

	private void cancelPhaseTask(CampLocation camp) {
		Future<?> task = camp.getPhaseTask();
		if (task != null && !task.isDone())
			task.cancel(false);
		camp.setPhaseTask(null);
	}
}
