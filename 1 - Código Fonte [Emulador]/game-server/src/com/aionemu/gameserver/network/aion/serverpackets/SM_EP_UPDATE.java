package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * EP (Ki do Brawler) do próprio jogador. 5.0 oficial: 0x175, 2 b, no tick de ~1 s seguinte à mudança e só quando o valor muda.
 */
public class SM_EP_UPDATE extends AionServerPacket {

	private final int ep;

	public SM_EP_UPDATE(int ep) {
		this.ep = ep;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(ep);
	}
}
