package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Security token / auth state (Opcode 0x0102 in 5.0 Classic).
 */
public class S_SECURITY_TOKEN extends AionServerPacket {

	private byte[] tokenData;

	public S_SECURITY_TOKEN() {
		this(new byte[32]);
	}

	public S_SECURITY_TOKEN(byte[] tokenData) {
		this.tokenData = tokenData;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (tokenData != null) {
			writeB(tokenData);
		} else {
			writeB(new byte[32]);
		}
	}
}
