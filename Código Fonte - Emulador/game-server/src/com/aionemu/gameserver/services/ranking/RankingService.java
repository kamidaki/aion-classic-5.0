package com.aionemu.gameserver.services.ranking;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.dao.AbyssRankDAO;
import com.aionemu.gameserver.dao.AbyssRankDAO.RankingListPlayer;
import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANK_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANK_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANK_LIST.RankingEntry;
import com.aionemu.gameserver.services.CombatTalentService;
import com.aionemu.gameserver.world.World;

/**
 * Service for Classic 5.0 Combat Power Rankings (S_RANK_LIST / S_RANK_INFO).
 * Supports types 1000, 1001, 1002, 1003.
 */
public class RankingService {

	private static final Logger log = LoggerFactory.getLogger(RankingService.class);

	// Official class order for class-specific rankings (descending class ID)
	public static final int[] ORDERED_CLASSES = { 25, 22, 19, 16, 13, 11, 10, 8, 7, 5, 4, 2, 1 };

	private static final int MAX_ENTRIES_1000 = 500;
	private static final int MAX_PER_CLASS_1001 = 100;
	private static final int MAX_ENTRIES_1002 = 300;
	private static final int MAX_PER_CLASS_1003 = 20;

	private final Map<Integer, List<RankingEntry>> cachedRankings = new ConcurrentHashMap<>();
	private final Map<Integer, List<SM_RANK_LIST>> cachedPackets = new ConcurrentHashMap<>();
	private volatile int lastUpdateTimestamp;

	private RankingService() {
		refreshRankings();
	}

	public static RankingService getInstance() {
		return SingletonHolder.INSTANCE;
	}

	public synchronized void refreshRankings() {
		int updateTime = (int) (System.currentTimeMillis() / 1000);
		this.lastUpdateTimestamp = updateTime;

		// 1. Gather players from World and DB
		Map<Integer, RankingCandidate> candidateMap = new HashMap<>();

		// From DB (AbyssRankDAO)
		try {
			List<RankingListPlayer> dbPlayers = AbyssRankDAO.loadRankingListPlayers();
			if (dbPlayers != null) {
				for (RankingListPlayer dbp : dbPlayers) {
					int baseCp = dbp.level() * 300 + (dbp.ap() > 0 ? (int) Math.min(15000, dbp.ap() / 50) : 0);
					candidateMap.put(dbp.id(), new RankingCandidate(
						dbp.id(), dbp.name(), dbp.race().getRaceId(), dbp.playerClass().getClassId(), baseCp, dbp.oldPosition()
					));
				}
			}
		} catch (Exception e) {
			log.warn("Could not load DB players for ranking: " + e.getMessage());
		}

		// Live players in world (exact combat power calculation)
		try {
			for (Player player : World.getInstance().getAllPlayers()) {
				int cp = CombatTalentService.calculateCombatPower(player);
				int oldRank = 0;
				if (candidateMap.containsKey(player.getObjectId())) {
					oldRank = candidateMap.get(player.getObjectId()).oldRank();
				}
				candidateMap.put(player.getObjectId(), new RankingCandidate(
					player.getObjectId(), player.getName(), player.getRace().getRaceId(), player.getPlayerClass().getClassId(), cp, oldRank
				));
			}
		} catch (Exception e) {
			log.warn("Could not scan world players for ranking: " + e.getMessage());
		}

		List<RankingCandidate> allCandidates = new ArrayList<>(candidateMap.values());
		allCandidates.sort(Comparator.comparingInt(RankingCandidate::score).reversed().thenComparingInt(RankingCandidate::playerId));

		// Build Type 1000: Inter-Server Overall (up to 500)
		List<RankingEntry> entries1000 = buildOverallRanking(1000, allCandidates, MAX_ENTRIES_1000);
		cachedRankings.put(1000, entries1000);
		cachedPackets.put(1000, partitionPackets(1000, false, updateTime, entries1000));

		// Build Type 1001: Inter-Server By Class (13 classes * up to 100)
		List<RankingEntry> entries1001 = buildClassRanking(1001, allCandidates, MAX_PER_CLASS_1001);
		cachedRankings.put(1001, entries1001);
		cachedPackets.put(1001, partitionPackets(1001, false, updateTime, entries1001));

		// Build Type 1002: Local Server Overall (up to 300)
		List<RankingEntry> entries1002 = buildOverallRanking(1002, allCandidates, MAX_ENTRIES_1002);
		cachedRankings.put(1002, entries1002);
		cachedPackets.put(1002, partitionPackets(1002, true, updateTime, entries1002));

		// Build Type 1003: Local Server By Class (13 classes * up to 20)
		List<RankingEntry> entries1003 = buildClassRanking(1003, allCandidates, MAX_PER_CLASS_1003);
		cachedRankings.put(1003, entries1003);
		cachedPackets.put(1003, partitionPackets(1003, true, updateTime, entries1003));
	}

	private List<RankingEntry> buildOverallRanking(int type, List<RankingCandidate> candidates, int maxCount) {
		List<RankingEntry> result = new ArrayList<>();
		int rank = 1;
		for (RankingCandidate c : candidates) {
			if (rank > maxCount) break;
			result.add(new RankingEntry(type, c.score(), rank, c.oldRank(), c.playerId(), c.raceId(), c.classId(), c.name()));
			rank++;
		}
		return result;
	}

	private List<RankingEntry> buildClassRanking(int type, List<RankingCandidate> candidates, int maxPerClass) {
		List<RankingEntry> result = new ArrayList<>();
		Map<Integer, List<RankingCandidate>> byClass = candidates.stream().collect(Collectors.groupingBy(RankingCandidate::classId));

		for (int cid : ORDERED_CLASSES) {
			List<RankingCandidate> classList = byClass.getOrDefault(cid, Collections.emptyList());
			int rank = 1;
			for (RankingCandidate c : classList) {
				if (rank > maxPerClass) break;
				result.add(new RankingEntry(type, c.score(), rank, c.oldRank(), c.playerId(), c.raceId(), c.classId(), c.name()));
				rank++;
			}
		}
		return result;
	}

	public List<SM_RANK_LIST> partitionPackets(int rankingType, boolean isLocalServer, int timestamp, List<RankingEntry> entries) {
		List<SM_RANK_LIST> packets = new ArrayList<>();
		if (entries == null || entries.isEmpty()) {
			packets.add(new SM_RANK_LIST(rankingType, isLocalServer, true, true, timestamp, Collections.emptyList()));
			return packets;
		}

		int total = entries.size();
		int maxPerChunk = SM_RANK_LIST.MAX_ENTRIES_PER_PACKET;
		int numChunks = (total + maxPerChunk - 1) / maxPerChunk;

		for (int i = 0; i < numChunks; i++) {
			int from = i * maxPerChunk;
			int to = Math.min(from + maxPerChunk, total);
			boolean isFirst = (i == 0);
			boolean isLast = (i == numChunks - 1);
			packets.add(new SM_RANK_LIST(rankingType, isLocalServer, isFirst, isLast, timestamp, entries.subList(from, to)));
		}
		return packets;
	}

	public List<SM_RANK_LIST> getRankListPackets(int rankingType) {
		List<SM_RANK_LIST> list = cachedPackets.get(rankingType);
		if (list == null) {
			refreshRankings();
			list = cachedPackets.get(rankingType);
		}
		return list != null ? list : Collections.singletonList(
			new SM_RANK_LIST(rankingType, rankingType >= 1002, true, true, lastUpdateTimestamp, Collections.emptyList())
		);
	}

	public SM_RANK_INFO getRankInfoPacket(Player player, int rankingType) {
		int cp = CombatTalentService.calculateCombatPower(player);
		int currentRank = 0;

		List<RankingEntry> list = cachedRankings.get(rankingType);
		if (list != null) {
			for (RankingEntry entry : list) {
				if (entry.playerId() == player.getObjectId()) {
					currentRank = entry.rank();
					break;
				}
			}
		}

		int bestRank = currentRank > 0 ? currentRank : -1;
		int bestScore = cp;
		return new SM_RANK_INFO(rankingType, currentRank, cp, bestRank, bestScore);
	}

	public int getLastUpdateTimestamp() {
		return lastUpdateTimestamp;
	}

	private record RankingCandidate(
		int playerId,
		String name,
		int raceId,
		int classId,
		int score,
		int oldRank
	) {}

	private static class SingletonHolder {
		private static final RankingService INSTANCE = new RankingService();
	}
}
