package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/** S 0x0149: update one claimed-reward flag, payload [H rewardId][C claimed]. */
public class SM_COMBAT_TALENT_REWARD_UPDATE extends AionServerPacket {

	private final int rewardId;
	private final boolean claimed;

	public SM_COMBAT_TALENT_REWARD_UPDATE(int rewardId, boolean claimed) {
		this.rewardId = rewardId;
		this.claimed = claimed;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(rewardId);
		writeC(claimed ? 1 : 0);
	}
}
