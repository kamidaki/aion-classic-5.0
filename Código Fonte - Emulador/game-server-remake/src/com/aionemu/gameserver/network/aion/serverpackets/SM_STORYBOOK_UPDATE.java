package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x14E (S_USER_STORY_BOOK_UPDATE_RESULT), resposta ao registro no Book of Legends (C 0xE4), depois dos 0x1C/0x1D dos fragmentos gastos:
 * [D jogador][D livro][C 0][H n][n x (D livro, D item, D quantidade)], só com os itens registrados agora.
 * <p>
 * Capturas (3 de 3): livro 1 com 2 itens (35 b), livro 2 com 2 e livro 6 com 6 (83 b), todos de quantidade 1 e o byte sempre 0. O registro que
 * completa o livro não foi capturado, então o byte continua 0.
 */
public class SM_STORYBOOK_UPDATE extends AionServerPacket {

	public record Entry(int itemId, long count) {
	}

	private final int playerObjectId;
	private final int storybookId;
	private final List<Entry> entries;

	public SM_STORYBOOK_UPDATE(int playerObjectId, int storybookId, List<Entry> entries) {
		this.playerObjectId = playerObjectId;
		this.storybookId = storybookId;
		this.entries = List.copyOf(entries);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjectId);
		writeD(storybookId);
		writeC(0);
		writeH(entries.size());
		for (Entry entry : entries) {
			writeD(storybookId);
			writeD(entry.itemId());
			writeD((int) entry.count());
		}
	}
}
