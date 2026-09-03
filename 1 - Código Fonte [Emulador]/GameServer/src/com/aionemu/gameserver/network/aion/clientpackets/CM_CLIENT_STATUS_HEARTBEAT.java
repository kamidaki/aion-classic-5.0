package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client status heartbeat / ping packet (decOp 0x0225, wire 0x02DF, len 1 in 5.0 Classic).
 */
public class CM_CLIENT_STATUS_HEARTBEAT extends AionClientPacket {

	private int statusByte;

	public CM_CLIENT_STATUS_HEARTBEAT(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 1) {
			statusByte = readC();
		} else {
			readB(getRemainingBytes());
		}
	}

	@Override
	protected void runImpl() {
		// Client status heartbeat ACK
	}
}
