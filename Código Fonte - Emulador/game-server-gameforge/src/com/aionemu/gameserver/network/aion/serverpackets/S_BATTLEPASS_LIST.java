package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassReward;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassSeason;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.PlayerBattlePass;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_BATTLEPASS_LIST (0x0117) - 2 bytes count + 232 bytes per season (wire verified).
 */
public class S_BATTLEPASS_LIST extends AionServerPacket {

	private final Player player;
	private final PlayerBattlePass pass;

	public S_BATTLEPASS_LIST(Player player) {
		this.player = player;
		this.pass = player.getPlayerBattlePass();
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (this.pass == null || this.pass.getBattlePassSeason() == null || this.pass.getBattlePassSeason().isEmpty()) {
			writeH(0);
			return;
		}

		writeH(this.pass.getBattlePassSeason().size());
		int passType = (this.player.getAccount() != null && this.player.getAccount().getMembership() == 2) ? 2 : 1;

		for (BattlePassSeason season : this.pass.getBattlePassSeason().values()) {
			writeD(season != null ? season.getId() : 0);
			writeD(1);
			writeD(passType);
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
}

