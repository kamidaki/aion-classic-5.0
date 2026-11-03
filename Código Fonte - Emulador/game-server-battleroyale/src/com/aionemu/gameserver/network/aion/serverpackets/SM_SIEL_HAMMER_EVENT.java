package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/** S_ITEM_CRUSH_EVENT: 1 starts the progress bar, 2 closes it (Game.dll RVA 0x23F000). */
public class SM_SIEL_HAMMER_EVENT extends AionServerPacket {
	private final int event;
	private final int duration;
	public SM_SIEL_HAMMER_EVENT(int event, int duration) { this.event = event; this.duration = duration; }
	@Override
	protected void writeImpl(AionConnection connection) { writeC(event); writeD(duration); }
}
