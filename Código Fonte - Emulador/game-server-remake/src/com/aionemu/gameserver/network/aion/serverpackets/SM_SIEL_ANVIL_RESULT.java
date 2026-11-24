package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/** Recipe, completion flag, byte outcome vector, unsigned-short ceiling progress. */
public class SM_SIEL_ANVIL_RESULT extends AionServerPacket {
	private final int recipeId;
	private final java.util.List<Integer> results;
	private final int ceiling;
	public SM_SIEL_ANVIL_RESULT(int recipeId, int productIndex) {
		this(recipeId, java.util.List.of(productIndex), 0);
	}
	public SM_SIEL_ANVIL_RESULT(int recipeId, java.util.List<Integer> results, int ceiling) {
		this.recipeId = recipeId;
		this.results = java.util.List.copyOf(results);
		this.ceiling = ceiling;
	}
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeC(1);
		writeH(results.size());
		for (int result : results) writeC(result);
		writeH(ceiling);
	}
}
