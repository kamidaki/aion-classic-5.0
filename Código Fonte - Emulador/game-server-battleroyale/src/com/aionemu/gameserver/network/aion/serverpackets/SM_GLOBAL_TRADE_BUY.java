package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_BUY (0x13E), depois da compra: [C 0][Q anúncio][D quantidade][D 0] (2 de 2 nas capturas).
 */
public class SM_GLOBAL_TRADE_BUY extends AionServerPacket {

	private final long listingId;
	private final long count;

	public SM_GLOBAL_TRADE_BUY(long listingId, long count) {
		this.listingId = listingId;
		this.count = count;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0);
		writeQ(listingId);
		writeD((int) count);
		writeD(0);
	}
}
