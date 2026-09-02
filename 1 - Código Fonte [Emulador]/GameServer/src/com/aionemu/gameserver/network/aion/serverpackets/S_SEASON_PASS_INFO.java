package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Season pass / quest info (Opcode 0x0110 in 5.0 Classic).
 */
public class S_SEASON_PASS_INFO extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(1);
		writeD(0x0F206D58);
		writeD(0);
		writeC(2);
		writeC(1);
		writeB(new byte[24]);
	}
}
