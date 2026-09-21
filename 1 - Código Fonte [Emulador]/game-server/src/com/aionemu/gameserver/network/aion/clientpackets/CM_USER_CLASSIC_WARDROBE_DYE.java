package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Tingir uma entrada do Wardrobe, decodificado 0xF8 (cru 0x18A): [D entrada][D tinta]. Captura 14:56 (1 de 1): S 0x1C da tinta (motivo 0x82),
 * S 0x124 ação 3 com a cor nova e msg 1401565.
 */
public class CM_USER_CLASSIC_WARDROBE_DYE extends AionClientPacket {

	private int entryObjId;
	private int dyeObjId;

	public CM_USER_CLASSIC_WARDROBE_DYE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		entryObjId = readD();
		dyeObjId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			PlayerWardrobeService.getInstance().dyeEntry(player, entryObjId, dyeObjId);
	}
}
