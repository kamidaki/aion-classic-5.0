package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * This packet is response for CM_MAY_LOGIN_INTO_GAME
 * 
 */
public class S_SA_ACCOUNT_ITEM_NOTI extends AionServerPacket {

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		/**
		 * probably here is msg if fail.
		 */
		writeD(0x00);
	}
}
