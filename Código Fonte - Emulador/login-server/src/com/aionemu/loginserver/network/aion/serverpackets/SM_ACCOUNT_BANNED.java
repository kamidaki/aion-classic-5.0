package com.aionemu.loginserver.network.aion.serverpackets;

import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.LoginConnection;

/**
 * @author Lost Academy Team & Durak
 */
public final class SM_ACCOUNT_BANNED extends AionServerPacket {

	public SM_ACCOUNT_BANNED() {
		super(0x02);
	}

	@Override
	protected void writeImpl(LoginConnection con) {
		// maybe some option to specify a custom message (STR_L2AUTH_BLOCK_*)? need retail sniff
	}
}
