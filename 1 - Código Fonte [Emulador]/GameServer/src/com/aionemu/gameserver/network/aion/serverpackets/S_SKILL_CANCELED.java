package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_SKILL_CANCELED extends AionServerPacket {

	private Creature creature;
	private int skillId;

	public S_SKILL_CANCELED(Creature creature, int skillId) {
		this.creature = creature;
		this.skillId = skillId;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(creature.getObjectId());
		writeH(skillId);
		writeH(0);
	}
}
