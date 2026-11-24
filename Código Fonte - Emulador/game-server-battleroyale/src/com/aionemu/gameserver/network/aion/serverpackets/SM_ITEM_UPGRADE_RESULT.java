package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x1AE (S_ITEM_UPGRADE_RESULT), resultado do Ascend, antes do S_ADD_INVENTORY do item novo. Captura (1 de 1, 22 b):
 * [D 1070][H 1][D 123001182][Q 1][D objeto novo]. Escrito como [D receita][H itens][itens x (D item, Q quantidade, D objeto)]; só a faixa UP
 * foi capturada, então a FAIL sai no mesmo formato, com o item que volta.
 */
public class SM_ITEM_UPGRADE_RESULT extends AionServerPacket {

	public record Result(int itemId, long count, int objectId) {
	}

	private final int recipeId;
	private final List<Result> results;

	public SM_ITEM_UPGRADE_RESULT(int recipeId, List<Result> results) {
		this.recipeId = recipeId;
		this.results = List.copyOf(results);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeH(results.size());
		for (Result result : results) {
			writeD(result.itemId());
			writeQ(result.count());
			writeD(result.objectId());
		}
	}
}
