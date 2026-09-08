package com.aionemu.loginserver.network.aion.clientpackets;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.sql.Timestamp;

import javax.crypto.Cipher;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.loginserver.configs.Config;
import com.aionemu.loginserver.controller.AccountController;
import com.aionemu.loginserver.controller.BannedIpController;
import com.aionemu.loginserver.network.aion.AionAuthResponse;
import com.aionemu.loginserver.network.aion.AionClientPacket;
import com.aionemu.loginserver.network.aion.LoginConnection;
import com.aionemu.loginserver.network.aion.LoginConnection.State;
import com.aionemu.loginserver.network.aion.SessionKey;
import com.aionemu.loginserver.network.aion.serverpackets.SM_LOGIN_FAIL;
import com.aionemu.loginserver.network.aion.serverpackets.SM_LOGIN_OK;
import com.aionemu.loginserver.utils.BruteForceProtector;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_LOGIN extends AionClientPacket {

	private static final Logger log = LoggerFactory.getLogger(CM_LOGIN.class);

	private byte[] data;
	private int sessionId;

	public CM_LOGIN(ByteBuffer buf, LoginConnection client, int opCode) {
		super(buf, client, opCode);
	}

	@Override
	protected void readImpl() {
		sessionId = readD();

		if (getRemainingBytes() >= 128) {
			data = readB(128);
		}
	}

	@Override
	protected void runImpl() {
		if (data == null) {
			return;
		}

		byte[] decrypted;
		try {
			Cipher rsaCipher = Cipher.getInstance("RSA/ECB/nopadding");
			rsaCipher.init(Cipher.DECRYPT_MODE, getConnection().getRSAPrivateKey());
			decrypted = rsaCipher.doFinal(data, 0, 128);
		} catch (GeneralSecurityException e) {
			log.error("RSA decryption failed for client login", e);
			sendPacket(new SM_LOGIN_FAIL(AionAuthResponse.STR_L2AUTH_S_SYSTEM_ERROR));
			return;
		}

		// Decrypted 128 bytes:
		// 0..63: padding
		// 64..95: username (up to 32 bytes, zero-terminated)
		// 96..127: password (up to 32 bytes, zero-terminated)
		int userLen = 0;
		while (userLen < 32 && decrypted[64 + userLen] != 0) {
			userLen++;
		}
		String user = new String(decrypted, 64, userLen, StandardCharsets.UTF_8).trim().toLowerCase();

		int passLen = 0;
		while (passLen < 32 && decrypted[96 + passLen] != 0) {
			passLen++;
		}
		String password = new String(decrypted, 96, passLen, StandardCharsets.UTF_8).trim();

		@SuppressWarnings("unused")
		int ncotp = decrypted[0x7c] & 0xFF;
		ncotp |= (decrypted[0x7d] & 0xFF) << 8;
		ncotp |= (decrypted[0x7e] & 0xFF) << 16;
		ncotp |= (decrypted[0x7f] & 0xFF) << 24;

		LoginConnection client = getConnection();
		AionAuthResponse response = AccountController.login(user, password, client);
		if (response == null) {
			return;
		}

		switch (response) {
			case STR_L2AUTH_S_ALL_OK:
				client.setState(State.AUTHED_LOGIN);
				client.setSessionKey(new SessionKey(client.getAccount()));
				client.sendPacket(new SM_LOGIN_OK(client.getSessionKey()));
				log.info("{} got authed state", user);
				break;
			case STR_L2AUTH_S_INVALID_ACCOUT:
			case STR_L2AUTH_S_INCORRECT_PWD:
				if (Config.ENABLE_BRUTEFORCE_PROTECTION) {
					String ip = client.getIP();
					if (!ip.equals("127.0.0.1") && BruteForceProtector.getInstance().addFailedConnect(ip)) {
						Timestamp newTime = new Timestamp(System.currentTimeMillis() + Config.WRONG_LOGIN_BAN_TIME * 60000);
						BannedIpController.banIp(ip, newTime);
						log.info("{} on {} banned for {} min. bruteforce", user, ip, Config.WRONG_LOGIN_BAN_TIME);
						client.close(new SM_LOGIN_FAIL(AionAuthResponse.STR_L2AUTH_S_BLOCKED_IP));
						break;
					}
				}
				log.info("{} got failed login response ({})", user, response);
				client.sendPacket(new SM_LOGIN_FAIL(response));
				break;
			default:
				log.info("{} got failed login response ({})", user, response);
				client.sendPacket(new SM_LOGIN_FAIL(response));
				break;
		}
	}
}
