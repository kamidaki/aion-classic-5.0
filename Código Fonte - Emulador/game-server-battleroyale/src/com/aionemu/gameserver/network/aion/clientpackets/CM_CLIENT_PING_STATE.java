package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

import java.util.Set;

/**
 * Client packet for client state update / heartbeat (decOp 0x0150, wire 0x0222 in 5.0 Classic).
 */
public class CM_CLIENT_PING_STATE extends AionClientPacket {

	private byte stateType;
	private int value;

	public CM_CLIENT_PING_STATE(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_CLIENT_PING_STATE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 5) {
			stateType = (byte) readC();
			value = readD();
		} else {
			readB(getRemainingBytes());
		}
	}

	@Override
	protected void runImpl() {
		// Keep-alive state acknowledgment
	}
}
