package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Skill penalty status other info (Opcode 0x00D8 in 5.0 Classic).
 */
public class S_SKILL_PENALTY_STATUS_OTHER extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0);
		writeD(0);
		writeD(0);
		writeH(0);
	}
}
