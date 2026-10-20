package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_RANKING_BADGE (S 0x138) [D 0][C mostrar]: a opção "mostrar ranking badge" das configurações do jogo, para o próprio jogador. Vai no login
 * com o valor salvo (1 em quem nunca mexeu) e em resposta ao C 0xC8 (captura 06_Sistemas_Novos 2026-10-20 02:17: 0 e depois 1).
 */
public class SM_RANKING_BADGE extends AionServerPacket {

	private final boolean shown;

	public SM_RANKING_BADGE(boolean shown) {
		this.shown = shown;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(0);
		writeC(shown ? 1 : 0);
	}
}
