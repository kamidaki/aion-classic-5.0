package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Map;
import java.util.Set;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.StorybookService;

/**
 * Identificação de fragmentos desconhecidos do Book of Legends, decodificado 0xDC (cru 0x196). Captura (1 de 1, 50 b): 4 pilhas inteiras de
 * fragmentos desconhecidos. Layout no {@link CM_ITEM_COUNT_LIST}.
 */
public class CM_STORYBOOK_APPRAISE extends CM_ITEM_COUNT_LIST {

	public CM_STORYBOOK_APPRAISE(int opcode, Set<State> validStates) {
		super(opcode, validStates, StorybookService.MAX_ITEMS_PER_REQUEST);
	}

	@Override
	protected void handle(Player player, Map<Integer, Long> items) {
		StorybookService.appraise(player, items);
	}

	@Override
	protected void onInvalid(Player player, String reason) {
		LoggerFactory.getLogger(CM_STORYBOOK_APPRAISE.class).warn("Book of Legends: identificação inválida de {}: {}", player.getName(), reason);
	}
}
