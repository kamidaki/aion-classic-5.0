package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0131 (305) - SM_RANK_INFO (S_RANK_INFO)
 * Official Classic 5.0 player ranking info packet (40 bytes fixed, 10 ints).
 */
public class SM_RANK_INFO extends AionServerPacket {

	private final int rankingType;
	private final int currentRank;
	private final int currentScore;
	private final int preRank;
	private final int preScore;
	private final int bestRank;
	private final int bestScore;

	public SM_RANK_INFO(int rankingType, int currentRank, int currentScore, int bestRank, int bestScore) {
		this(rankingType, currentRank, currentScore, 0, 0, bestRank, bestScore);
	}

	public SM_RANK_INFO(int rankingType, int currentRank, int currentScore, int preRank, int preScore, int bestRank, int bestScore) {
		this.rankingType = rankingType;
		this.currentRank = currentRank;
		this.currentScore = currentScore;
		this.preRank = preRank;
		this.preScore = preScore;
		this.bestRank = bestRank;
		this.bestScore = bestScore;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(rankingType);
		writeD(currentRank);
		writeD(currentScore);
		writeD(preRank);
		writeD(preScore);
		writeD(0);
		writeD(bestRank);
		writeD(bestScore);
		writeD(currentRank);
		writeD(currentScore);
	}

	public int getRankingType() {
		return rankingType;
	}

	public int getCurrentRank() {
		return currentRank;
	}

	public int getCurrentScore() {
		return currentScore;
	}

	public int getBestRank() {
		return bestRank;
	}

	public int getBestScore() {
		return bestScore;
	}
}
