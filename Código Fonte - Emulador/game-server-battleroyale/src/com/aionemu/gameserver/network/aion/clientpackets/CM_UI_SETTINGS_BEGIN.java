package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * C 0x0C (cru 0xE6) do 5.0: sempre vazio, logo antes dos dois C 0x1A (CM_UI_SETTINGS) com que o cliente salva a interface ao sair ou trocar de
 * personagem. Nas capturas oficiais aparece 23 vezes e nunca tem resposta, então não há o que fazer. Antes ele caía no CM_CUSTOM_SETTINGS da 4.x
 * e zerava o esconder capacete/capa.
 */
public class CM_UI_SETTINGS_BEGIN extends AionClientPacket {

	public CM_UI_SETTINGS_BEGIN(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
	}

	@Override
	protected void runImpl() {
	}
}
