package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
// Secure Area completely decommissioned
public class CM_SERVER_PVP_ACK extends AionClientPacket {

	public CM_SERVER_PVP_ACK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_SERVER_PVP_ACK(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		// No-op: Secure Area completely disabled
	}
}
