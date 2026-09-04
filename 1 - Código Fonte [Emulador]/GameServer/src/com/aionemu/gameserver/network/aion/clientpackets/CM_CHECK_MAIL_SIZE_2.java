package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/****/
/**
 * Author Rinzler (Encom) /
 ****/

public class CM_CHECK_MAIL_SIZE_2 extends AionClientPacket {

	public CM_CHECK_MAIL_SIZE_2(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		player.getMailbox().sendMailList(false);
	}
}
