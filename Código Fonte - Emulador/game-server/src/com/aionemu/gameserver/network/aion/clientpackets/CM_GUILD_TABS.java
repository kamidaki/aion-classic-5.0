package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

import java.util.Set;

public class CM_GUILD_TABS extends AionClientPacket {

	public CM_GUILD_TABS(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_GUILD_TABS(int opcode, Set<State> validStates) {
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
