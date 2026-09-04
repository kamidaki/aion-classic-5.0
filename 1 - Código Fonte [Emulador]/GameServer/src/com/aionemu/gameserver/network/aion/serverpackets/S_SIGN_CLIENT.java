package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_SIGN_CLIENT extends AionServerPacket {

	private byte[] token;

	/**
	 * @param token
	 */
	public S_SIGN_CLIENT(byte[] token) {
		this.token = token;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(token.length);
		writeB(token);
	}
}
