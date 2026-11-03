package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

import java.util.Set;

/**
 * Client motion / posture state acknowledgment (decOp 0x00F3, wire 0x0181, len 5 in 5.0 Classic).
 */
public class CM_CLIENT_MOTION_ACK extends AionClientPacket {

	private byte motionType;
	private int value;

	public CM_CLIENT_MOTION_ACK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_CLIENT_MOTION_ACK(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 5) {
			motionType = (byte) readC();
			value = readD();
		} else {
			readB(getRemainingBytes());
		}
	}

	@Override
	protected void runImpl() {
		// Client motion acknowledgment
	}
}
