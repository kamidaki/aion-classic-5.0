package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_EXCHANGE_REQUEST extends AionServerPacket {

	private String receiver;

	public SM_EXCHANGE_REQUEST(String receiver) {
		this.receiver = receiver;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeS(receiver);
	}
}
