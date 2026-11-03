package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.CombatTalentRewardService;

/** C 0x010F: claim one Combat Talent milestone, payload [H rewardId]. */
public class CM_COMBAT_TALENT_REWARD extends AionClientPacket {

	private int rewardId;

	public CM_COMBAT_TALENT_REWARD(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		rewardId = readUH();
	}

	@Override
	protected void runImpl() {
		CombatTalentRewardService.claim(getConnection().getActivePlayer(), rewardId);
	}
}
