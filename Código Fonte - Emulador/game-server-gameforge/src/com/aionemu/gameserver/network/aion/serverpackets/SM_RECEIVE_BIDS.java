package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_RECEIVE_BIDS extends AionServerPacket {

	private final int unk;

	public SM_RECEIVE_BIDS(int unk) {
		this.unk = unk;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(unk);
	}

}
