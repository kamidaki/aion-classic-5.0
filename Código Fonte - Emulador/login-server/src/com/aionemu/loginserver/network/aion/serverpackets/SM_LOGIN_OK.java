package com.aionemu.loginserver.network.aion.serverpackets;

import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.LoginConnection;
import com.aionemu.loginserver.network.aion.SessionKey;

/**
 * @author Lost Academy Team & Durak
 */
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

	@Override
	protected void writeImpl(LoginConnection con) {
		writeD(accountId);
		writeD(loginOk);
		writeD(0x00);
		writeD(0x00);

		// Account active flags (4x 0x0000003F, 4th must not have bit 0x10 set to prevent PC room notice)
		writeD(0x0000003F);
		writeD(0x0000003F);
		writeD(0x0000003F);
		writeD(0x00000000);

		// Classic Signature (0xFF 0xFE 0x00 0x00)
		writeC(0xFF);
		writeC(0xFE);
		writeC(0x00);
		writeC(0x00);

		// 12 bytes zeros
		writeD(0x00);
		writeD(0x00);
		writeD(0x00);

		// PC room complaint / TOS flag (0 = normal login, 1 = STR_BLOCK_PC_ROOM_COMPLAIN)
		writeD(0);

		// 25 bytes zeros
		writeB(new byte[25]);
	}
}
