package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_TOGGLE_SKILL_ON_OFF extends AionServerPacket {

	private boolean isActive;
	private int unk;
	private int skillId;

	/**
	 * For toggle skills
	 * 
	 * @param skillId
	 * @param isActive
	 */
	public S_TOGGLE_SKILL_ON_OFF(int skillId, boolean isActive) {
		this.skillId = skillId;
		this.isActive = isActive;
		this.unk = 0;
	}

	/**
	 * For stigma remove should work in 1.5.1.15
	 * 
	 * @param skillId
	 */
	public S_TOGGLE_SKILL_ON_OFF(int skillId) {
		this.skillId = skillId;
		this.isActive = true;
		this.unk = 1;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeH(skillId);
		writeD(unk);
		writeC(isActive ? 1 : 0);
	}
}
