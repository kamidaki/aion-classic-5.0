package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client scene state acknowledgment (decOp 0x00CD, wire 0x01A7, len 0 in 5.0 Classic).
 */
public class CM_CLIENT_SCENE_ACK extends AionClientPacket {

	public CM_CLIENT_SCENE_ACK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		// Client scene acknowledgment
	}
}
