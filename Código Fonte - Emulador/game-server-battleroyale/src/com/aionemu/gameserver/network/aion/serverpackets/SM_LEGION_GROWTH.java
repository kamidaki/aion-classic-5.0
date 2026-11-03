package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x164, crescimento da Legion: [D nível][D exp][D 0] (Lost Academy 22/09: 1 e 3000 depois da primeira recompensa de missão).
 */
public class SM_LEGION_GROWTH extends AionServerPacket {

	private final int level;
	private final int exp;

	public SM_LEGION_GROWTH(int level, int exp) {
		this.level = level;
		this.exp = exp;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(level);
		writeD(exp);
		writeD(0);
	}
}
