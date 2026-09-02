package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Account reputation info (Opcode 0x0105 in 5.0 Classic).
 */
public class S_ACCOUNT_REPUTATION extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(1);
		writeD(0);
		writeD(0);
	}
}
