package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * EP de um jogador para quem o vê, o próprio incluído. 5.0 oficial: 0x176, 6 b, no mesmo tick do 0x175.
 */
public class SM_EP_UPDATE_OTHER extends AionServerPacket {

	private final int objectId;
	private final int ep;

	public SM_EP_UPDATE_OTHER(int objectId, int ep) {
		this.objectId = objectId;
		this.ep = ep;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeH(ep);
	}
}
