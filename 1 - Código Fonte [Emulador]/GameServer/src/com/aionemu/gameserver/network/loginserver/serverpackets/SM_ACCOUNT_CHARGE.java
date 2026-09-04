package com.aionemu.gameserver.network.loginserver.serverpackets;

import com.aionemu.gameserver.network.loginserver.LoginServerConnection;
import com.aionemu.gameserver.network.loginserver.LsServerPacket;

/**
 * In this packet Gameserver is asking if given account sessionKey is valid at Loginserver side. [if user that is
 * authenticating on Gameserver is already authenticated on Loginserver]
 * 
 */
public class SM_ACCOUNT_CHARGE extends LsServerPacket {

	/**
	 * accountId [part of session key]
	 */
	private final int accountId;

	private final int type;
	/**

	/**
	 * Constructs new instance of <tt>SM_ACCOUNT_AUTH </tt> packet.
	 *
	 * @param accountId
	 *          account identifier.
	 */
	public SM_ACCOUNT_CHARGE(int accountId, int type) {
		super(0x0F);
		this.accountId = accountId;
		this.type = type;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(LoginServerConnection con) {
		writeD(accountId);
		writeD(type);
	}
}
