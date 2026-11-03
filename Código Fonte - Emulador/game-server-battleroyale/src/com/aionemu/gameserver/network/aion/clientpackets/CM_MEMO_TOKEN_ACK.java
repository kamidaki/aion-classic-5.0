package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Confirmação do token do bloco de notas (MemoPad) no Classic 5.0.
 * Opcode decodificado: 289 (0x0121), no fio 0x01D3 (22 a 24 bytes).
 */
public class CM_MEMO_TOKEN_ACK extends AionClientPacket {

	private int length;
	private byte[] tokenData;

	public CM_MEMO_TOKEN_ACK(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		length = readD();
		if (getRemainingBytes() > 0) {
			tokenData = readB(Math.min(length, getRemainingBytes()));
		}
	}

	@Override
	protected void runImpl() {
		// Handshake do MemoPad concluído com sucesso
	}
}
