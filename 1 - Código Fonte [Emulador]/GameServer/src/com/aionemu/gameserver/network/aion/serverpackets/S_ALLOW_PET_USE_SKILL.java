package com.aionemu.gameserver.network.aion.serverpackets;


import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_ALLOW_PET_USE_SKILL extends AionServerPacket {

	private int summonId;
	private int skillId;
	private int skillLvl;
	private int targetId;

	/**
	 * @param summonId
	 * @param skillId
	 * @param skillLvl
	 * @param targetId
	 */
	public S_ALLOW_PET_USE_SKILL(int summonId, int skillId, int skillLvl, int targetId) {
		this.summonId = summonId;
		this.skillId = skillId;
		this.skillLvl = skillLvl;
		this.targetId = targetId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(summonId);
		writeH(skillId);
		writeC(skillLvl);
		writeD(targetId);
	}

}
