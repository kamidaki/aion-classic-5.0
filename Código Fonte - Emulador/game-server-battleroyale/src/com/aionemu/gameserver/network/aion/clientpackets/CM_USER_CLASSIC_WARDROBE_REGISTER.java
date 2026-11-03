package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Registrar um item no Wardrobe, decodificado 0xEE (cru 0x184): [D item]. Captura 15:16 (1 de 1): o item some com S 0x1C motivo 0x81, depois
 * msg 1401541 e S 0x124 ação 1 com um objeto novo.
 */
public class CM_USER_CLASSIC_WARDROBE_REGISTER extends AionClientPacket {

	private int itemObjId;

	public CM_USER_CLASSIC_WARDROBE_REGISTER(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			PlayerWardrobeService.getInstance().registerItem(player, itemObjId);
	}
}
