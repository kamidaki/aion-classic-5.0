package com.aionemu.gameserver.network.loginserver.serverpackets;

import com.aionemu.gameserver.network.loginserver.LoginServerConnection;
import com.aionemu.gameserver.network.loginserver.LsServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_ACCOUNT_RECONNECT_KEY extends LsServerPacket {

	/**
	 * AccountId of client that is requested reconnection to LoginServer.
	 */
	private final int accountId;

	/**
	 * Constructs new instance of <tt>SM_ACCOUNT_RECONNECT_KEY </tt> packet.
	 * 
	 * @param accountId
	 *          account identifier.
	 */
	public SM_ACCOUNT_RECONNECT_KEY(int accountId) {
		super(0x02);
		this.accountId = accountId;
	}

	@Override
	protected void writeImpl(LoginServerConnection con) {
		writeD(accountId);
	}
}
