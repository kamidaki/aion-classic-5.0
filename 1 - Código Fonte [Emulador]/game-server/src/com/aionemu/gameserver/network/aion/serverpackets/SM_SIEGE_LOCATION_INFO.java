package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.HashMap;
import java.util.Map;

import com.aionemu.gameserver.configs.main.SiegeConfig;
import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.siege.SiegeLocation;
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
			writeH(emblem.getEmblemId() & 0xFFFF); // 2
			writeH(emblem.getEmblemType().getValue() & 0xFFFF); // 2
			writeC(emblem.getColor_a()); // 1
			writeC(emblem.getColor_r()); // 1
			writeC(emblem.getColor_g()); // 1
			writeC(emblem.getColor_b()); // 1
			writeC(loc.getRace().getRaceId()); // 1
			writeC(loc.isVulnerable() ? 2 : 0); // 1 (0 - no, 2 - yes)
			writeC(loc.isCanTeleport(player) ? 1 : 0); // 1
			writeC(loc.getNextState()); // 1 (0 - invulnerable, 1 - vulnerable)
			writeD(locId == 2111 || locId == 3111 ? SiegeService.getInstance().getRemainingSiegeTimeInSeconds(locId) : 0); // 4 (veille/masta timer)
			writeD(0); // 4
			writeD(NetworkConfig.GAMESERVER_ID); // 4 (server ID of the fortress owner)
			writeD(0); // 4
			writeD(0); // 4
			writeD(loc.getOccupiedCount()); // 4
			// 4+4+2+2+1+1+1+1+1+1+1+1+4+4+4+4+4+4 = exactly 44 bytes per entry
		}
	}
}
