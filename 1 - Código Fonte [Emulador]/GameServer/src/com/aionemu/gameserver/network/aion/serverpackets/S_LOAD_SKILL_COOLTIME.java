package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

import java.util.ArrayList;
import java.util.Map;

public class S_LOAD_SKILL_COOLTIME extends AionServerPacket
{
    private Map<Integer, Long> cooldowns;

    public S_LOAD_SKILL_COOLTIME(Map<Integer, Long> cooldowns) {
        this.cooldowns = cooldowns;
    }
    
	@Override
    protected void writeImpl(AionConnection con) {
    	writeH(calculateSize());
        writeC(1);
        long currentTime = System.currentTimeMillis();
        for (Map.Entry<Integer, Long> entry : cooldowns.entrySet()) {
            int left = (int) ((entry.getValue() - currentTime) / 1000);
            ArrayList<Integer> skillsWithCooldown = DataManager.SKILL_DATA.getSkillsForDelayId(entry.getKey());
            for (int index = 0; index < skillsWithCooldown.size(); index++) {
                int skillId = skillsWithCooldown.get(index);
                writeH(skillId);
                writeD(left > 0 ? left : 0);
                writeD(DataManager.SKILL_DATA.getSkillTemplate(skillId).getCooldown());
            }
        }
    }
	
	private int calculateSize() {
        int size = 0;
        for (Map.Entry<Integer, Long> entry : cooldowns.entrySet()) {
            size += DataManager.SKILL_DATA.getSkillsForDelayId(entry.getKey()).size();
        }
        return size;
    }
}