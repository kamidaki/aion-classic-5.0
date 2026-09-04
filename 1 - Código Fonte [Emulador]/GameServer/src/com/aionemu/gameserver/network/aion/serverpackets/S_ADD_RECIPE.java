package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_ADD_RECIPE extends AionServerPacket
{
	private int recipeId;
	
	public S_ADD_RECIPE(int recipeId) {
		this.recipeId = recipeId;
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeC(1);
	}
}