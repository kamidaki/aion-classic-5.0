package com.aionemu.gameserver.network.aion.clientpackets;

import java.nio.charset.StandardCharsets;
import java.util.Set;

import com.aionemu.gameserver.configs.main.SecurityConfig;
import com.aionemu.gameserver.dao.PlayerPasskeyDAO;
import com.aionemu.gameserver.model.account.CharacterPasskey;
import com.aionemu.gameserver.model.account.CharacterPasskey.ConnectType;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CHARACTER_SELECT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DELETE_CHARACTER;
import com.aionemu.gameserver.network.loginserver.LoginServer;
import com.aionemu.gameserver.services.player.PlayerEnterWorldService;
import com.aionemu.gameserver.services.player.PlayerService;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_CHARACTER_PASSKEY extends AionClientPacket {

	private static final Logger log = LoggerFactory.getLogger(CM_CHARACTER_PASSKEY.class);

	private short type;
	private String passkey;
	private String newPasskey;

	public CM_CHARACTER_PASSKEY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	private static String toSha256Hex(byte[] data) {
		if (data == null) {
			return "";
		}
		try {
			java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-256");
			byte[] hash = md.digest(data);
			StringBuilder sb = new StringBuilder(hash.length * 2);
			for (byte b : hash) {
				sb.append(String.format("%02x", b));
			}
			return sb.toString();
		} catch (java.security.NoSuchAlgorithmException e) {
			log.error("SHA-256 algorithm not available", e);
			return "";
		}
	}

	@Override
	protected void readImpl() {
		type = (short) readC();
		int unk = readC();
		try {
			byte[] passkeyBytes = readB(48);
			passkey = toSha256Hex(passkeyBytes);
			if (type == 2) {
				byte[] newPasskeyBytes = readB(48);
				newPasskey = toSha256Hex(newPasskeyBytes);
			}
		} catch (Exception e) {
			log.error("Error reading CM_CHARACTER_PASSKEY", e);
		}
	}

	@Override
	protected void runImpl() {
		AionConnection client = getConnection();
		CharacterPasskey chaPasskey = client.getAccount().getCharacterPasskey();

		switch (type) {
			case 0:
				chaPasskey.setIsPass(false);
				chaPasskey.setWrongCount(0);
				PlayerPasskeyDAO.insertPlayerPasskey(client.getAccount().getId(), passkey);
				client.sendPacket(new SM_CHARACTER_SELECT(2, type, chaPasskey.getWrongCount()));
				break;
			case 2:
				boolean isSuccess = PlayerPasskeyDAO.updatePlayerPasskey(client.getAccount().getId(), passkey, newPasskey);

				chaPasskey.setIsPass(false);
				if (isSuccess) {
					chaPasskey.setWrongCount(0);
					client.sendPacket(new SM_CHARACTER_SELECT(2, type, chaPasskey.getWrongCount()));
				} else {
					chaPasskey.setWrongCount(chaPasskey.getWrongCount() + 1);
					checkBlock(client.getAccount().getId(), chaPasskey.getWrongCount());
					client.sendPacket(new SM_CHARACTER_SELECT(2, type, chaPasskey.getWrongCount()));
				}
				break;
			case 3:
				boolean isPass = !SecurityConfig.PASSKEY_ENABLE || PlayerPasskeyDAO.checkPlayerPasskey(client.getAccount().getId(), passkey);

				if (isPass) {
					chaPasskey.setIsPass(true);
					chaPasskey.setWrongCount(0);
					log.debug("[PASSKEY] Autenticacao aceita para accountId={} - enviando SM_CHARACTER_SELECT(2,3) para fechar HUD de selecao", client.getAccount().getId());
					client.sendPacket(new SM_CHARACTER_SELECT(2, (short) 3, 0));

					if (chaPasskey.getConnectType() == ConnectType.ENTER)
						PlayerEnterWorldService.startEnterWorld(chaPasskey.getObjectId(), client);
					else if (chaPasskey.getConnectType() == ConnectType.DELETE) {
						PlayerAccountData playerAccData = client.getAccount().getPlayerAccountData(chaPasskey.getObjectId());
						if (playerAccData != null) {
							boolean isDeleted = PlayerService.deletePlayer(playerAccData);
							if (isDeleted) {
								client.getAccount().removePlayerAccountData(chaPasskey.getObjectId());
								client.sendPacket(new SM_DELETE_CHARACTER(chaPasskey.getObjectId(), 0));
							} else {
								client.sendPacket(new SM_DELETE_CHARACTER(chaPasskey.getObjectId(), playerAccData.getDeletionTimeInSeconds()));
							}
						}
					}
				} else {
					chaPasskey.setIsPass(false);
					chaPasskey.setWrongCount(chaPasskey.getWrongCount() + 1);
					log.warn("[PASSKEY] Falha na autenticacao para accountId={} (tentativa {})", client.getAccount().getId(), chaPasskey.getWrongCount());
					checkBlock(client.getAccount().getId(), chaPasskey.getWrongCount());
					client.sendPacket(new SM_CHARACTER_SELECT(2, type, chaPasskey.getWrongCount()));
				}
				break;
		}
	}

	/**
	 * @param accountId
	 * @param wrongCount
	 */
	private void checkBlock(int accountId, int wrongCount) {
		if (wrongCount >= SecurityConfig.PASSKEY_WRONG_MAXCOUNT) {
			// TODO : Change the account to be blocked
			LoginServer.getInstance().sendBanPacket((byte) 2, accountId, "", 60 * 8, 0);
		}
	}
}
