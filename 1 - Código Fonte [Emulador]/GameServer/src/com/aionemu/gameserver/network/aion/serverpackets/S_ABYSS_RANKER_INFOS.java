/*
 * This file is part of aion-unique <aion-unique.smfnew.com>.
 *
 *  aion-unique is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  aion-unique is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with aion-unique.  If not, see <http://www.gnu.org/licenses/>.
 */
package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.AbyssRankingResult;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

import java.util.Collections;
import java.util.List;

/**
 * @author Rhys2002, zdead, LokiReborn
 */
public class S_ABYSS_RANKER_INFOS extends AionServerPacket {

	private List<AbyssRankingResult> data;
	private int lastUpdate;
	private int race;
	private int page;
	private boolean isEndPacket;

	public S_ABYSS_RANKER_INFOS(int lastUpdate, List<AbyssRankingResult> data, Race race, int page, boolean isEndPacket) {
		this.lastUpdate = lastUpdate;
		this.data = data;
		this.race = race.getRaceId();
		this.page = page;
		this.isEndPacket = isEndPacket;
	}
	
	public S_ABYSS_RANKER_INFOS(int lastUpdate, Race race) {
		this.lastUpdate = lastUpdate;
		this.data = Collections.emptyList();
		this.race = race.getRaceId();
		this.page = 0;
		this.isEndPacket = false;
	}

	@Override
	protected void writeImpl(AionConnection con){
		writeD(race);// 0:Elyos 1:Asmo
		writeD(lastUpdate);// Date
		writeD(page);
		writeD(isEndPacket ? 0x7F : 0);// 0:Nothing 1:Update Table
		writeH(data.size());// list size

		for (AbyssRankingResult rs : data) {
			writeD(rs.getRankPos());// Current Rank
			writeD(rs.getPlayerAbyssRank());// Abyss rank
			writeD((rs.getOldRankPos() == 0) ? 501 : rs.getOldRankPos());// Old Rank
			writeD(rs.getPlayerId()); // PlayerID
			writeD(race);
			writeD(rs.getPlayerClass().getClassId());// Class Id
			writeD(0); // Sex ? 0=male / 1=female
			writeQ(rs.getPlayerAP());// Abyss Points
			/*
			 * Medido na captura oficial (subida-1-60, sessao 1): o registro tem 177 bytes --
			 * 7 dwords + o Q dos pontos (36) + nome (54) + legiao (86) + 1 byte final. Nao ha
			 * campo de nivel; o `writeH` que existia aqui deslocava tudo a partir do nome, e os
			 * tamanhos 52/82 fechavam 172 em vez de 177. Conferido em 100 registros:
			 * `18 + 45*177 = 7983`, o tamanho exato do pacote.
			 */
			writeS(rs.getPlayerName(), 54);// Player Name
			writeS(rs.getLegionName(), 86);// Legion Name
			// 0x2E em todos os 86 registros com legiao, 0 nos 14 sem: marca a presenca da legiao.
			String legiao = rs.getLegionName();
			writeC(legiao == null || legiao.isEmpty() ? 0x00 : 0x2E);
		}
	}
}
