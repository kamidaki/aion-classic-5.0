package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Pacote de telemetria periódica e sincronização de estado enviado pelo cliente oficial 5.0 Classic.
 * Wire Opcode: 0x01E0 (dec=0x0112).
 * Payload típico: 1 byte (00).
 */
public class CM_CLIENT_TELEMETRY_SYNC extends AionClientPacket {

	private int syncFlag;

	public CM_CLIENT_TELEMETRY_SYNC(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_CLIENT_TELEMETRY_SYNC(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() > 0) {
			syncFlag = readC();
		}
	}

	@Override
	protected void runImpl() {
		// Absorve o pacote de sincronização silenciosamente para manter compatibilidade com o cliente oficial
	}
}
