package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.model.account.PlayerAccountData;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ACCOUNT_PROPERTIES;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CHARACTER_LIST;
import com.aionemu.gameserver.services.player.PlayerService;

/**
 * In this packet aion client is requesting character list.
 */
public class CM_CHARACTER_LIST extends AionClientPacket {

	private int playOk2;

	public CM_CHARACTER_LIST(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		playOk2 = readD();
	}

	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(CM_CHARACTER_LIST.class);

	@Override
	protected void runImpl() {
		// INFO: e o que mostra se o cliente voltou a pedir a lista depois da tela de edicao
		log.info("[CHARACTER_LIST] Pedido da conta {}", getConnection().getAccount() != null ? getConnection().getAccount().getId() : "null");
		boolean isGM = getConnection().getAccount() != null && getConnection().getAccount().getAccessLevel() >= AdminConfig.GM_PANEL;
		sendPacket(new SM_ACCOUNT_PROPERTIES(isGM));
		if (getConnection().getAccount() != null)
			SM_CHARACTER_LIST.of(getConnection().getAccount(), playOk2).forEach(this::sendPacket);
		if (getConnection().getAccount() != null) {
			for (PlayerAccountData pad : getConnection().getAccount()) {
				if (pad.getDeletionDate() != null && pad.getDeletionDate().getTime() > System.currentTimeMillis()) {
					PlayerService.scheduleCharacterDeletion(getConnection(), pad.getPlayerCommonData().getPlayerObjId(), pad.getDeletionDate().getTime());
				}
			}
		}
	}
}

