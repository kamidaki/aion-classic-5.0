package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SP de um jogador para quem o vê, o próprio incluído. 5.0 oficial: 0x166, 6 b, no mesmo tick do 0x14B.
 */
public class SM_SP_UPDATE_OTHER extends AionServerPacket {

	private final int objectId;
	private final int sp;

	public SM_SP_UPDATE_OTHER(int objectId, int sp) {
		this.objectId = objectId;
		this.sp = sp;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeH(sp);
	}
}
