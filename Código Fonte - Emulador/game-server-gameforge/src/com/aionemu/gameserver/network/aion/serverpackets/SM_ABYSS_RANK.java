package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.AbyssRank;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.abyss.AbyssRankingCache;
import com.aionemu.gameserver.utils.stats.AbyssRankEnum;

/**
 * SM_ABYSS_RANK (0x00ED) - Exactly 69 bytes payload verified against official Classic 5.0 PCAP.
 * @author Lost Academy Team & Durak
 */
public class SM_ABYSS_RANK extends AionServerPacket {

	private final AbyssRank rank;
	private final int rankingListPosition;

	public SM_ABYSS_RANK(Player player) {
		this(player, null);
	}

	public SM_ABYSS_RANK(Player player, Integer rankingListPosition) {
		this.rank = player.getAbyssRank();
		this.rankingListPosition = rankingListPosition == null ? AbyssRankingCache.getInstance().getRankingListPosition(player) : rankingListPosition;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		int currentRankId = rank.getRank().getId();
		int nextRankId = currentRankId < AbyssRankEnum.values().length ? currentRankId + 1 : currentRankId;
		int apRequired = AbyssRankEnum.getRankById(nextRankId).getRequiredAP();
		int percent = apRequired > 0 ? (int) (100 * rank.getAp() / apRequired) : 0;

		writeQ(rank.getAp()); // 8 (curAP)
		writeD(currentRankId); // 4 (curRank)
		writeD(rankingListPosition); // 4 (curRating)
		writeD(percent); // 4
		writeD(rank.getAllKill()); // 4 (allKill)
		writeD(rank.getMaxRank()); // 4 (maxRank)
		writeD(rank.getDailyKill()); // 4 (dayKill)
		writeQ(rank.getDailyAP()); // 8 (dayAP)
		writeD(rank.getWeeklyKill()); // 4 (weekKill)
		writeQ(rank.getWeeklyAP()); // 8 (weekAP)
		writeD(rank.getLastKill()); // 4 (laterKill)
		writeQ(rank.getLastAP()); // 8 (laterAP)
		writeC(0x00); // 1
		writeD(0x00); // 4
		// 8+4+4+4+4+4+4+8+4+8+4+8+1+4 = 69 bytes
	}
}

