package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collections;
import java.util.List;

import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.abyss.AbyssRankingCache;

/**
 * S_GUILD_INFO (0x6D) da 5.0, conferido byte a byte nas 11 variantes das capturas oficiais (AinzOO, Org Asmo, Lost Academy, com e sem aviso):
 *
 * <pre>
 * [S nome][C nível][D posição no ranking][H x4 permissões Deputy/Centurion/Legionary/Volunteer]
 * [D pontos de contribuição][D ?][D 0][D 0]
 * até 7 x ([S aviso][D hora]), com [S ""] no fim quando são menos de 7
 * [S descrição]
 * [11 b 0][D nível de crescimento][D exp de crescimento][24 b]
 * </pre>
 *
 * A 4.8 mandava Q de contribuição, horário de dissolução e três D de Legion Dominion no lugar do bloco de 16 b, e não tinha descrição nem o
 * bloco final de 43 b.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_LEGION_INFO extends AionServerPacket {

	private static final int MAX_ANNOUNCEMENTS = 7;

	private final Legion legion;
	private final int rankingListPosition;

	public SM_LEGION_INFO(Legion legion) {
		this(legion, AbyssRankingCache.getInstance().getRankingListPosition(legion));
	}

	SM_LEGION_INFO(Legion legion, int rankingListPosition) {
		this.legion = legion;
		this.rankingListPosition = rankingListPosition;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeS(legion.getName());
		writeC(legion.getLegionLevel());
		writeD(rankingListPosition);
		writeH(legion.getDeputyPermission());
		writeH(legion.getCenturionPermission());
		writeH(legion.getLegionaryPermission());
		writeH(legion.getVolunteerPermission());
		// contribuição: sobe o AP ganho pelo membro (Org Asmo 13/09 e 27/09, junto do STR_MSG_COMBAT_MY_ABYSS_POINT_GAIN)
		writeD((int) Math.min(legion.getContributionPoints(), Integer.MAX_VALUE));
		writeD(0); // PENDENTE_DE_COMPROVACAO: 5000000 na Org Asmo (nível 5), 0 nas de nível 1
		writeD(0);
		writeD(0);
		writeAnnouncements();
		writeS(""); // PENDENTE_DE_COMPROVACAO: texto da Legion (Org Asmo: "Legion BR - PvPvE - Discord Obg"), sem origem no servidor ainda
		writeB(new byte[11]); // 0 nas 11 variantes
		writeD(legion.getGrowthLevel());
		writeD(legion.getGrowthExp());
		// PENDENTE_DE_COMPROVACAO: +8 e +16 valem 10 e 314 na Org Asmo, +24 vai de 0 a 10 na Lost Academy depois do primeiro aviso
		writeB(new byte[24]);
	}

	/**
	 * O cliente aceita até 7 avisos e mostra o primeiro; o modelo guarda só o atual.
	 */
	private void writeAnnouncements() {
		List<Legion.Announcement> announcements = legion.getAnnouncement() == null ? Collections.emptyList()
			: Collections.singletonList(legion.getAnnouncement());
		for (int i = 0; i < MAX_ANNOUNCEMENTS; i++) {
			Legion.Announcement announcement = i < announcements.size() ? announcements.get(i) : null;
			if (announcement == null || announcement.message().isEmpty()) { // string vazia encerra a lista
				writeS("");
				return;
			}
			writeS(announcement.message());
			writeD((int) (announcement.time().getTime() / 1000));
		}
	}
}
