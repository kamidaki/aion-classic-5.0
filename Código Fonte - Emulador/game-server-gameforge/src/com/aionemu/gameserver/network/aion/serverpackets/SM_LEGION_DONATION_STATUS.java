package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x158, produção do próprio personagem: [D produções hoje][D dias seguidos] (Kodra 1 a 10 com 1 dia, 22/09).
 */
public class SM_LEGION_DONATION_STATUS extends AionServerPacket {

	private final int countToday;
	private final int streak;

	public SM_LEGION_DONATION_STATUS(int countToday, int streak) {
		this.countToday = countToday;
		this.streak = streak;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(countToday);
		writeD(streak);
	}
}
