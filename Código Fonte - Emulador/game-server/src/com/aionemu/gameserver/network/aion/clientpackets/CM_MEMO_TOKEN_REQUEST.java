package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MEMO_TOKEN;

/**
 * Pedido de token de escrita do bloco de notas (MemoPad) no Classic 5.0.
 * Opcode decodificado: 288 (0x0120), no fio 0x01D2 (0 bytes).
 */
public class CM_MEMO_TOKEN_REQUEST extends AionClientPacket {

	public CM_MEMO_TOKEN_REQUEST(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		// Sem payload
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null) {
			sendPacket(new SM_MEMO_TOKEN());
		}
	}
}
