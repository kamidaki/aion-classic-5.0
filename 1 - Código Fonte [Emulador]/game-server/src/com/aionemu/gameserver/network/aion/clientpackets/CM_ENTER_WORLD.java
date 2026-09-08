package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.configs.main.SecurityConfig;
import com.aionemu.gameserver.dao.PlayerPasskeyDAO;
import com.aionemu.gameserver.model.account.Account;
import com.aionemu.gameserver.model.account.CharacterPasskey;
import com.aionemu.gameserver.model.account.CharacterPasskey.ConnectType;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CHARACTER_SELECT;
import com.aionemu.gameserver.services.player.PlayerEnterWorldService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_ENTER_WORLD extends AionClientPacket {

	/**
	 * Object Id of player that is entering world
	 */
	private int objectId;

	public CM_ENTER_WORLD(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		objectId = readD();
	}

	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(CM_ENTER_WORLD.class);

	@Override
	protected void runImpl() {
		final AionConnection client = getConnection();
		if (client.getAccount() == null) {
			return;
		}
		CharacterPasskey chaPasskey = client.getAccount().getCharacterPasskey();
		chaPasskey.setObjectId(objectId);
		chaPasskey.setConnectType(ConnectType.ENTER);

		if (!SecurityConfig.PASSKEY_ENABLE) {
			chaPasskey.setIsPass(true);
			chaPasskey.setWrongCount(0);
			log.debug("[PASSKEY_BYPASS] PIN desativado. Enviando SM_CHARACTER_SELECT(2,3) e entrando no mundo para objectId={}", objectId);
			client.sendPacket(new SM_CHARACTER_SELECT(2, (short) 3, 0));
			PlayerEnterWorldService.startEnterWorld(objectId, client);
		} else {
			client.sendPacket(new SM_CHARACTER_SELECT(1));
		}
	}
}
