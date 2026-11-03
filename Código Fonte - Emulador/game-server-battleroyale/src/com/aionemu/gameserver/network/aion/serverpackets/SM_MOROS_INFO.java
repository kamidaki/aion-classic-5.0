package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x169, estado do Moreth, Chronicle of Time: [H nível][D pontos no nível][D 0][H registros disponíveis]. Sai no login, depois do 0x14D, a cada
 * gravação (C 0x111) e quando um registro volta.
 * <p>
 * Capturas (40 de 40, 11/09 a 21/09): nível 1 com 1281 pontos e 20 registros; depois de gravar um capacete, 1283 e 19; 30 min depois, 20 de
 * novo. Nível 2 com 1390, 2990 e 3257 pontos. O terceiro campo nunca saiu de 0.
 */
public class SM_MOROS_INFO extends AionServerPacket {

	private final int level;
	private final long points;
	private final int records;

	public SM_MOROS_INFO(int level, long points, int records) {
		this.level = level;
		this.points = points;
		this.records = records;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(level);
		writeD((int) points);
		writeD(0);
		writeH(records);
	}
}
