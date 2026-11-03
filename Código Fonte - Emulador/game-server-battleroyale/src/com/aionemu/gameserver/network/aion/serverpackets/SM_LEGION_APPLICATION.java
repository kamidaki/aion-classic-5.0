package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x151, a candidatura do personagem: [D Legion][S nome da Legion], ou [D 0][S ""] sem candidatura. Vai no login de todos e responde à
 * candidatura (C 0x119) e ao cancelamento (C 0x11A) (Nova Pasta 2026-09-29 16:49).
 */
public class SM_LEGION_APPLICATION extends AionServerPacket {

	private final int legionId;
	private final String legionName;

	public SM_LEGION_APPLICATION(int legionId, String legionName) {
		this.legionId = legionId;
		this.legionName = legionName;
	}

	public SM_LEGION_APPLICATION() {
		this(0, "");
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(legionId);
		writeS(legionName);
	}
}
