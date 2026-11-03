package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.ArmsfusionService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_BREAK_WEAPONS extends AionClientPacket {

	public CM_BREAK_WEAPONS(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	private int weaponToBreakUniqueId;

	@Override
	protected void readImpl() {
		readD();
		weaponToBreakUniqueId = readD();
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
		ArmsfusionService.breakWeapons(player, weaponToBreakUniqueId);
	}
}
