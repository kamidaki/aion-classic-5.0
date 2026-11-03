package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_SECURITY_TOKEN extends AionServerPacket {

	private byte[] token;

	public SM_SECURITY_TOKEN(byte[] token) {
		this.token = token;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (token != null && token.length == 32) {
			writeB(token);
		} else if (token != null && token.length > 0) {
			byte[] fullToken = new byte[32];
			System.arraycopy(token, 0, fullToken, 0, Math.min(token.length, 32));
			writeB(fullToken);
		} else {
			writeB(new byte[32]);
		}
	}
}
