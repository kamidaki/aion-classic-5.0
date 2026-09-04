package com.aionemu.gameserver.network.aion.clientpackets;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.gameserver.dao.PlayerPasskeyDAO;

import com.aionemu.gameserver.model.account.CharacterPasskey;
import com.aionemu.gameserver.model.account.CharacterPasskey.ConnectType;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_2ND_PASSWORD;
import com.aionemu.gameserver.network.aion.serverpackets.S_DELETE_CHARACTER;
import com.aionemu.gameserver.network.loginserver.LoginServer;
import com.aionemu.gameserver.services.player.PlayerEnterWorldService;
import com.aionemu.gameserver.services.player.PlayerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

 

public class CM_CHARACTER_PASSKEY extends AionClientPacket
{
	private static final Logger log = LoggerFactory.getLogger(CM_CHARACTER_PASSKEY.class);

	private int type;
	private int unk;
	private String passkey;
	private String newPasskey;
	
	public CM_CHARACTER_PASSKEY(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}
	
	private static String toSha256Hex(byte[] data) {
		if (data == null) {
			return "";
		}
		try {
			MessageDigest md = MessageDigest.getInstance("SHA-256");
			byte[] hash = md.digest(data);
			StringBuilder sb = new StringBuilder(hash.length * 2);
			for (byte b : hash) {
				sb.append(String.format("%02x", b));
			}
			return sb.toString();
		} catch (NoSuchAlgorithmException e) {
			log.error("SHA-256 algorithm not available", e);
			return "";
		}
	}

	@Override
	protected void readImpl() {
		type = readC();
		unk = readC();
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
				DAOManager.getDAO(PlayerPasskeyDAO.class).insertPlayerPasskey(client.getAccount().getId(), passkey);
				log.info("[PASSKEY] Novo PIN cadastrado com sucesso para accountId=" + client.getAccount().getId());
				client.sendPacket(new S_2ND_PASSWORD(2, type, 0, chaPasskey.getWrongCount()));
			break;
			case 2:
				boolean isSuccess = DAOManager.getDAO(PlayerPasskeyDAO.class).updatePlayerPasskey(client.getAccount().getId(), passkey, newPasskey);
				chaPasskey.setIsPass(false);
				if (isSuccess) {
					chaPasskey.setWrongCount(0);
					log.info("[PASSKEY] PIN alterado com sucesso para accountId=" + client.getAccount().getId());
					client.sendPacket(new S_2ND_PASSWORD(2, type, 0, chaPasskey.getWrongCount()));
				} else {
					chaPasskey.setWrongCount(chaPasskey.getWrongCount() + 1);
					log.warn("[PASSKEY] Falha ao alterar PIN para accountId=" + client.getAccount().getId() + " (tentativa " + chaPasskey.getWrongCount() + ")");
					checkBlock(client.getAccount().getId(), chaPasskey.getWrongCount());
					client.sendPacket(new S_2ND_PASSWORD(2, type, 0, chaPasskey.getWrongCount()));
				}
			break;
			case 3:
				chaPasskey.setIsPass(true);
				chaPasskey.setWrongCount(0);
				log.info("[PASSKEY] Autenticacao automatica aceita para accountId=" + client.getAccount().getId() + " - enviando S_2ND_PASSWORD(2,3) para fechar HUD de selecao");
				client.sendPacket(new S_2ND_PASSWORD(2, 3, 0, 0));
				if (chaPasskey.getConnectType() == ConnectType.ENTER) {
					PlayerEnterWorldService.startEnterWorld(chaPasskey.getObjectId(), client);
				} else if (chaPasskey.getConnectType() == ConnectType.DELETE) {
					PlayerAccountData playerAccData = client.getAccount().getPlayerAccountData(chaPasskey.getObjectId());
					PlayerService.deletePlayer(playerAccData);
					client.sendPacket(new S_DELETE_CHARACTER(chaPasskey.getObjectId(), playerAccData.getDeletionTimeInSeconds()));
				}
			break;
		}
	}
	
	private void checkBlock(int accountId, int wrongCount) {
		if (wrongCount >= 5) {
			LoginServer.getInstance().sendBanPacket((byte) 2, accountId, "", 60 * 8, 0);
		}
	}
}