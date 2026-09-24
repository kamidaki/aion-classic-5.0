package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.teleport.TeleportService;

import java.util.Set;

public class CM_QUEST_TELEPORT extends AionClientPacket {

	private int questId;
	private int npcId;

	public CM_QUEST_TELEPORT(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_QUEST_TELEPORT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		this.questId = readD();
		this.npcId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null || !player.isSpawned() || player.isDead()) {
			return;
		}

		if (player.getController().isInCombat() || player.getMoveController().isInMove()) {
			return;
		}

		if (npcId > 0) {
			TeleportService.teleportToNpc(player, npcId);
		}
	}
}
