package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x167, favorito de produção da Legion: [D receita][C marcado], a resposta ao C_GUILD 0x16 com os mesmos valores (Nova Pasta 2026-09-29
 * 16:14: receitas 1, 2 e 3 marcadas, 3 de 3).
 */
public class SM_LEGION_CRAFT_BOOKMARK extends AionServerPacket {

	private final int recipeId;
	private final boolean bookmarked;

	public SM_LEGION_CRAFT_BOOKMARK(int recipeId, boolean bookmarked) {
		this.recipeId = recipeId;
		this.bookmarked = bookmarked;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeC(bookmarked ? 1 : 0);
	}
}
