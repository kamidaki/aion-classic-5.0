package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_LOAD_CLIENT_SETTINGS extends AionServerPacket
{
	private byte[] data;
	private int type;
	
	public S_LOAD_CLIENT_SETTINGS(byte[] data, int type) {
		this.data = data;
		this.type = type;
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		writeC(type);
		writeH(0x1C00);
		writeB(data);
		if (0x1C00 > data.length)
			writeB(new byte[0x1C00 - data.length]);
	}
}