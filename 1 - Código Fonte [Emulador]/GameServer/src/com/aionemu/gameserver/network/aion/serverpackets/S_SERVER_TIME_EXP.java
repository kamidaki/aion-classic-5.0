package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Server time boost / EXP rate (Opcode 0x0181 in 5.0 Classic).
 */
public class S_SERVER_TIME_EXP extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(1);
		writeD(0x0003627C);
		writeD(0x800C8B28);
		writeD(0x000269FD);
		writeD(0x000269FD);
		writeB(new byte[18]);
	}
}
