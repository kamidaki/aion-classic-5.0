package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_RECIPE_LIST;

/**
 * Client request for recipes list (Opcode 0x00B6 in 5.0 Classic).
 */
public class CM_RECIPE_LIST extends AionClientPacket {

	public CM_RECIPE_LIST(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		// Empty payload in 5.0 Classic (len 0)
		readB(getRemainingBytes());
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null && player.getRecipeList() != null) {
			sendPacket(new S_RECIPE_LIST(player.getRecipeList().getRecipeList()));
		}
	}
}
