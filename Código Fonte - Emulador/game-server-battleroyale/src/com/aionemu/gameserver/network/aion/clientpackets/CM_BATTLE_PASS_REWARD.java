package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.player.BattlePassService;

public class CM_BATTLE_PASS_REWARD extends AionClientPacket {

	private int seasonId;
	private int unk;

	public CM_BATTLE_PASS_REWARD(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_BATTLE_PASS_REWARD(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		this.seasonId = readD();
		this.unk = readC();
		readD();
		readD();
	}

	@Override
	protected void runImpl() {
		final Player player = getConnection().getActivePlayer();
		if (player == null || !player.isSpawned()) {
			return;
		}
		BattlePassService.getInstance().onGetReward(player, this.seasonId);
	}
}
