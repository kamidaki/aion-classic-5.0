package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_SHOP_POINT_INFO extends AionServerPacket {

	private long tollCount;

	public S_SHOP_POINT_INFO(long tollCount) {
		this.tollCount = tollCount;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeQ(tollCount);
		writeQ(150);
	}
}
