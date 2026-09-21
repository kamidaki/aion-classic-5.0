package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_COLLECT (0x142), depois de receber as vendas: [C 0][D vendas recebidas] (1 de 1 na captura).
 */
public class SM_GLOBAL_TRADE_COLLECT extends AionServerPacket {

	private final int collected;

	public SM_GLOBAL_TRADE_COLLECT(int collected) {
		this.collected = collected;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0);
		writeD(collected);
	}
}
