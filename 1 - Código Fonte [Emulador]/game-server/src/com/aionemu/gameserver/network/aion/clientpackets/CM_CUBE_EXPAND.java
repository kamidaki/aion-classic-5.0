package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.CubeExpandService;

import java.util.Set;

public class CM_CUBE_EXPAND extends AionClientPacket {

	private int type;

	public CM_CUBE_EXPAND(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_CUBE_EXPAND(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		type = readC();
	}

	@Override
	protected void runImpl() {
		Player activePlayer = getConnection().getActivePlayer();
		if (activePlayer == null || !activePlayer.isSpawned()) {
			return;
		}
		if (activePlayer.isProtectionActive()) {
			activePlayer.getController().stopProtectionActiveTask();
		}
		if (activePlayer.isCasting()) {
			activePlayer.getController().cancelCurrentSkill(null);
		}
	}
}
