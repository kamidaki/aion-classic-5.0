package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * PvP environment info (Opcode 0x00BC in 5.0 Classic).
 */
public class S_LOAD_PVP_ENV extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(0);
	}
}
