package com.aionemu.gameserver.services.abyss;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.stats.AbyssRankEnum;

/**
 * @author Lost Academy Team & Durak
 */
public class AbyssService {

	private static final int[] killAnnounceMaps = { 210050000, 220070000, 400010000, 400020000, 400030000, 400040000, 400050000,
		400060000, 600010000, 600070000, 0 };

	private static final boolean shouldAnnounceHighRankedDeath(Player victim) {
		if (victim.getAbyssRank().getRank().getId() >= AbyssRankEnum.GRADE1_SOLDIER.getId()) {
			for (int map : killAnnounceMaps) {
				if (map == victim.getWorldId())
					return true;
			}
		}
		return false;
	}

	public static final void announceHighRankedDeath(Player victim) {
		if (!shouldAnnounceHighRankedDeath(victim))
			return;
		PacketSendUtility.broadcastToWorld(SM_SYSTEM_MESSAGE.STR_ABYSS_ORDER_RANKER_DIE(victim),
			p -> p != victim && victim.getWorldType() == p.getWorldType() && !p.isInInstance());
	}

	public static final void announceAbyssSkillUsage(Player player, String skillL10n) {
		PacketSendUtility.broadcastToWorld(SM_SYSTEM_MESSAGE.STR_SKILL_ABYSS_SKILL_IS_FIRED(player, skillL10n),
			p -> p != player && player.getWorldType() == p.getWorldType() && !p.isInInstance());
	}
}
