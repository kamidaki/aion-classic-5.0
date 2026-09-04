package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_XCHG_GOLD extends AionServerPacket {

	private long itemCount;
	private int action;

	public S_XCHG_GOLD(long itemCount, int action) {
		this.itemCount = itemCount;
		this.action = action;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(action); // 0 -self 1-other
		writeD((int) itemCount); // itemId
		writeD(0); // unk
	}
}
