package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.ArmsfusionService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_FUSION_WEAPONS extends AionClientPacket {

	public CM_FUSION_WEAPONS(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	private int firstItemId;
	private int secondItemId;

	@Override
	protected void readImpl() {
		readD();
		firstItemId = readD();
		secondItemId = readD();
	}

	@Override
	protected void runImpl() {
		final Player player = getConnection().getActivePlayer();
		if (player == null || !player.isSpawned()) {
			return;
		}
		if (player.isProtectionActive()) {
			player.getController().stopProtectionActiveTask();
		}
		if (player.isCasting()) {
			player.getController().cancelCurrentSkill(null);
		}
		ArmsfusionService.fusionWeapons(player, firstItemId, secondItemId);
	}
}
