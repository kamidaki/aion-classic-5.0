package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Warmup / Arena reputation packet (Opcode 0x01C2 in 5.0 Classic).
 */
public class S_WARMUP_REPUTATION extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(2);
		writeD(5);
		writeD(0);
		writeH(6);
	}
}
