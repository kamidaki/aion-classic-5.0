package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Achievement reward notification (Opcode 0x0114 in 5.0 Classic).
 */
public class S_ACHIEVEMENT_REWARD_NOTI extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(1);
		writeH(4);
		writeD(0x0F206D58);
		writeD(0);
		writeD(0x0931);
		writeB(new byte[50]);
	}
}
