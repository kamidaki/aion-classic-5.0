package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Server packet for world environment flags (Opcode 0x019D in 5.0 Classic).
 */
public class S_WORLD_ENV_FLAGS extends AionServerPacket {

	private String flagName;

	public S_WORLD_ENV_FLAGS() {
		this("DisablePvP_DF4_");
	}

	public S_WORLD_ENV_FLAGS(String flagName) {
		this.flagName = flagName;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (flagName != null) {
			writeH(flagName.length());
			writeS(flagName);
		} else {
			writeH(0);
		}
	}
}
