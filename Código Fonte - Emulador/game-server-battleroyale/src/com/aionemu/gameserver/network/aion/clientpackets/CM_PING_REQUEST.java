package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_PING_RESPONSE;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_PING_REQUEST extends AionClientPacket {

	/**
	 * Constructs new instance of <tt>CM_PING_REQUEST </tt> packet
	 * 
	 * @param opcode
	 */
	public CM_PING_REQUEST(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		// empty
	}

	@Override
	protected void runImpl() {
		// O oficial responde cada C 0x6F com S_PING (0x7F) [C 4] (captura 05_Combate_Skills_Asmodians de 2026-09-14)
		sendPacket(new SM_PING_RESPONSE());
	}
}
