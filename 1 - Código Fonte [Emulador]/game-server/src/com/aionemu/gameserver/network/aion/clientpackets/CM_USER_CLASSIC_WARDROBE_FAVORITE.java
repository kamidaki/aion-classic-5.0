package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

/**
 * Marcar ou desmarcar favorito, decodificado 0xF9 (cru 0x18B): [D entrada][C 1 marca, 0 desmarca]. Captura 14:56 (1 de 1, marcando): S 0x124
 * ação 4 e msg 1401543.
 */
public class CM_USER_CLASSIC_WARDROBE_FAVORITE extends AionClientPacket {

	private int entryObjId;
	private int favorite;

	public CM_USER_CLASSIC_WARDROBE_FAVORITE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		entryObjId = readD();
		favorite = readUC();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			PlayerWardrobeService.getInstance().setFavorite(player, entryObjId, favorite != 0);
	}
}
