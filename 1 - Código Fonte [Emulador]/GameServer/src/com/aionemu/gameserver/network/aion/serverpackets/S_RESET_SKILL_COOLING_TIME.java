package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_RESET_SKILL_COOLING_TIME extends AionServerPacket
{
    private int skillId;
    private int modifier;
	
	public S_RESET_SKILL_COOLING_TIME(int skillId, int modifier) {
        this.skillId = skillId;
        this.modifier = modifier;
    }
	
	@Override
    protected void writeImpl(AionConnection con) {
        this.writeH(this.skillId);
        this.writeD(this.modifier);
    }
}