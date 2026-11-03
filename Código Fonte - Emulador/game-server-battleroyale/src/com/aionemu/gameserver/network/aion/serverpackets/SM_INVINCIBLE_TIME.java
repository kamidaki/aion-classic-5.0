package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Server packet for invincible time (Opcode 0x00FE / 254 in 5.0 Classic).
 */
public class SM_INVINCIBLE_TIME extends AionServerPacket {

	private int time;

	public SM_INVINCIBLE_TIME(int time) {
		this.time = time;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(time);
	}
}
