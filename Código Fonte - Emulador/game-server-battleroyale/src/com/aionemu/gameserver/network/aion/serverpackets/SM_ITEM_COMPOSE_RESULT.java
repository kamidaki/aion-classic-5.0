package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x1A7, resultado da fusão no Altar of Transcendence. Layout confirmado com uma e duas fusões:
 * [D receita][H quantidade][quantidade x (H grau, D item, Q quantidade)]. Cada fusão ocupa um registro, inclusive quando vários resultados
 * têm o mesmo itemId. Grau: 0 SAME, 1 UP, 2 TOP.
 */
public class SM_ITEM_COMPOSE_RESULT extends AionServerPacket {

	public record Reward(int grade, int itemId, long count) {
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
		for (Reward reward : rewards) {
			writeH(reward.grade());
			writeD(reward.itemId());
			writeQ(reward.count());
		}
	}
}
