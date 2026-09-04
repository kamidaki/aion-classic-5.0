package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_RESURRECT_BY_OTHER extends AionServerPacket {

	private String name;
	private int skillId;

	public S_RESURRECT_BY_OTHER(Creature creature) {
		this(creature, 0);
	}

	public S_RESURRECT_BY_OTHER(Creature creature, int skillId) {
		this.name = creature.getName();
		this.skillId = skillId;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeS(name);
		writeH(skillId); // unk
		writeD(0);
	}
}
