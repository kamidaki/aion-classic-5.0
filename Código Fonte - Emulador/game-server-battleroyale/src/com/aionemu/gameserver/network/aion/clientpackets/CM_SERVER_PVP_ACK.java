package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.lostacademy.lostsocket.secure.SecureAreaService;

/**
 * Pacote disparado quando o jogador clica no botão com espadas cruzadas do console de Altar / Secure Area.
 * Opcode wire: 0x03DC (decodificado: 806 / 0x0326).
 *
 * @author Lost Academy Team & Durak
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
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null) {
			SecureAreaService.getInstance().requestToggle(player);
		}
	}
}
