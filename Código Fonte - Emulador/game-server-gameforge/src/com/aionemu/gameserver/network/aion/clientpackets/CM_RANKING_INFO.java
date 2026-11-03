package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.List;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANK_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANK_LIST;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANKING_READY;
import com.aionemu.gameserver.services.ranking.RankingService;

/**
 * Opcode wire 0x01B6 (dec 0x00BC) - CM_RANKING_INFO
 * Client requests ranking list and player ranking info for a rankingType (1000, 1001, 1002, 1003).
 */
public class CM_RANKING_INFO extends AionClientPacket {

	private static final Logger log = LoggerFactory.getLogger(CM_RANKING_INFO.class);

	private int rankingType;

	public CM_RANKING_INFO(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_RANKING_INFO(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		rankingType = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null) {
			return;
		}

		log.debug("Player " + player.getName() + " requested ranking info for type " + rankingType);

		// Send ranking list parts (SM_RANK_LIST)
		List<SM_RANK_LIST> parts = RankingService.getInstance().getRankListPackets(rankingType);
		for (SM_RANK_LIST part : parts) {
			sendPacket(part);
		}

		// Send player ranking info (SM_RANK_INFO)
		SM_RANK_INFO info = RankingService.getInstance().getRankInfoPacket(player, rankingType);
		sendPacket(info);

		// 5.0: depois do S 0x131 vem o S 0x1B5 (06_Sistemas_Novos 2026-10-20 02:17); o S 0x138 é a opção do badge e não vai aqui
		sendPacket(new SM_RANKING_READY());
	}
}
