package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * NetPasskey auth token packet.
 * Opcode: 264 (0x108)
 */
public class SM_REPLY_NP_AUTH_TOKEN extends AionServerPacket {

	private final String hexString;

	public SM_REPLY_NP_AUTH_TOKEN(String hexString) {
		this.hexString = hexString;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeB(hexStringToByteArray(hexString));
	}

	private static byte[] hexStringToByteArray(String s) {
		int len = s.length();
		byte[] data = new byte[len / 2];
		for (int i = 0; i < len; i += 2) {
			data[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4)
								 + Character.digit(s.charAt(i + 1), 16));
		}
		return data;
	}
}
