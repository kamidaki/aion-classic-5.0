package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Resultado da identificação (0x171, C 0xDC) e da desmontagem (0x172, C 0xDD) de fragmentos do Book of Legends, entre os 0x1C dos fragmentos
 * gastos e os S_ADD_INVENTORY: [D 0][H n][n x (D item, Q quantidade)], somado por item na ordem em que saiu.
 * <p>
 * Capturas: 0x171 com 12 itens (150 b, 17 unidades de 17 fragmentos desconhecidos) e 0x172 com 3 itens (42 b, 7 fragmentos desmontados).
 */
public abstract class SM_STORYBOOK_ITEM_RESULT extends AionServerPacket {

	public record Result(int itemId, long count) {
	}

	private final List<Result> results;

	protected SM_STORYBOOK_ITEM_RESULT(List<Result> results) {
		this.results = List.copyOf(results);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(0);
		writeH(results.size());
		for (Result result : results) {
			writeD(result.itemId());
			writeQ(result.count());
		}
	}
}
