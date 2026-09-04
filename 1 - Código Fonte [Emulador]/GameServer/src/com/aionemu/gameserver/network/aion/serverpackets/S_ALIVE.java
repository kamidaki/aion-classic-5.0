package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_ALIVE extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0x00);
		writeC(0x00);
	}
}
