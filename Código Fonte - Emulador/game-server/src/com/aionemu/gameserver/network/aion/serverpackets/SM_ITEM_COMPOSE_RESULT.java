package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x1A7, resultado da fusão no Altar of Transcendence. Layout confirmado com uma e duas fusões:
 * [D receita][H quantidade][H resultados UP/TOP][quantidade x (D item, Q quantidade)]. Cada fusão ocupa um registro, inclusive quando
 * vários resultados têm o mesmo itemId.
 */
public class SM_ITEM_COMPOSE_RESULT extends AionServerPacket {

	public record Reward(int itemId, long count) {
	}

	private final int recipeId;
	private final int quantity;
	private final int upgraded;
	private final List<Reward> rewards;

	public SM_ITEM_COMPOSE_RESULT(int recipeId, int quantity, int upgraded, List<Reward> rewards) {
		this.recipeId = recipeId;
		this.quantity = quantity;
		this.upgraded = upgraded;
		this.rewards = rewards;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeH(quantity);
		writeH(upgraded);
		for (Reward reward : rewards) {
			writeD(reward.itemId());
			writeQ(reward.count());
		}
	}
}
