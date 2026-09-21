package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x1A7, resultado da fusão no Altar of Transcendence. Captura (2 de 2, quantidade 1): [D receita][H 1][H 1][D item][D 1][D 0], antes do
 * S_ADD_INVENTORY do item. Escrito como [D receita][H quantidade][H itens][itens x (D item, Q quantidade)]; com mais de uma fusão por
 * pedido o layout não foi capturado.
 */
public class SM_ITEM_COMPOSE_RESULT extends AionServerPacket {

	public record Reward(int itemId, long count) {
	}

	private final int recipeId;
	private final int quantity;
	private final List<Reward> rewards;

	public SM_ITEM_COMPOSE_RESULT(int recipeId, int quantity, List<Reward> rewards) {
		this.recipeId = recipeId;
		this.quantity = quantity;
		this.rewards = rewards;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeH(quantity);
		writeH(rewards.size());
		for (Reward reward : rewards) {
			writeD(reward.itemId());
			writeQ(reward.count());
		}
	}
}
