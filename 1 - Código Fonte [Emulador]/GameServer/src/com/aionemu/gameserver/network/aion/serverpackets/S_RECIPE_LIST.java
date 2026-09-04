package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

import java.util.Set;

public class S_RECIPE_LIST extends AionServerPacket
{
	private Integer[] recipeIds;
	private int count;
	
	public S_RECIPE_LIST(Set<Integer> recipeIds) {
		this.recipeIds = recipeIds.toArray(new Integer[recipeIds.size()]);
		this.count = recipeIds.size();
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		writeH(count);
		for (int id : recipeIds) {
			writeD(id);
			writeC(1);
		}
	}
}