package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

import java.util.Set;

public class CM_AUTH_SUCCESS extends AionClientPacket {

	public CM_AUTH_SUCCESS(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_AUTH_SUCCESS(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readD();
	}

	@Override
	protected void runImpl() {
	}
}
