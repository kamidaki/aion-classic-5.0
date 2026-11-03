package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_KEY extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(con.enableCryptKey());
	}
}
