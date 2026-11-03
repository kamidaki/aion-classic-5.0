package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_AFTER_TIME_CHECK_4_7_5 extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(1);
		writeD(0);
	}
}
