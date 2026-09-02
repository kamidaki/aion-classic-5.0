package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Gather/combine cooldown info (Opcode 0x00A4 in 5.0 Classic).
 */
public class S_LOAD_GATHERCOMBINE_COOLTIME extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(1);
		writeH(0);
	}
}
