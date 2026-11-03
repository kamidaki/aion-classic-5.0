package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.StorybookService;

/**
 * C_USER_STORY_BOOK_REGISTER_ITEM, decodificado 0xE4 (cru 0x19E): [D livro]. O servidor escolhe o que registrar entre os itens do inventário.
 * Capturas (3 de 3): livros 1, 2 e 6.
 */
public class CM_STORYBOOK_REGISTER extends AionClientPacket {

	private int storybookId;

	public CM_STORYBOOK_REGISTER(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		storybookId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			StorybookService.register(player, storybookId);
	}
}
