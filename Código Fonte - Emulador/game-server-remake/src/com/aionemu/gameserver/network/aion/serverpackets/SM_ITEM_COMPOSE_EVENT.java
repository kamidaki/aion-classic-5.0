package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 0x1A6, início da fusão no Altar of Transcendence: [D receita][C evento][D ms]. Captura (2 de 2): [D receita][C 1][D 1000], e o resultado
 * chega 1 s depois. Mesmo layout do SM_SIEL_ANVIL_START, de onde vêm os eventos 0 (recusado) e 2 (interrompido).
 */
public class SM_ITEM_COMPOSE_EVENT extends AionServerPacket {

	public static final int REJECTED = 0;
	public static final int STARTED = 1;
	public static final int ABORTED = 2;

	private final int recipeId;
	private final int event;
	private final int duration;

	public SM_ITEM_COMPOSE_EVENT(int recipeId, int event, int duration) {
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
