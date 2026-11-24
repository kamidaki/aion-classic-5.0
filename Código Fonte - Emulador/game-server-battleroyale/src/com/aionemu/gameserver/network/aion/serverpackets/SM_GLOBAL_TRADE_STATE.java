package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_GLOBAL_TRADE_STATE (0x144), resposta do C 0x10C ao abrir a janela: [D 0][Q 1.000.000.000] nas 4 capturas (o limite semanal de kinah de
 * STR_MSG_WORLD_VENDOR_GOLD_EXCESS e do "Registerable Kinah (%0/1 billion)").
 */
public class SM_GLOBAL_TRADE_STATE extends AionServerPacket {

	private final long kinahLimit;

	public SM_GLOBAL_TRADE_STATE(long kinahLimit) {
		this.kinahLimit = kinahLimit;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(0);
		writeQ(kinahLimit);
	}
}
