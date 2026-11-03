package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

import java.util.Set;

/**
 * Client performance and telemetry metrics packet (decOp 0x00C5, wire 0x01BF in 5.0 Classic).
 * 21 bytes sent periodically by official client.
 */
public class CM_CLIENT_PERF_METRICS extends AionClientPacket {

	public CM_CLIENT_PERF_METRICS(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_CLIENT_PERF_METRICS(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		// Absorb telemetry gracefully
	}
}
