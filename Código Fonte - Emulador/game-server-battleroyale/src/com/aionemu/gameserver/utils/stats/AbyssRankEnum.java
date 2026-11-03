package com.aionemu.gameserver.utils.stats;

import javax.xml.bind.annotation.XmlEnum;

import com.aionemu.gameserver.configs.main.RankingConfig;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.utils.ChatUtil;

/**
 * @author Lost Academy Team & Durak
 */
@XmlEnum
public enum AbyssRankEnum {
	GRADE9_SOLDIER(1, 300, 90, 0),
	GRADE8_SOLDIER(2, 345, 103, 1200),
	GRADE7_SOLDIER(3, 396, 118, 4220),
	GRADE6_SOLDIER(4, 455, 136, 10990),
	GRADE5_SOLDIER(5, 523, 156, 23500),
	GRADE4_SOLDIER(6, 601, 180, 42780),
	GRADE3_SOLDIER(7, 721, 216, 69700),
	GRADE2_SOLDIER(8, 865, 259, 105600),
	GRADE1_SOLDIER(9, 1038, 311, 150800),
	STAR1_OFFICER(10, 1557, 467, 150800),
	STAR2_OFFICER(11, 1868, 560, 150800),
	STAR3_OFFICER(12, 2148, 644, 150800),
	STAR4_OFFICER(13, 2470, 741, 150800),
	STAR5_OFFICER(14, 3705, 1482, 150800),
	GENERAL(15, 4075, 1630, 150800),
	GREAT_GENERAL(16, 4482, 1792, 150800),
	COMMANDER(17, 4930, 1972, 150800),
	SUPREME_COMMANDER(18, 5916, 2366, 150800);

	private final int id;
	private final int pointsGained;
	private final int pointsLost;
	private final int requiredAP;
	
	AbyssRankEnum(int id, int pointsGained, int pointsLost, int required) {
		this.id = id;
		this.pointsGained = pointsGained;
		this.pointsLost = pointsLost;
		this.requiredAP = required;
	}

	/**
	 * @return the id
	 */
	public int getId() {
		return id;
	}

	/**
	 * @return the pointsLost
	 */
	public int getPointsLost() {
		return pointsLost;
	}

	/**
	 * @return the pointsGained
	 */
	public int getPointsGained() {
		return pointsGained;
	}

	/**
	 * @return AP required for Rank
	 */
	public int getRequiredAP() {
		return requiredAP;
	}

	
	
	/**
	 * @return The quota is the maximum number of allowed player to have the rank
	 */
	public int getQuota() {
		return RankingConfig.TOP_RANKING_QUOTA.getOrDefault(this, 0);
	}

	public static String getRankL10n(Player player) {
		return player.getAbyssRank().getRank().getRankL10n(player.getRace());
	}

	public static String getRankL10n(Race race, int rankId) {
		return getRankById(rankId).getRankL10n(race);
	}

	public String getRankL10n(Race race) {
		int rank9L10nId = race == Race.ELYOS ? 901215 : 901233;
		int rankL10nId = rank9L10nId + ordinal();
		return ChatUtil.l10n(rankL10nId);
	}

	public static AbyssRankEnum getRankById(int id) {
		for (AbyssRankEnum rank : values()) {
			if (rank.getId() == id)
				return rank;
		}
		throw new IllegalArgumentException("Invalid abyss rank provided " + id);
	}

	public static AbyssRankEnum getRankForPoints(int ap) {
		AbyssRankEnum r = AbyssRankEnum.GRADE9_SOLDIER;
		for (AbyssRankEnum rank : values()) {
			if (rank.getRequiredAP() <= ap)
				r = rank;
		}
		return r;
	}
}
