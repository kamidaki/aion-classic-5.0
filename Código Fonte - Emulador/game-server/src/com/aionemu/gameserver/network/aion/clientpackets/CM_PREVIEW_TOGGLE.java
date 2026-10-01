package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Notificação de alternância de modo/câmera de visualização prévia (Aion Look / Preview toggle).
 * Opcode decodificado: 275 (0x0113), no fio 0x01E1 (1 byte).
 */
public class CM_PREVIEW_TOGGLE extends AionClientPacket {

	private int mode;

	public CM_PREVIEW_TOGGLE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() > 0) {
			mode = readC();
		}
	}

	@Override
	protected void runImpl() {
		// Notificação de alternância recebida com sucesso
	}
}
