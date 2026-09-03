package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client packet for Server PVP acknowledgment (decOp 0x0326, wire 0x03DC, len 7 in 5.0 Classic).
 */
public class CM_SERVER_PVP_ACK extends AionClientPacket {

	public CM_SERVER_PVP_ACK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		// PVP acknowledgment from client
	}
}
