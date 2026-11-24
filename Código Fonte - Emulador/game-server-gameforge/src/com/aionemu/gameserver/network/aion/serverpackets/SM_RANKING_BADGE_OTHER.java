package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_RANKING_BADGE_OTHER (S 0x139) [D objeto][D 0][C mostrar]: a opção "mostrar ranking badge" de um jogador, para quem o vê. Na captura
 * 06_Sistemas_Novos 2026-10-20 02:17 vai logo depois do S 0x138, e o próprio jogador também recebe.
 */
public class SM_RANKING_BADGE_OTHER extends AionServerPacket {

	private final int objectId;
	private final boolean shown;

	public SM_RANKING_BADGE_OTHER(int objectId, boolean shown) {
		this.objectId = objectId;
		this.shown = shown;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeD(0);
		writeC(shown ? 1 : 0);
	}
}
