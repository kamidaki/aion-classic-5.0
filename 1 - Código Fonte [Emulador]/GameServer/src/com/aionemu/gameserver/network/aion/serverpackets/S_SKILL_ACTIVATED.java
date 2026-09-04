package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_SKILL_ACTIVATED extends AionServerPacket {

	private Player player;
	private int subEffectId;

	public S_SKILL_ACTIVATED(Player player, int subEffectId) {
		this.player = player;
		this.subEffectId = subEffectId;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(0x00);// unk
		writeD(player.getObjectId());
		writeD(subEffectId);
	}
}
