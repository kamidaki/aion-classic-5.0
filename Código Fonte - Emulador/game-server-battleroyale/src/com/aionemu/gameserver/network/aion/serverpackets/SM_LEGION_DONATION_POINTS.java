package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x157, pontos de produção da Legion no dia: [D pontos] (0 na criação, 1 a 10 nas produções do Kodra, 22/09).
 */
public class SM_LEGION_DONATION_POINTS extends AionServerPacket {

	private final int points;

	public SM_LEGION_DONATION_POINTS(int points) {
		this.points = points;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(points);
	}
}
