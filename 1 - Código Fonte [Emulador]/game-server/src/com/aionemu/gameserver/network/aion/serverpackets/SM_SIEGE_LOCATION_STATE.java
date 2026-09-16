package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.siege.SiegeLocation;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_SIEGE_LOCATION_STATE extends AionServerPacket {

	/** Estados medidos no S_CHANGE_ABYSS_PVP_STATUS oficial 5.0: 0 protegida, 3 vulneravel. */
	public static final int PROTEGIDA = 0, VULNERAVEL = 3;

	private int locationId;
	private int state;

	public SM_SIEGE_LOCATION_STATE(SiegeLocation location) {
		this.locationId = location.getLocationId();
		this.state = location.isVulnerable() ? VULNERAVEL : PROTEGIDA;
	}

	public SM_SIEGE_LOCATION_STATE(int locationId, int state) {
		this.locationId = locationId;
		this.state = state;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		// 5.0 oficial: [D locId][D estado][C 0] = 9 bytes. Medido nas capturas de Tiamaranta (2026-09-13 e 15):
		// 3d110000 03000000 00 = loc 4413 vulneravel, 3d110000 00000000 00 = loc 4413 protegida.
		writeD(locationId);
		writeD(state);
		writeC(0);
	}

}
