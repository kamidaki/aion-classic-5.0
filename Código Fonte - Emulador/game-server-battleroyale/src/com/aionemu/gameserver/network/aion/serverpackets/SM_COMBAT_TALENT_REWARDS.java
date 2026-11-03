package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.CombatTalentService;

/** S 0x0148: current Combat Talent followed by 32 claimed-reward flags. */
public class SM_COMBAT_TALENT_REWARDS extends AionServerPacket {

	private final Player player;
	private final int claimedMask;

	public SM_COMBAT_TALENT_REWARDS(Player player, int claimedMask) {
		this.player = player;
		this.claimedMask = claimedMask;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(CombatTalentService.calculateCombatPower(player));
		for (int i = 0; i < 32; i++)
			writeC(claimedMask >>> i & 1);
	}
}
