package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Map;
import java.util.Set;

import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.StorybookService;

/**
 * Desmontagem de fragmentos do Book of Legends, decodificado 0xDD (cru 0x197). Captura (1 de 1, 62 b): 5 pilhas inteiras de fragmentos repetidos.
 * Layout no {@link CM_ITEM_COUNT_LIST}.
 */
public class CM_STORYBOOK_DISASSEMBLE extends CM_ITEM_COUNT_LIST {

	public CM_STORYBOOK_DISASSEMBLE(int opcode, Set<State> validStates) {
		super(opcode, validStates, StorybookService.MAX_ITEMS_PER_REQUEST);
	}

	@Override
	protected void handle(Player player, Map<Integer, Long> items) {
		StorybookService.disassemble(player, items);
	}

	@Override
	protected void onInvalid(Player player, String reason) {
		LoggerFactory.getLogger(CM_STORYBOOK_DISASSEMBLE.class).warn("Book of Legends: desmontagem inválida de {}: {}", player.getName(), reason);
	}
}
