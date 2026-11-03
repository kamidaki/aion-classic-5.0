package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Server packet for tutorial hints (Opcode 0x000D in 5.0 Classic).
 */
public class SM_TUTORIAL_HINT extends AionServerPacket {

	private int type;
	private int param;

	public SM_TUTORIAL_HINT() {
		this(0, 0);
	}

	public SM_TUTORIAL_HINT(int type, int param) {
		this.type = type;
		this.param = param;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(type);
		writeC(param);
	}
}
