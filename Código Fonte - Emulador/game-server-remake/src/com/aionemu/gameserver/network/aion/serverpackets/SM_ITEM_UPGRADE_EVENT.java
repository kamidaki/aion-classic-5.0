package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x1AD (S_ITEM_UPGRADE_EVENT), estado do Ascend: [D receita][C evento][D ms]. Capturas: início [D receita][C 1][D 1000] (3 de 3, receitas 1070
 * e 1071; o resultado chega 1 s depois) e interrupção pelo C 0x142 [D 0][C 2][D 0] (2 de 2, receita 0). O evento 0 (recusado) vem do
 * SM_ITEM_COMPOSE_EVENT, de mesmo layout.
 */
public class SM_ITEM_UPGRADE_EVENT extends AionServerPacket {

	public static final int REJECTED = 0;
	public static final int STARTED = 1;
	public static final int ABORTED = 2;

	private final int recipeId;
	private final int event;
	private final int duration;

	public SM_ITEM_UPGRADE_EVENT(int recipeId, int event, int duration) {
		this.recipeId = recipeId;
		this.event = event;
		this.duration = duration;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(recipeId);
		writeC(event);
		writeD(duration);
	}
}
