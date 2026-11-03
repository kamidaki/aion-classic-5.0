package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_MAY_LOGIN_INTO_GAME extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		/**
		 * probably here is msg if fail.
		 */
		writeD(0x00);
	}
}
