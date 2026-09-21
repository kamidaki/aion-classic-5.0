package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0138 (312) - SM_RANKING_BADGE (S_RANKING_BADGE)
 * Official Classic 5.0 wire: writeD(0) + writeC(1).
 */
public class SM_RANKING_BADGE extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(0);
		writeC(1);
	}
}
