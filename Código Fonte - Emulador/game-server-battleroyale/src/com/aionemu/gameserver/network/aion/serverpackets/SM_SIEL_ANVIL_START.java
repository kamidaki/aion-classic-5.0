package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/** Official payload: D recipe, C accepted, D milliseconds. */
public class SM_SIEL_ANVIL_START extends AionServerPacket {
	private final int recipeId;
	private final int duration;
	private final int event;
	public SM_SIEL_ANVIL_START(int recipeId, int duration) {
		this(recipeId, duration > 0 ? 1 : 0, duration);
	}
	public SM_SIEL_ANVIL_START(int recipeId, int event, int duration) {
		this.recipeId = recipeId;
		this.duration = duration;
		this.event = event;
	}
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeC(event);
		writeD(duration);
	}
}
