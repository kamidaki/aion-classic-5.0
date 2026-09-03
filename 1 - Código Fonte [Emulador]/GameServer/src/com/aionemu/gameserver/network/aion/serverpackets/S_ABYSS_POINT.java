package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.AbyssRank;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.utils.stats.AbyssRankEnum;

public class S_ABYSS_POINT extends AionServerPacket
{
	private AbyssRank rank;
	private int currentRankId;
	
	public S_ABYSS_POINT(AbyssRank rank) {
		this.rank = rank;
		this.currentRankId = rank.getRank().getId();
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		writeQ(rank.getAp()); // curAP
		writeD(currentRankId); // curRank
		writeD(rank.getTopRanking()); // curRating
		int nextRankId = currentRankId < AbyssRankEnum.values().length ? currentRankId + 1 : currentRankId;
		writeD(100 * rank.getAp() / AbyssRankEnum.getRankById(nextRankId).getApRequired());
		writeD(rank.getAllKill()); // allKill
		writeD(rank.getMaxRank()); // maxRank
		writeD(rank.getDailyKill()); // dayKill
		writeQ(rank.getDailyAP()); // dayAP
		writeD(rank.getWeeklyKill()); // weekKill
		writeQ(rank.getWeeklyAP()); // weekAP
		writeD(rank.getLastKill()); // laterKill
		writeQ(rank.getLastAP()); // laterAP
		writeC(0x00); // unk
		/*
		 * A captura oficial traz 69 bytes; sem estes quatro o pacote fecha em 65 e o cliente le
		 * quatro bytes alem do corpo. Nas tres ocorrencias da captura estes bytes sao zero, entao
		 * o significado do campo ainda e desconhecido -- o que se sabe e o tamanho.
		 */
		writeD(0x00);
	}
}