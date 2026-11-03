package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Map;
import java.util.Set;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.MorosService;

/**
 * Gravação no Moreth, Chronicle of Time, decodificado 0x111 (cru 0x1E3): um por espaço preenchido da janela (18 espaços). Captura (1 de 1, 14 b):
 * um capacete, quantidade 1. Layout no {@link CM_ITEM_COUNT_LIST}.
 */
public class CM_MOROS_RECORD extends CM_ITEM_COUNT_LIST {

	public CM_MOROS_RECORD(int opcode, Set<State> validStates) {
		super(opcode, validStates, MorosService.MAX_SLOTS);
	}

	@Override
	protected void handle(Player player, Map<Integer, Long> items) {
		MorosService.record(player, items);
	}

	@Override
	protected void onInvalid(Player player, String reason) {
		LoggerFactory.getLogger(CM_MOROS_RECORD.class).warn("Moreth: pedido inválido de {}: {}", player.getName(), reason);
	}
}
