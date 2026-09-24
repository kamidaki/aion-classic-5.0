package com.aionemu.loginserver.network.aion.serverpackets;

import javax.crypto.SecretKey;

import com.aionemu.loginserver.network.aion.AionServerPacket;
import com.aionemu.loginserver.network.aion.LoginConnection;

public final class SM_INIT extends AionServerPacket {

	/**
	 * Session Id of this connection
	 */
	private final int sessionId;

	/**
	 * public Rsa key that client will use to encrypt login and password that will be send in RequestAuthLogin client packet.
	 */
	private final byte[] publicRsaKey;
	/**
	 * blowfish key for packet encryption/decryption.
	 */
	private final byte[] blowfishKey;

	public SM_INIT(LoginConnection client, SecretKey blowfishKey) {
		this(client.getEncryptedModulus(), blowfishKey.getEncoded(), client.getSessionId());
	}

	private SM_INIT(byte[] publicRsaKey, byte[] blowfishKey, int sessionId) {
		super(0x00);
		this.sessionId = sessionId;
		this.publicRsaKey = publicRsaKey;
		this.blowfishKey = blowfishKey;
	}

	@Override
	protected void writeImpl(LoginConnection con) {
		writeD(sessionId); // session id
		writeD(0x0000c621); // protocol revision
		writeB(publicRsaKey); // RSA Public Key
		// unk
		writeD(0x00);
		writeD(0x00);
		writeD(0x00);
		writeD(0x00);

		writeB(blowfishKey); // BlowFish key

		// Aion Classic 5.0 version tags & flag
		writeC(0x03);
		writeC(0x05);
		writeC(0x00);
		writeC(0x00);
		writeC(0x03);
		writeC(0x05);
		writeC(0x00);
		writeC(0x00);
	}
}
