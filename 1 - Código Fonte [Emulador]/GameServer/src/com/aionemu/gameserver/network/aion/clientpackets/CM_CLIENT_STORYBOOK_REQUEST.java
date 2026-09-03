package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client story book / collection request packet (decOp 0x0122, wire 0x01D0, len 10 in 5.0 Classic).
 */
public class CM_CLIENT_STORYBOOK_REQUEST extends AionClientPacket {

	private byte[] payload;

	public CM_CLIENT_STORYBOOK_REQUEST(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		payload = readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		// Client storybook request
	}
}
