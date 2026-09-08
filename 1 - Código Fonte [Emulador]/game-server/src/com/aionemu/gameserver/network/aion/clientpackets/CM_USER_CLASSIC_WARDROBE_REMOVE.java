package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

import java.util.Set;

public class CM_USER_CLASSIC_WARDROBE_REMOVE extends AionClientPacket {

	private int objectId;

	public CM_USER_CLASSIC_WARDROBE_REMOVE(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_USER_CLASSIC_WARDROBE_REMOVE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		this.objectId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null) {
			PlayerWardrobeService.getInstance().onDelete(player, this.objectId);
		}
	}
}
