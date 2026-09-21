package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Apagar uma entrada do Wardrobe, decodificado 0xEF (cru 0x185): [D entrada]. Captura 15:16 (2 de 2): S 0x124 ação 2 e msg 1401542, sem custo.
 */
public class CM_USER_CLASSIC_WARDROBE_REMOVE extends AionClientPacket {

	private int entryObjId;

	public CM_USER_CLASSIC_WARDROBE_REMOVE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		entryObjId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			PlayerWardrobeService.getInstance().deleteEntry(player, entryObjId);
	}
}
