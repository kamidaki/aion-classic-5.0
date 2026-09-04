package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_DELETE_SKILL extends AionServerPacket
{
	private int skillId;
	private int skillLevel;
	private boolean isStigma;
	
	public S_DELETE_SKILL(int skillId, int skillLevel, boolean isStigma) {
		this.skillId = skillId;
		this.skillLevel = skillLevel;
		this.isStigma = isStigma;
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		writeH(skillId);
		if (skillId >= 30001 && skillId <= 30003 || skillId >= 40001 && skillId <= 40009) {
			writeC(0);
			writeC(0);
		} else if (isStigma) {
			writeC(skillLevel);
			writeC(1);
		} else {
			writeC(skillLevel);
		}
	}
}