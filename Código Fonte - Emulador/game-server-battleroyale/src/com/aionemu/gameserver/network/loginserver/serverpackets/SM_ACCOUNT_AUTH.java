package com.aionemu.gameserver.network.loginserver.serverpackets;

import com.aionemu.gameserver.network.loginserver.LoginServerConnection;
import com.aionemu.gameserver.network.loginserver.LsServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_ACCOUNT_AUTH extends LsServerPacket {

	/**
	 * accountId [part of session key]
	 */
	private final int accountId;
	/**
	 * loginOk [part of session key]
	 */
	private final int loginOk;
	/**
	 * playOk1 [part of session key]
	 */
	private final int playOk1;
	/**
	 * playOk2 [part of session key]
	 */
	private final int playOk2;

	/**
	 * Constructs new instance of <tt>SM_ACCOUNT_AUTH </tt> packet.
	 * 
	 * @param accountId
	 *          account identifier.
	 * @param loginOk
	 * @param playOk1
	 * @param playOk2
	 */
	public SM_ACCOUNT_AUTH(int accountId, int loginOk, int playOk1, int playOk2) {
		super(0x01);
		this.accountId = accountId;
		this.loginOk = loginOk;
		this.playOk1 = playOk1;
		this.playOk2 = playOk2;
	}

	@Override
	protected void writeImpl(LoginServerConnection con) {
		writeD(accountId);
		writeD(loginOk);
		writeD(playOk1);
		writeD(playOk2);
	}
}
