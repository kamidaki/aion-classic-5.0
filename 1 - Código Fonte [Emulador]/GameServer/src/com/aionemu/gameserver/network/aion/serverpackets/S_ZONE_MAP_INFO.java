package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Server packet for zone map information (Opcode 0x005F in 5.0 Classic).
 */
public class S_ZONE_MAP_INFO extends AionServerPacket {

	private byte[] data;

	public S_ZONE_MAP_INFO() {
		this(new byte[134]);
	}

	public S_ZONE_MAP_INFO(byte[] data) {
		this.data = data;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (data != null) {
			writeB(data);
		} else {
			writeB(new byte[134]);
		}
	}
}
