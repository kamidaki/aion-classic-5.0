package com.aionemu.gameserver.network.aion.serverpackets;

import static com.aionemu.gameserver.network.aion.serverpackets.AbstractPlayerInfoPacket.CHARNAME_MAX_LENGTH;

import java.util.Collections;
import java.util.List;

import com.aionemu.gameserver.dao.AbyssRankDAO.RankingListPlayer;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_ABYSS_RANKING_PLAYERS extends AionServerPacket {

	private final List<RankingListPlayer> players;
	private final int lastUpdate;
	private final int race;
	private final int page;
	private final boolean isEndPacket;

	public SM_ABYSS_RANKING_PLAYERS(int lastUpdate, Race race) {
		this(lastUpdate, Collections.emptyList(), race, 1, true);
	}

	public SM_ABYSS_RANKING_PLAYERS(int lastUpdate, List<RankingListPlayer> players, Race race, int page, boolean isEndPacket) {
		this.lastUpdate = lastUpdate;
		this.players = players;
		this.race = race.getRaceId();
		this.page = page;
		this.isEndPacket = isEndPacket;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(race);
		writeD(lastUpdate);
		writeD(page);
		writeD(isEndPacket ? 0x7F : 0);
		writeH(players.size());

		for (RankingListPlayer player : players) {
			writeD(player.position());
			writeD(player.abyssRank());
			writeD(player.oldPosition() == 0 ? 501 : player.oldPosition());
			writeD(player.id());
			writeD(race);
			writeD(player.playerClass().getClassId());
			writeD(player.gender().getGenderId());
			writeQ(player.ap());
			writeS(player.name(), 54);
			writeS(player.legionName(), 86);
			String legion = player.legionName();
			writeC(legion == null || legion.isEmpty() ? 0x00 : 0x2E);
		}
	}
}
