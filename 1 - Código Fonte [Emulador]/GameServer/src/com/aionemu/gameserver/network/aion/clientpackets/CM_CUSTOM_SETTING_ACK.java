package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Client setting acknowledgment (decOp 0xFFFC wire 0x00F6 / decOp 0xFFFD wire 0x00F7 in 5.0 Classic).
 */
public class CM_CUSTOM_SETTING_ACK extends AionClientPacket {

	private int settingId;

	public CM_CUSTOM_SETTING_ACK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 4) {
			settingId = readD();
		} else {
			readB(getRemainingBytes());
		}
	}

	@Override
	protected void runImpl() {
		// Acknowledged client custom setting
	}
}
