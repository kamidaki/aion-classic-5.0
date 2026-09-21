package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.lostacademy.lostsocket.secure.SecureAreaService;

/**
 * Botão Secure Area / FFA do cliente Aion Classic 5.0.
 * Wire opcode: 0x03DC — decoded index: 806 (0x326).
 * Enviado quando o jogador clica no botão de alternar modo FFA.
 */
public class CM_SERVER_PVP_ACK extends AionClientPacket {

	public CM_SERVER_PVP_ACK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_SERVER_PVP_ACK(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes()); // consume remaining bytes (len 7 → 2 bytes payload after header)
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;
		SecureAreaService.getInstance().requestToggle(player);
	}
}
