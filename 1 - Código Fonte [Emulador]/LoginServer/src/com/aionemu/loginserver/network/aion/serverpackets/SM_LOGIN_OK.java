package com.aionemu.loginserver.network.aion.serverpackets;

import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.LoginConnection;
import com.aionemu.loginserver.network.aion.SessionKey;


public class SM_LOGIN_OK extends AionServerPacket {

	/**
	 * accountId is part of session key - its used for security purposes
	 */
	private final int accountId;
	/**
	 * loginOk is part of session key - its used for security purposes
	 */
	private final int loginOk;

	/**
	 * Constructs new instance of <tt>SM_LOGIN_OK</tt> packet.
	 * 
	 * @param key
	 *          session key
	 */
	public SM_LOGIN_OK(SessionKey key) {
		super(0x03);
		this.accountId = key.accountId;
		this.loginOk = key.loginOk;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(LoginConnection con) {
		writeC(getOpcode());
		writeD(accountId);
		writeD(loginOk);
		writeD(0x00);
		writeD(0x00);

		// Account active flags (4x 0x0000003F)
		writeD(0x0000003F);
		writeD(0x0000003F);
		writeD(0x0000003F);
		writeD(0x0000003F);

		// Classic Signature (0xFF 0xFE 0x00 0x00)
		writeC(0xFF);
		writeC(0xFE);
		writeC(0x00);
		writeC(0x00);

		// 12 bytes zeros
		writeD(0x00);
		writeD(0x00);
		writeD(0x00);

		// TOS agreement (1 = accepted)
		writeD(1);

		// 25 bytes zeros
		writeB(new byte[25]);
	}
}
