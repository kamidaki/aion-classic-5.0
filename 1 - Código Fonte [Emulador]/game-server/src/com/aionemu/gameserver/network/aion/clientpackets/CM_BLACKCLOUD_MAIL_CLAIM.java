package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

import java.util.Set;

public class CM_BLACKCLOUD_MAIL_CLAIM extends AionClientPacket {

	public CM_BLACKCLOUD_MAIL_CLAIM(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_BLACKCLOUD_MAIL_CLAIM(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
	}
}
