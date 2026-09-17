package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.HashMap;
import java.util.Map;

import com.aionemu.gameserver.configs.main.SiegeConfig;
import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.siege.CampLocation;
import com.aionemu.gameserver.model.siege.SiegeLocation;
import com.aionemu.gameserver.model.siege.SiegeRace;
import com.aionemu.gameserver.model.team.legion.LegionEmblem;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.LegionService;
import com.aionemu.gameserver.services.SiegeService;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_SIEGE_LOCATION_INFO extends AionServerPacket {

	/**
	 * infoType 0 - reset 1 - update
	 */
	private int infoType;
	private Map<Integer, SiegeLocation> locations;

	public SM_SIEGE_LOCATION_INFO() {
		this.infoType = 0;
		locations = SiegeService.getInstance().getSiegeLocations();
	}

	public SM_SIEGE_LOCATION_INFO(SiegeLocation loc) {
		this.infoType = 1;
		locations = new HashMap<>();
		locations.put(loc.getLocationId(), loc);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		Player player = con.getActivePlayer();
		if (!SiegeConfig.SIEGE_ENABLED) {
			writeC(0);
			writeH(0);
			return;
		}

		writeC(infoType);
		writeH(locations.size());

		for (SiegeLocation loc : locations.values()) {
			LegionEmblem emblem = new LegionEmblem();
			int legionId = loc.getLegionId();
			int locId = loc.getLocationId();
			writeD(locId); // 4
			writeD(legionId); // 4
			if (legionId != 0 && LegionService.getInstance().getLegion(legionId) != null) // can be null if legion got deleted
				emblem = LegionService.getInstance().getLegion(legionId).getLegionEmblem();
			// 5.0 oficial, torre conquistada por legiao: [C emblema][C tipo, 0x80 custom][H][C a][C r][C g][C b]. Ex.: 4413 da
			// legiao 771755128 = 04 80 f041 ff000000. O H varia entre capturas sem padrao conhecido (0961, 5e12, f041...).
			writeC(emblem.getEmblemId()); // 8
			writeC(emblem.getEmblemType().getValue()); // 9
			writeH(0); // 10
			writeC(emblem.getColor_a()); // 1
			writeC(emblem.getColor_r()); // 1
			writeC(emblem.getColor_g()); // 1
			writeC(emblem.getColor_b()); // 1
			writeC(loc.getRace().getRaceId()); // 16
			// 5.0 oficial: 0 protegida, 3 vulneravel. Em 270 entradas das duas capturas de Tiamaranta o byte so
			// assume 0 ou 3, nunca 2 (S_ABYSS_INFO, entrada de 44 bytes, offset 17).
			writeC(loc.isVulnerable() ? SM_SIEGE_LOCATION_STATE.VULNERAVEL : SM_SIEGE_LOCATION_STATE.PROTEGIDA); // 17
			writeC(loc instanceof CampLocation ? 0 : loc.isCanTeleport(player) ? 1 : 0); // 18 (camps nunca teleportam)
			writeC(loc.getNextState()); // 19 (1 enquanto protegida, 0 enquanto vulneravel)
			writeD(0); // 20 -- zerado em 270 de 270 entradas oficiais
			writeD(0); // 24
			writeD(loc instanceof CampLocation ? 0 : NetworkConfig.GAMESERVER_ID); // 28 (id do servidor dono; 0 nos camps)
			writeD(protectSeconds(loc, locId)); // 32 (segundos que faltam da fase protegida)
			writeD(resetSeconds(loc)); // 36 (segundos ate os Balaur retomarem, so quando vulneravel e de uma raca)
			writeD(loc.getOccupiedCount()); // 40
			// 4+4+2+2+4+1+1+1+1+4+4+4+4+4+4 = exactly 44 bytes per entry
		}
	}

	/**
	 * Offset 32: o que falta da fase invulneravel. Nas capturas de Tiamaranta e o prazo de protecao do camp (600 s
	 * para a 4413, uma Tower_M); nas fortalezas e o tempo ate a siege comecar.
	 */
	private int protectSeconds(SiegeLocation loc, int locId) {
		if (loc instanceof CampLocation camp)
			return camp.isVulnerable() ? 0 : camp.getRemainingPhaseSeconds();
		return locId == 2111 || locId == 3111 ? SiegeService.getInstance().getRemainingSiegeTimeInSeconds(locId) : 0;
	}

	/** Offset 36: so os camps usam -- 300 s para os Balaur retomarem uma torre de jogador que ficou vulneravel. */
	private int resetSeconds(SiegeLocation loc) {
		if (loc instanceof CampLocation camp && camp.isVulnerable() && camp.getRace() != SiegeRace.BALAUR)
			return camp.getRemainingPhaseSeconds();
		return 0;
	}
}
