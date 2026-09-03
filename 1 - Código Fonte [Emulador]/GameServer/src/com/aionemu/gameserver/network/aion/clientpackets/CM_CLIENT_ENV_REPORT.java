package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client environment / system report packet (decOp 0x00B5, wire 0x014F, len 20 in 5.0 Classic).
 */
public class CM_CLIENT_ENV_REPORT extends AionClientPacket {

	private byte[] data;

	public CM_CLIENT_ENV_REPORT(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		data = readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		// Client environment telemetry
	}
}
