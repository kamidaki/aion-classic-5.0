package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SP (energia do Revenant) do próprio jogador. 5.0 oficial: 0x14B, 2 b, sai no tick de ~1 s seguinte à mudança e só quando o valor muda.
 */
public class SM_SP_UPDATE extends AionServerPacket {

	private final int sp;

	public SM_SP_UPDATE(int sp) {
		this.sp = sp;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(sp);
	}
}
