package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassReward;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassSeason;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_BATTLEPASS_UPDATED (0x0118) - Exactly 232 bytes per season (wire verified).
 */
public class S_BATTLEPASS_UPDATED extends AionServerPacket {

	private final BattlePassSeason season;

	public S_BATTLEPASS_UPDATED(BattlePassSeason season) {
		this.season = season;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(this.season != null ? this.season.getId() : 0);
		writeD(1);
		writeD(2);
		writeD(season != null ? season.getLevel() : 1);
		writeD(season != null ? (int) season.getExp() : 0);
		writeD(0);
		writeD(0);
		writeD(0);

		int writtenRewardBytes = 0;
		if (season != null && season.getRewards() != null) {
			for (BattlePassReward reward : season.getRewards().values()) {
				if (writtenRewardBytes + 2 > 200)
					break;
				writeC(reward.isRewarded() ? 1 : 0);
				writeC(reward.isUnlockReward() ? 1 : 0);
				writtenRewardBytes += 2;
			}
		}
		if (writtenRewardBytes < 200) {
			writeB(new byte[200 - writtenRewardBytes]);
		}
	}
}

