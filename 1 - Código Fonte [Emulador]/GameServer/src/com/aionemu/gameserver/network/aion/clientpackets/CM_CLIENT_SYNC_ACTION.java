package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client sync action packet (decOp 0x0002, wire 0x00F0, len 1 in 5.0 Classic).
 */
public class CM_CLIENT_SYNC_ACTION extends AionClientPacket {

	private int actionType;

	public CM_CLIENT_SYNC_ACTION(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 1) {
			actionType = readC();
		} else {
			readB(getRemainingBytes());
		}
	}

	@Override
	protected void runImpl() {
		// Client action sync
	}
}
