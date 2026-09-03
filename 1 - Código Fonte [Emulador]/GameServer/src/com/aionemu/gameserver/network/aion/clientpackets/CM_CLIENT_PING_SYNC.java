package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client ping sync packet (decOp 0x00A3, wire 0x0151, len 1 in 5.0 Classic).
 */
public class CM_CLIENT_PING_SYNC extends AionClientPacket {

	private int pingCode;

	public CM_CLIENT_PING_SYNC(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 1) {
			pingCode = readC();
		} else {
			readB(getRemainingBytes());
		}
	}

	@Override
	protected void runImpl() {
		// Client ping sync acknowledgment
	}
}
