package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client world event acknowledgment (decOp 0x010E, wire 0x01E4, len 0 in 5.0 Classic).
 */
public class CM_CLIENT_WORLD_EVENT_ACK extends AionClientPacket {

	public CM_CLIENT_WORLD_EVENT_ACK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		// World event acknowledgment
	}
}
