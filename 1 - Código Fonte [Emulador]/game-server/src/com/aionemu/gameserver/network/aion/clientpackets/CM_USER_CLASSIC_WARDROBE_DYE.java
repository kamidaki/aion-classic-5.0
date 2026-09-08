package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.PlayerWardrobeService;

import java.util.Set;

public class CM_USER_CLASSIC_WARDROBE_DYE extends AionClientPacket {

	private int skinObj;
	private int dyeObj;

	public CM_USER_CLASSIC_WARDROBE_DYE(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_USER_CLASSIC_WARDROBE_DYE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		this.skinObj = readD();
		this.dyeObj = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null) {
			PlayerWardrobeService.getInstance().onApplyDye(player, this.skinObj, this.dyeObj);
		}
	}
}
