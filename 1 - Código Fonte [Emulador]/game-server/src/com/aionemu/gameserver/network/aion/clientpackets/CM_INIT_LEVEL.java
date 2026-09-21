package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.List;
import java.util.Set;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ABYSS_RANKING_PLAYERS;
import com.aionemu.gameserver.network.aion.serverpackets.SM_INVINCIBLE_TIME;
import com.aionemu.gameserver.network.aion.serverpackets.SM_NPSHOP_GOODS_COUNT;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANKING_READY;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SECURITY_TOKEN;
import com.aionemu.gameserver.services.abyss.AbyssRankingCache;
import com.aionemu.gameserver.services.mail.BlackCloudMailService;

/**
 * CM_INIT_LEVEL (0x0056 wire 0x12C).
 * Notificacao de inicializacao de level enviada pelo cliente Classic 5.0.
 * No PCAP oficial, a resposta a este pacote conclui o carregamento enviando:
 * SM_ABYSS_RANKING_PLAYERS, SM_NPSHOP_GOODS_COUNT, SM_RANKING_READY,
 * SM_SECURITY_TOKEN e SM_INVINCIBLE_TIME, permitindo que o cliente envie CM_LEVEL_READY.
 */
public class CM_INIT_LEVEL extends AionClientPacket {

	public CM_INIT_LEVEL(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	public CM_INIT_LEVEL(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null) {
			return;
		}
		List<SM_ABYSS_RANKING_PLAYERS> elyosRanks = AbyssRankingCache.getInstance().getPlayers(Race.ELYOS);
		if (elyosRanks == null || elyosRanks.isEmpty()) {
			sendPacket(new SM_ABYSS_RANKING_PLAYERS(AbyssRankingCache.getInstance().getLastUpdate(), Race.ELYOS));
		} else {
			for (SM_ABYSS_RANKING_PLAYERS packet : elyosRanks) {
				sendPacket(packet);
			}
		}
		List<SM_ABYSS_RANKING_PLAYERS> asmoRanks = AbyssRankingCache.getInstance().getPlayers(Race.ASMODIANS);
		if (asmoRanks == null || asmoRanks.isEmpty()) {
			sendPacket(new SM_ABYSS_RANKING_PLAYERS(AbyssRankingCache.getInstance().getLastUpdate(), Race.ASMODIANS));
		} else {
			for (SM_ABYSS_RANKING_PLAYERS packet : asmoRanks) {
				sendPacket(packet);
			}
		}
		sendPacket(new SM_NPSHOP_GOODS_COUNT(BlackCloudMailService.getGoodsCount(player.getAccount().getId())));
		sendPacket(new SM_RANKING_READY());
		sendPacket(new SM_RANKING_READY());
		sendPacket(new SM_SECURITY_TOKEN(new byte[32]));
		sendPacket(new SM_INVINCIBLE_TIME(60));
	}
}
