package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * NetPasskey / Blackcloud shop goods count packet.
 * Opcode: 266 (0x10A)
 */
public class SM_NPSHOP_GOODS_COUNT extends AionServerPacket {

	private final int count;

	public SM_NPSHOP_GOODS_COUNT(int count) {
		this.count = count;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(this.count);
	}
}
