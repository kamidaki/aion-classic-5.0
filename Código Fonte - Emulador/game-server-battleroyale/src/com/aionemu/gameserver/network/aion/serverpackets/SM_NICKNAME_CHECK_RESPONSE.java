package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_NICKNAME_CHECK_RESPONSE extends AionServerPacket {

	/**
	 * Value of response object
	 */
	private final int value;

	/**
	 * Constructs new <tt>SM_NICKNAME_CHECK_RESPONSE</tt> packet
	 * 
	 * @param value
	 *          Response value
	 */
	public SM_NICKNAME_CHECK_RESPONSE(int value) {
		this.value = value;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		/**
		 * Here is some msg: 0x00 = ok 0x0A = not ok and much more
		 */
		writeC(value);
	}
}
