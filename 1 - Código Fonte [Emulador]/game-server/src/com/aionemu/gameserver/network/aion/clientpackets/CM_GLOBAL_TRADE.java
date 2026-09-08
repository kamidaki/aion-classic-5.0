package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

import java.util.Set;

/**
 * Client packet for Global Trade query (Opcode 0x0101, wire 0x01F3 in 5.0 Classic).
 */
public class CM_GLOBAL_TRADE extends AionClientPacket {

	private int queryType;
	private int param;

	public CM_GLOBAL_TRADE(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_GLOBAL_TRADE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 6) {
			queryType = readD();
			param = readH();
		} else {
			readB(getRemainingBytes());
		}
	}

	@Override
	protected void runImpl() {
	}
}
