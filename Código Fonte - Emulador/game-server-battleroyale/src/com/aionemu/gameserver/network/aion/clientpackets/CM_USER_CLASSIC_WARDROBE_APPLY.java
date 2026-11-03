package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Aplicar ou tirar o visual de um item, decodificado 0xFA (cru 0x188): [D item][D entrada], com entrada 0 para tirar. Captura 14:56 (5 de 5):
 * 3 aplicações e 2 remoções, em asa e torso que estavam no cubo.
 */
public class CM_USER_CLASSIC_WARDROBE_APPLY extends AionClientPacket {

	private int itemObjId;
	private int entryObjId;

	public CM_USER_CLASSIC_WARDROBE_APPLY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjId = readD();
		entryObjId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			PlayerWardrobeService.getInstance().changeSkin(player, itemObjId, entryObjId);
	}
}
