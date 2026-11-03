package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x14C (S_USER_STORY_BOOK_FINISHED_LIST_LOAD), livros completos do Book of Legends, no login antes do 0x14D: [D jogador][H n] e n entradas.
 * <p>
 * As 54 amostras das capturas oficiais têm n = 0: nenhum personagem capturado completou um livro, então o formato da entrada não é conhecido e o
 * pacote sai sempre vazio. O livro completo continua valendo no servidor (recompensa aplicada, registro recusado com STR_MSG_STORYBOOK_ALREADY_FINISH).
 */
public class SM_STORYBOOK_FINISHED_LIST extends AionServerPacket {

	private final int playerObjectId;

	public SM_STORYBOOK_FINISHED_LIST(int playerObjectId) {
		this.playerObjectId = playerObjectId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjectId);
		writeH(0);
	}
}
