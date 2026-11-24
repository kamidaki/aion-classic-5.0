package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x14D (S_USER_STORY_BOOK_REGISTERED_ITEM_LIST_LOAD), itens registrados no Book of Legends, no login:
 * [D jogador][H n][n x (D jogador, D livro, D item, D quantidade)].
 * <p>
 * Capturas: 146 entradas em 7 livros (2342 b) e 5 entradas do livro 2 (86 b), todas com quantidade 1 (livros de fragmento).
 */
public class SM_STORYBOOK_REGISTERED_LIST extends AionServerPacket {

	public record Entry(int storybookId, int itemId, long count) {
	}

	private final int playerObjectId;
	private final List<Entry> entries;

	public SM_STORYBOOK_REGISTERED_LIST(int playerObjectId, List<Entry> entries) {
		this.playerObjectId = playerObjectId;
		this.entries = List.copyOf(entries);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjectId);
		writeH(entries.size());
		for (Entry entry : entries) {
			writeD(playerObjectId);
			writeD(entry.storybookId());
			writeD(entry.itemId());
			writeD((int) entry.count());
		}
	}
}
