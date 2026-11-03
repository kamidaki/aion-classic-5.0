package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collections;
import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0130 (304) - SM_RANK_LIST (S_RANK_LIST)
 * Official Classic 5.0 ranking list packet.
 * Chunked in parts of up to 94 entries (8003 bytes max).
 */
public class SM_RANK_LIST extends AionServerPacket {

	public static final int MAX_ENTRIES_PER_PACKET = 94;

	private final int rankingType;
	private final boolean isLocalServer;
	private final boolean isFirstPart;
	private final boolean isLastPart;
	private final int timestamp;
	private final List<RankingEntry> entries;

	public SM_RANK_LIST(int rankingType, boolean isLocalServer, boolean isFirstPart, boolean isLastPart, int timestamp, List<RankingEntry> entries) {
		this.rankingType = rankingType;
		this.isLocalServer = isLocalServer;
		this.isFirstPart = isFirstPart;
		this.isLastPart = isLastPart;
		this.timestamp = timestamp;
		this.entries = entries != null ? entries : Collections.emptyList();
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(rankingType);
		writeC(isLocalServer ? 1 : 0);
		writeC(isFirstPart ? 1 : 0);
		writeD(timestamp);

		int count = entries.size();
		// Negative count marks the final part of a list
		writeH(isLastPart ? -count : count);
		writeC(count > 0 ? 1 : 0);

		for (RankingEntry entry : entries) {
			writeD(entry.rankingType());
			writeD(entry.score());
			writeD(entry.rank());
			writeD(entry.oldRank());
			writeD(0);
			writeD(entry.playerId());
			writeD(entry.raceId());
			writeD(entry.playerClassId());
			writeC(0x17);
			writeS(entry.name(), 25);
		}
	}

	public int getRankingType() {
		return rankingType;
	}

	public boolean isLocalServer() {
		return isLocalServer;
	}

	public boolean isFirstPart() {
		return isFirstPart;
	}

	public boolean isLastPart() {
		return isLastPart;
	}

	public int getTimestamp() {
		return timestamp;
	}

	public List<RankingEntry> getEntries() {
		return entries;
	}

	public record RankingEntry(
		int rankingType,
		int score,
		int rank,
		int oldRank,
		int playerId,
		int raceId,
		int playerClassId,
		String name
	) {}
}
