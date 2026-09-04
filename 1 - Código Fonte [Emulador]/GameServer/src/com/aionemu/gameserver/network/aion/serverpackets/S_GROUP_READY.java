package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_GROUP_READY extends AionServerPacket {

	private int playerObjectId;
	private int statusCode;

	public S_GROUP_READY(int playerObjectId, int statusCode) {
		this.playerObjectId = playerObjectId;
		this.statusCode = statusCode;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjectId);
		writeC(statusCode);
	}

}
